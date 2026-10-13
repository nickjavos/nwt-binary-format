#!/usr/bin/env python3
"""Reference-data converters: security master, corporate actions, symbol directories, option series, MIC list.

    python3 tools/nwt_convert_reference.py KIND SRC OUT [--dataset NAME] [--retrieved YYYY-MM-DD]
    python3 tools/nwt_convert.py KIND SRC OUT [--dataset NAME] [--retrieved YYYY-MM-DD]

    KIND                    SRC                                  records written
    csv-secmaster           security-master CSV export           SECURITY_DEF per row
    csv-corporate-actions   corporate-actions CSV export         SECURITY_DEF when a listing is new or its facts
                                                                 changed, then CORPORATE_ACTION per row
    nasdaqlisted            Nasdaq-listed symbol directory       LISTING and SYMBOL_MAP per row
    otherlisted             other-exchange symbol directory      LISTING and SYMBOL_MAP per row
    options                 option series directory              OPTION_DEF per row
    mic                     ISO 10383 market identifier list     VENUE_DEF per row

The column mapping, the code tables and the policies are described in docs/REAL-DATA.md.
Every converter fails, with the source line, on an unknown code, an over-long text or a
value it cannot carry; nothing is truncated, trimmed or guessed, and rows keep their order.
The same source bytes always give the same container bytes.
"""

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "examples/python", ROOT / "tools"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
import nwt_example as nwt
import nwt_ids
from nwt_parse import days_from_civil, parse_date_ns, parse_decimal, parse_decimal_rounded, parse_timestamp_ns, strip_id

NULL, NULL_I64, NULL_U32 = nwt.NULL, nwt.NULL_I64, nwt.NULL_U32
CREATED_NS = parse_date_ns("2026-10-13")  # fixed, so a rebuild from the same source gives identical bytes
PRODUCER = "nwt-developer-kit/1.1-draft.1"
ERRORS = (ValueError, KeyError, OverflowError, UnicodeError, OSError)
DATES = "POSIX nanoseconds. A source date becomes midnight UTC of that date."


def need(ok, why):
    if not ok:
        raise ValueError(why)


# ------------------------------------------------------------ shared pieces


class Batch:
    """Encoded records in source order, with output sequences for publisher 1, channel 0."""

    def __init__(self):
        self.raws, self.counts, self.sequencer = [], {}, nwt.Sequencer()

    def add(self, typ, **values):
        record = nwt.make_record(typ, sequence=self.sequencer.next(1, 0), **values)
        self.raws.append(nwt.encode_record(record))  # refuses a text outside its limits
        name = nwt.S[typ]["name"]
        self.counts[name] = self.counts.get(name, 0) + 1


class Ids:
    """Instrument IDs for keys. A repeated key, or two keys that give one ID, fails the conversion."""

    def __init__(self):
        self.by_id, self.keys = {}, set()

    def claim(self, namespace, key):
        need(key not in self.keys, f"repeated key {key!r}")
        self.keys.add(key)
        value = nwt_ids.instrument_id_for(namespace, key)
        name = f"{namespace}:{key}"
        other = self.by_id.setdefault(value, name)
        need(other == name, f"instrument ID collision: {other!r} and {name!r} both give {value}")
        return value


def each(rows, convert_row):
    """Run convert_row(line, row) for every row. A failure is reported with its source line. Returns the row count."""
    count = 0
    for line, row in rows:
        try:
            convert_row(line, row)
        except (ValueError, OverflowError) as error:
            raise ValueError(f"line {line}: {error}") from None
        count += 1
    return count


def finish(out_path, source, dataset, publisher, types, batch, provenance, args):
    """Write the container and return its provenance. Nothing is written unless every row converted."""
    # shortcut: all records are held in memory (the provenance counts must be written before the first frame);
    # convert in two passes instead when a source is larger than a few hundred megabytes.
    digest = hashlib.sha256(source)
    provenance = {**provenance, "converter": PRODUCER, "source_sha256": digest.hexdigest(), "records": batch.counts}
    retrieved = getattr(args, "retrieved", None)
    if retrieved:
        parse_date_ns(retrieved)
        provenance["retrieved"] = retrieved
    manifest = nwt.build_manifest(getattr(args, "dataset", None) or dataset, PRODUCER, [publisher], types)
    text = json.dumps(provenance, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    out = io.BytesIO()
    writer = nwt.Writer(out, manifest, digest.digest()[:16], CREATED_NS, provenance=text)
    for raw in batch.raws:
        writer.write_raw(raw)
    writer.close()
    Path(out_path).write_bytes(out.getvalue())
    return provenance


def csv_rows(source, required, allowed=None):
    """(line, {column: text}) per data row of a CSV file.

    Fails on a missing required column and, when `allowed` is given, on a column outside it:
    a format with no place for unknown columns must not drop one silently.
    """
    reader = csv.reader(io.StringIO(source.decode("utf-8"), newline=""))
    header = next(reader, None)
    need(header, "missing header row")
    need(len(set(header)) == len(header), "repeated column name")
    missing = [c for c in required if c not in header]
    need(not missing, "missing columns: " + ", ".join(missing))
    unknown = [c for c in header if allowed is not None and c not in allowed]
    need(not unknown, "columns with no field: " + ", ".join(unknown))
    for row in reader:
        need(len(row) == len(header), f"line {reader.line_num}: expected {len(header)} fields, found {len(row)}")
        yield reader.line_num, dict(zip(header, row))


def number(row, column, parse, empty):
    """parse(text) for a filled column; `empty` for an empty or absent one. A failure names the column."""
    text = row.get(column, "")
    if text == "":
        return empty
    try:
        return parse(text)
    except ValueError as error:
        raise ValueError(f"column {column}: {error}") from None


def code(row, column, table):
    """The table entry for a source code. A code outside the table fails; it is never guessed."""
    text = row.get(column, "")
    need(text in table, f"column {column}: unknown code {text!r}")
    return table[text]


def ident(prefix):
    return lambda text: strip_id(text, prefix)


def whole(bits):
    """Parser for a count in an unsigned field of `bits` bits, below its null value. "7370.0" is 7370."""

    def parse(text):
        value = parse_decimal(text, 0)
        need(0 <= value < (1 << bits) - 1, f"out of range: {text!r}")
        return value

    return parse


def scaled(row, column, noted, empty):
    """A decimal column times 10^9, rounded half to even. A source text that needed rounding is kept in `noted`."""

    def parse(text):
        value, dropped = parse_decimal_rounded(text)
        if dropped:
            noted["source_decimals"][column] = text
        return value

    return number(row, column, parse, empty)


def date(row, column, noted):
    """A YYYY-MM-DD column as midnight UTC. A date before 1970 has no NWT value: the field is null and the text is kept in `noted`."""

    def parse(text):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text, re.ASCII)
        if m and int(m[1]) < 1970:
            days_from_civil(int(m[1]), int(m[2]), int(m[3]))  # it must still be a real date
            noted["source_dates"][column] = text
            return NULL
        return parse_date_ns(text)

    return number(row, column, parse, NULL)


# ------------------------------------------- security master, corporate actions

TRUTH = {"": 0, "False": 0, "True": 1}
LISTING_SOURCE = {"": 0, "M": 1, "S": 2}  # main, secondary
SECURITY_TEXTS = {  # NWT text -> source column
    "issuer_name": "issuer_name", "description": "security_description", "security_type": "security_type",
    "structure": "structure", "listing_status": "listing_status", "voting": "voting",
    "primary_exchange": "primary_exchange", "exchange": "exchange", "operating_mic": "operating_mic",
    "segment_mic": "segment_mic", "segment_name": "segment_mic_name", "symbol": "symbol",
    "alt_symbol": "nasdaq_symbol", "local_code": "local_code", "isin": "isin", "cusip": "us_code",
    "composite_figi": "bbg_comp_id", "composite_ticker": "bbg_comp_ticker", "figi": "figi",
    "figi_ticker": "figi_ticker", "fisn": "fisn", "lei": "lei", "cfi": "cfi", "cic": "cic", "gics": "gics",
    "incorporation_country": "incorporation_country", "listing_country": "listing_country",
    "register_country": "register_country", "trading_currency": "trading_currency",
    "par_value_currency": "par_value_currency",
}  # fmt: skip
SECURITY_COLUMNS = set(SECURITY_TEXTS.values()) | {
    "listing_id", "listing_group_id", "security_id", "issuer_id", "listing_source", "listing_created_date",
    "listing_date", "delisting_date", "sic", "cik", "naics", "multi_currency", "lot_size", "par_value",
    "vote_per_sec", "shares_outstanding", "shares_outstanding_date",
}  # fmt: skip
# Listing columns that a corporate-actions row does not have; its SECURITY_DEF leaves them empty, zero or null.
SECMASTER_ONLY = {
    "listing_created_date", "fisn", "lei", "sic", "cik", "gics", "naics", "cic", "cfi", "incorporation_country",
    "structure", "voting", "vote_per_sec", "shares_outstanding", "shares_outstanding_date",
}  # fmt: skip
ACTION_TEXTS = {  # NWT text -> source column
    "event": "event", "subtype": "event_subtype", "action": "event_action", "status": "global_status",
    "participation": "mand_volu_flag", "payment_type": "payment_type", "fraction": "fraction",
    "date_label": "event_date_label", "related_event": "related_event", "related_event_id": "related_event_id",
    "event_id": "event_id", "unique_id": "event_unique_id", "rate_currency": "rate_currency",
    "outturn_isin": "outturn_isin",
}  # fmt: skip
ACTION_COLUMNS = set(ACTION_TEXTS.values()) | {
    "event_date", "ts_record", "listing_id", "security_id", "issuer_id", "event_created_date", "effective_date",
    "ex_date", "record_date", "payment_date", "record_date_id", "outturn_security_id", "ratio_old", "ratio_new",
    "option_id", "serial_id", "default_option_flag",
}  # fmt: skip
DICT_COLUMNS = ("date_info", "rate_info", "event_info")  # Python-style dictionary literals
REFERENCE_PUBLISHER = {"id": 1, "name": "reference-data", "venue": ""}
REFERENCE_POLICY = (
    "Source identifiers keep their number (L- listing becomes the instrument ID; LG-, S-, I- and D- fill their "
    "fields). Status, action and type codes are carried as the source text. Decimals with more than nine places "
    "are rounded half to even and counted in rounded_decimals. A date before 1970 cannot be stored: its field is "
    "null and it is counted in dates_before_1970. Output sequences start at 1. "
)
LICENCE = "Licensed vendor export. Check the licence before redistributing."


def notes():
    """Per row: {column: source text} of the values that could not be stored exactly, by reason."""
    return {"source_decimals": {}, "source_dates": {}}


def inexact_counts(provenance, counts):
    return {**provenance, "rounded_decimals": counts["source_decimals"], "dates_before_1970": counts["source_dates"]}


def security_def(row, ts_event, noted):
    """make_record values for a SECURITY_DEF, from a security-master row or the listing columns of a corporate-actions row."""
    instrument = number(row, "listing_id", ident("L-"), 0)
    need(instrument, "column listing_id: empty or zero")
    return dict(
        instrument_id=instrument,
        ts_event=ts_event,
        ts_recv=number(row, "ts_record", parse_timestamp_ns, NULL),
        listing_group_id=number(row, "listing_group_id", ident("LG-"), 0),
        security_id=number(row, "security_id", ident("S-"), 0),
        issuer_id=number(row, "issuer_id", ident("I-"), 0),
        listing_created_ns=date(row, "listing_created_date", noted),
        listing_ns=date(row, "listing_date", noted),
        delisting_ns=date(row, "delisting_date", noted),
        shares_outstanding=number(row, "shares_outstanding", whole(64), NULL),
        shares_outstanding_ns=date(row, "shares_outstanding_date", noted),
        lot_size=scaled(row, "lot_size", noted, NULL),
        par_value=scaled(row, "par_value", noted, NULL_I64),
        votes_per_share=scaled(row, "vote_per_sec", noted, NULL_I64),
        cik=number(row, "cik", whole(64), 0),
        sic=number(row, "sic", whole(32), 0),
        naics=number(row, "naics", whole(32), 0),
        listing_source=code(row, "listing_source", LISTING_SOURCE),
        security_flags=code(row, "multi_currency", TRUTH),
        texts={name: row.get(column, "") for name, column in SECURITY_TEXTS.items()},
    )


def literal_json(node, text):
    """A parsed literal as JSON data. A number becomes a string of its source digits, so no float value is used."""
    if isinstance(node, ast.Dict):
        out = {}
        for key, value in zip(node.keys, node.values):
            need(isinstance(key, ast.Constant) and isinstance(key.value, str), "keys must be strings")
            need(key.value not in out, f"repeated key {key.value!r}")
            out[key.value] = literal_json(value, text)
        return out
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal_json(item, text) for item in node.elts]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        number_ = node.operand
        need(isinstance(number_, ast.Constant) and type(number_.value) in (int, float), "sign on a value that is not a number")
        return ast.get_source_segment(text, node)
    if isinstance(node, ast.Constant):
        if node.value is None or isinstance(node.value, (bool, str)):
            return node.value
        if isinstance(node.value, (int, float)):
            return ast.get_source_segment(text, node)
    raise ValueError("only dictionaries, lists, strings, numbers, True, False and None are allowed")


def literal_dict(column, text):
    """A Python-style dictionary literal ({'a': None, 'b': 0.07}) as JSON data. The text is parsed, never run."""
    try:
        need(isinstance(ast.literal_eval(text), dict), "not a dictionary")
        return literal_json(ast.parse(text, mode="eval").body, text)
    except (ValueError, SyntaxError, RecursionError, MemoryError) as error:
        raise ValueError(f"column {column}: not a literal dictionary ({error}): {text[:60]!r}") from None


def corporate_action(row, ts_event, noted):
    """make_record values for a CORPORATE_ACTION. `noted` already holds what the row's listing columns needed."""
    values = dict(
        instrument_id=number(row, "listing_id", ident("L-"), 0),
        ts_event=ts_event,
        ts_recv=number(row, "ts_record", parse_timestamp_ns, NULL),
        security_id=number(row, "security_id", ident("S-"), 0),
        issuer_id=number(row, "issuer_id", ident("I-"), 0),
        created_ns=date(row, "event_created_date", noted),
        effective_ns=date(row, "effective_date", noted),
        ex_ns=date(row, "ex_date", noted),
        record_ns=date(row, "record_date", noted),
        payment_ns=date(row, "payment_date", noted),
        record_date_id=number(row, "record_date_id", ident("D-"), 0),
        outturn_security_id=number(row, "outturn_security_id", ident("S-"), 0),
        ratio_old=scaled(row, "ratio_old", noted, NULL_I64),
        ratio_new=scaled(row, "ratio_new", noted, NULL_I64),
        option_id=number(row, "option_id", whole(32), NULL_U32),
        serial_id=number(row, "serial_id", whole(32), NULL_U32),
        action_flags=code(row, "default_option_flag", TRUTH),
    )
    # Every filled column without a field or text of its own goes into details, so no source value is dropped.
    details = {}
    for column, text in row.items():
        if text != "" and column not in SECURITY_COLUMNS and column not in ACTION_COLUMNS:
            details[column] = literal_dict(column, text) if column in DICT_COLUMNS else text
    for key, originals in noted.items():
        if originals:
            need(key not in details, f"source column {key} clashes with a details key")
            details[key] = originals
    texts = {name: row[column] for name, column in ACTION_TEXTS.items()}
    texts["details"] = json.dumps(details, sort_keys=True, separators=(",", ":"), ensure_ascii=False) if details else ""
    return {**values, "texts": texts}


def convert_secmaster(src_path, out_path, args):
    source = Path(src_path).read_bytes()
    batch, kept, counts = Batch(), [], {"source_decimals": 0, "source_dates": 0}
    known = SECURITY_COLUMNS | {"ts_effective", "ts_record", "ts_created"}

    def one(line, row):
        noted = notes()
        batch.add(21, **security_def(row, number(row, "ts_effective", parse_timestamp_ns, NULL), noted))
        # SECURITY_DEF has no free text, so a value that could not be stored exactly is listed in the provenance.
        for reason, originals in noted.items():
            counts[reason] += len(originals)
            kept.extend({"line": line, "column": column, "source": text} for column, text in originals.items())

    provenance = {
        "source_format": "vendor CSV export",
        "source_kind": "csv-secmaster",
        "source_rows": each(csv_rows(source, sorted(known), known), one),
        "conversion_policy": REFERENCE_POLICY
        + "ts_event is the effective timestamp and ts_recv the record timestamp. One SECURITY_DEF per row. "
        "A value that could not be stored exactly is listed in not_exact.",
        "clock_policy": DATES,
        "license_reference": LICENCE,
        "columns_not_carried": ["ts_created"],
        "not_exact": kept,
    }
    provenance = inexact_counts(provenance, counts)
    return finish(out_path, source, "REAL.SECMASTER", REFERENCE_PUBLISHER, [21], batch, provenance, args)


def convert_corporate_actions(src_path, out_path, args):
    source = Path(src_path).read_bytes()
    batch, facts, counts = Batch(), {}, {"source_decimals": 0, "source_dates": 0}
    listing_columns = sorted(SECURITY_COLUMNS)

    def one(_, row):
        noted = notes()
        ts_event = date(row, "event_date", noted)
        security = security_def(row, ts_event, noted)
        action = corporate_action(row, ts_event, noted)
        key = tuple(row.get(column, "") for column in listing_columns)
        if facts.get(security["instrument_id"]) != key:  # a new listing, or its facts changed
            facts[security["instrument_id"]] = key
            batch.add(21, **security)
        batch.add(22, **action)
        for reason, originals in noted.items():
            counts[reason] += len(originals)

    provenance = {
        "source_format": "vendor CSV export",
        "source_kind": "csv-corporate-actions",
        "source_rows": each(csv_rows(source, sorted(ACTION_COLUMNS | SECURITY_COLUMNS - SECMASTER_ONLY)), one),
        "conversion_policy": REFERENCE_POLICY
        + "ts_event is the event date and ts_recv the record timestamp. A row carries a copy of the listing facts: "
        "a SECURITY_DEF is written before the row's CORPORATE_ACTION when the listing is new or those facts differ "
        "from the previous row of that listing, and its ts_event is that row's event date. Every filled column "
        "without a field or text of its own is in details under its source column name, as the source text; the "
        "three dictionary columns are parsed as literals and their numbers kept as strings of the source digits. "
        "Texts that needed rounding are in details.source_decimals and dates before 1970 in details.source_dates.",
        "clock_policy": DATES,
        "license_reference": LICENCE,
    }
    provenance = inexact_counts(provenance, counts)
    return finish(out_path, source, "REAL.CORPACT", REFERENCE_PUBLISHER, [21, 22], batch, provenance, args)


# --------------------------------------------------------------- public files

# Code tables. The letters and their meanings are the publisher's (docs/REAL-DATA.md names the page);
# a letter that is not listed there is not listed here, and fails the conversion.
YES = {"Y": 1, "N": 0}
MARKET_TIER = {"Q": 1, "G": 2, "S": 3}  # Global Select, Global, Capital
# financial_flags: bit 0 reported, bit 1 deficient, bit 2 delinquent, bit 3 bankrupt
FINANCIAL = {"N": 1, "D": 3, "E": 5, "Q": 9, "G": 11, "H": 7, "J": 13, "K": 15}
EXCHANGE_MIC = {"A": "XASE", "N": "XNYS", "P": "ARCX", "Z": "BATS", "V": "IEXG"}
CLOSING_TYPE = {"N": 1, "L": 2}  # normal hours, late hours
OPTION_RIGHT = {"C": 1, "P": 2}
VENUE_KIND = {"OPRT": 1, "SGMT": 2}
VENUE_STATUS = {"ACTIVE": 1, "UPDATED": 2, "EXPIRED": 3}

NASDAQ_HEADER = ["Symbol", "Security Name", "Market Category", "Test Issue", "Financial Status", "Round Lot Size",
                 "ETF", "NextShares"]  # fmt: skip
OTHER_HEADER = ["ACT Symbol", "Security Name", "Exchange", "CQS Symbol", "ETF", "Round Lot Size", "Test Issue",
                "NASDAQ Symbol"]  # fmt: skip
OPTIONS_HEADER = ["Root Symbol", "Options Closing Type", "Options Type", "Expiration Date", "Explicit Strike Price",
                  "Underlying Symbol", "Underlying Issue Name", "Pending"]  # fmt: skip
VENUE_TEXTS = {  # NWT text -> source column
    "mic": "MIC", "operating_mic": "OPERATING MIC", "country": "ISO COUNTRY CODE (ISO 3166)",
    "category": "MARKET CATEGORY CODE", "acronym": "ACRONYM", "city": "CITY",
    "name": "MARKET NAME-INSTITUTION DESCRIPTION", "legal_entity": "LEGAL ENTITY NAME", "lei": "LEI",
}  # fmt: skip
MIC_NOT_CARRIED = ["WEBSITE", "LAST VALIDATION DATE", "COMMENTS"]
MIC_COLUMNS = set(VENUE_TEXTS.values()) | set(MIC_NOT_CARRIED) | {
    "OPRT/SGMT", "STATUS", "CREATION DATE", "LAST UPDATE DATE", "EXPIRY DATE"
}
SYMDIR = "https://www.nasdaqtrader.com/dynamic/SymDir/"
TRAILER = "File Creation Time: "
DIRECTORY_POLICY = (
    "Code letters are mapped by the tables in docs/REAL-DATA.md; a letter outside them fails the conversion. "
    "Instrument IDs are the first 63 bits of SHA-256(namespace, NUL, key), checked for collisions. "
    "Text is carried unchanged. Output sequences start at 1. "
)
DIRECTORY_CLOCK = DATES + " The file creation time is read as US Eastern time; ts_recv is null."


def creation_ns(text):
    """The file creation time "mmddyyyyhh:mm", publisher's local time (US Eastern), as POSIX nanoseconds."""
    m = re.fullmatch(r"(\d{2})(\d{2})(\d{4})(\d{2}):(\d{2})", text, re.ASCII)
    need(m, f"bad file creation time: {text!r}")
    month, day, year, hour, minute = (int(part) for part in m.groups())
    offset = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("America/New_York")).utcoffset()
    seconds = hour * 3600 + minute * 60 - (offset.days * 86400 + offset.seconds)
    return parse_date_ns(f"{m[3]}-{m[1]}-{m[2]}") + seconds * 10**9


def directory(source, header):
    """([(line, {column: text})], creation time) of a pipe-separated symbol directory file.

    The creation time is None when the last row does not carry it, as in a file cut short.
    """
    lines = source.decode("utf-8").split("\n")
    if lines[-1] == "":
        lines.pop()
    lines = [line.removesuffix("\r") for line in lines]
    need(lines and lines[0].split("|") == header, "unexpected header row")
    created = None
    if len(lines) > 1 and lines[-1].startswith(TRAILER):
        created = creation_ns(lines.pop().split("|")[0][len(TRAILER) :])
    rows = []
    for line, text in enumerate(lines[1:], 2):
        parts = text.split("|")
        need(len(parts) == len(header), f"line {line}: expected {len(header)} fields, found {len(parts)}")
        rows.append((line, dict(zip(header, parts))))
    return rows, created


def nasdaq_listing(row):
    """(ID namespace, symbol, LISTING values) for a Nasdaq-listed row."""
    flags = code(row, "ETF", YES) | code(row, "Test Issue", YES) << 1 | code(row, "NextShares", YES) << 2
    texts = dict(symbol=row["Symbol"], name=row["Security Name"], listing_mic="XNAS", cqs_symbol="", alt_symbol="")
    return "XNAS", row["Symbol"], dict(
        round_lot=number(row, "Round Lot Size", whole(32), NULL_U32),
        listing_flags=flags,
        market_tier=code(row, "Market Category", MARKET_TIER),
        financial_flags=code(row, "Financial Status", FINANCIAL),
        texts=texts,
    )


def other_listing(row):
    """(ID namespace, symbol, LISTING values) for an other-exchange row. The file has no tier or financial status."""
    mic = code(row, "Exchange", EXCHANGE_MIC)
    texts = dict(symbol=row["ACT Symbol"], name=row["Security Name"], listing_mic=mic,
                 cqs_symbol=row["CQS Symbol"], alt_symbol=row["NASDAQ Symbol"])  # fmt: skip
    return mic, row["ACT Symbol"], dict(
        round_lot=number(row, "Round Lot Size", whole(32), NULL_U32),
        listing_flags=code(row, "ETF", YES) | code(row, "Test Issue", YES) << 1,
        market_tier=0,
        financial_flags=0,
        texts=texts,
    )


def listings(kind, header, listing, venue, dataset):
    """The converter for one of the two listed-securities files."""

    def convert(src_path, out_path, args):
        source = Path(src_path).read_bytes()
        rows, created = directory(source, header)
        need(created is not None or not rows, "no File Creation Time row: SYMBOL_MAP valid_from_ns needs it")
        batch, ids = Batch(), Ids()

        def one(_, row):
            namespace, symbol, values = listing(row)
            instrument = ids.claim(namespace, symbol)
            batch.add(12, instrument_id=instrument, ts_event=created, **values)
            batch.add(17, instrument_id=instrument, ts_event=created, valid_from_ns=created, valid_to_ns=NULL,
                      symbology=1, texts={"symbol": symbol})  # fmt: skip

        provenance = {
            "source_format": "public symbol directory file (pipe-separated text)",
            "source_kind": kind,
            "source_url": SYMDIR + kind + ".txt",
            "source_rows": each(rows, one),
            "conversion_policy": DIRECTORY_POLICY
            + "Each row gives a LISTING and a SYMBOL_MAP (native symbology, open-ended, valid from the file "
            "creation time, which is also ts_event). The ID namespace is the listing MIC and the key is the symbol.",
            "clock_policy": DIRECTORY_CLOCK,
            "license_reference": "Public file of the publisher named in source_url; its terms of use apply.",
        }
        publisher = {"id": 1, "name": "symbol-directory", "venue": venue}
        return finish(out_path, source, dataset, publisher, [12, 17], batch, provenance, args)

    return convert


def convert_options(src_path, out_path, args):
    source = Path(src_path).read_bytes()
    rows, created = directory(source, OPTIONS_HEADER)
    batch, ids = Batch(), Ids()

    def one(_, row):
        m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", row["Expiration Date"], re.ASCII)
        need(m, f"column Expiration Date: not mm/dd/yyyy: {row['Expiration Date']!r}")
        day = f"{m[3]}-{m[1]}-{m[2]}"
        strike = number(row, "Explicit Strike Price", parse_decimal, None)
        need(strike is not None, "column Explicit Strike Price: empty")
        right = code(row, "Options Type", OPTION_RIGHT)
        key = f"{row['Root Symbol']}|{day}|{row['Options Type']}|{nwt.pretty_decimal(strike)}"
        batch.add(
            11,
            instrument_id=ids.claim("XNDQ", key),
            ts_event=NULL if created is None else created,
            underlying_instrument_id=0,  # the file gives the underlying as a symbol only
            expiration_ns=parse_date_ns(day),
            strike=strike,
            contract_multiplier=NULL_I64,
            right=right,
            exercise_style=0,
            settlement=0,
            closing_type=code(row, "Options Closing Type", CLOSING_TYPE),
            option_flags=code(row, "Pending", YES),
            texts=dict(root=row["Root Symbol"], underlying_symbol=row["Underlying Symbol"], osi_symbol="", currency=""),
        )

    provenance = {
        "source_format": "public symbol directory file (pipe-separated text)",
        "source_kind": "options",
        "source_url": SYMDIR + "options.txt",
        "source_rows": each(rows, one),
        "conversion_policy": DIRECTORY_POLICY
        + "Each row gives an OPTION_DEF. The file has no exercise style, settlement, multiplier, currency, "
        "adjusted flag or OSI symbol: they stay unknown, null or empty. The underlying is a symbol only, so "
        "underlying_instrument_id is 0. Expiration is midnight UTC of the source date. The ID namespace is XNDQ "
        "and the key is root|YYYY-MM-DD|C or P|strike with nine decimals. ts_event is the file creation time, or "
        "null when the source has no creation-time row.",
        "clock_policy": DIRECTORY_CLOCK,
        "license_reference": "Public file of the publisher named in source_url; its terms of use apply.",
        "columns_not_carried": ["Underlying Issue Name"],
    }
    publisher = {"id": 1, "name": "symbol-directory", "venue": "XNDQ"}
    return finish(out_path, source, "REAL.SYMDIR.OPTIONS", publisher, [11], batch, provenance, args)


def compact_date(text):
    need(len(text) == 8 and text.isascii() and text.isdigit(), f"not a date (YYYYMMDD): {text!r}")
    return parse_date_ns(f"{text[:4]}-{text[4:6]}-{text[6:]}")


def convert_mic(src_path, out_path, args):
    source = Path(src_path).read_bytes()
    batch = Batch()

    def one(_, row):
        kind = code(row, "OPRT/SGMT", VENUE_KIND)
        need(kind == 2 or row["MIC"] == row["OPERATING MIC"], "an operating MIC must be its own OPERATING MIC")
        batch.add(
            10,
            created_ns=number(row, "CREATION DATE", compact_date, NULL),
            updated_ns=number(row, "LAST UPDATE DATE", compact_date, NULL),
            expiry_ns=number(row, "EXPIRY DATE", compact_date, NULL),
            kind=kind,
            status=code(row, "STATUS", VENUE_STATUS),
            texts={name: row[column] for name, column in VENUE_TEXTS.items()},
        )

    provenance = {
        "source_format": "ISO 10383 market identifier code list (CSV)",
        "source_kind": "mic",
        "source_url": "https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv",
        "source_rows": each(csv_rows(source, sorted(MIC_COLUMNS), MIC_COLUMNS), one),
        "conversion_policy": "Each row gives a VENUE_DEF. OPRT is kind 1 and SGMT kind 2; ACTIVE, UPDATED and "
        "EXPIRED are status 1, 2 and 3; any other word fails the conversion. Text is carried unchanged. The header "
        "instrument is 0 and ts_event and ts_recv are null: the source dates are in created_ns, updated_ns and "
        "expiry_ns. Output sequences start at 1.",
        "clock_policy": DATES,
        "license_reference": "Public file of the publisher named in source_url; its terms of use apply.",
        "columns_not_carried": MIC_NOT_CARRIED,
    }
    publisher = {"id": 1, "name": "iso-10383", "venue": ""}
    return finish(out_path, source, "REAL.ISO10383.MIC", publisher, [10], batch, provenance, args)


# ------------------------------------------------------------------ commands


def add_kinds(registry):
    registry["csv-secmaster"] = convert_secmaster
    registry["csv-corporate-actions"] = convert_corporate_actions
    registry["nasdaqlisted"] = listings("nasdaqlisted", NASDAQ_HEADER, nasdaq_listing, "XNAS", "REAL.SYMDIR.NASDAQLISTED")
    registry["otherlisted"] = listings("otherlisted", OTHER_HEADER, other_listing, "", "REAL.SYMDIR.OTHERLISTED")
    registry["options"] = convert_options
    registry["mic"] = convert_mic


def main(argv=None):
    registry = {}
    add_kinds(registry)
    parser = argparse.ArgumentParser(prog="nwt_convert_reference.py", description="Convert reference data to NWT.")
    parser.add_argument("kind", choices=sorted(registry))
    parser.add_argument("src", help="source file")
    parser.add_argument("out", help="NWT container to write")
    parser.add_argument("--dataset", help="manifest dataset name (each kind has a default)")
    parser.add_argument("--retrieved", help="YYYY-MM-DD the source was retrieved, recorded in the provenance")
    args = parser.parse_args(argv)
    try:
        summary = registry[args.kind](args.src, args.out, args)
    except ERRORS as error:
        print(f"NWT error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
