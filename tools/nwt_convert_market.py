#!/usr/bin/env python3
"""Converters from a vendor's CSV exports of market data to NWT containers.

    python3 tools/nwt_convert_market.py KIND SRC OUT --dataset NAME [--option value | --flag] ...

Kinds: csv-definition, csv-mbo, csv-mbp1, csv-mbp10, csv-cmbp1, csv-ohlcv, csv-statistics.
The same kinds are registered with tools/nwt_convert.py through add_kinds().

Rules that hold for every kind (docs/REAL-DATA-MARKET.md has the column mapping):
- Prices, sizes and timestamps are parsed exactly (tools/nwt_parse.py). No floating point, no rounding.
- Source publisher and instrument IDs are kept. NWT sequences restart at 1 per (publisher, channel);
  the source sequence number is not carried.
- Records keep the order of the source rows. Rows that cannot be represented are skipped and counted
  in the provenance; an unknown code or an over-long text stops the conversion with the line number.
- The output is deterministic: a fixed created_ns and a stream ID taken from the SHA-256 of the rows read.
- Nothing is written when the conversion fails.
"""

import csv
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "examples/python", ROOT / "tools"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
import nwt_example as nwt
from nwt_parse import parse_date_ns, parse_decimal, parse_timestamp_ns

PRODUCER = "nwt-developer-kit/1.1-draft.1"
CREATED_NS = parse_date_ns("2026-10-13")  # fixed, so the same source rows always give the same bytes
NULL, NULL_I64, NULL_U32 = nwt.NULL, nwt.NULL_I64, nwt.NULL_U32
MINUTE = 60 * 10**9
SOURCE_NULL_QUANTITY = "9223372036854775807"  # how the statistics export writes "no quantity"
ERRORS = (ValueError, KeyError, OverflowError, UnicodeError, OSError)

# Source instrument class -> NWT asset class. Only stock, future, call and put are evident; the rest are unspecified.
ASSET_CLASS = {"K": 1, "F": 2, "C": 3, "P": 3, "B": 0, "I": 0, "M": 0, "S": 0, "T": 0, "X": 0, "Y": 0}
OPTION_RIGHT = {"C": 1, "P": 2}
EXERCISE_STYLE = {"A": 1, "E": 2}  # ISO 10962, third letter of an option CFI code
SIDE = {"B": 1, "A": 2}  # book side of an order; aggressor of a trade (buyer 1, seller 2)
OSI = re.compile(r"[A-Z0-9]{1,6} {0,5}\d{6}[CP]\d{8}")  # root padded to 6, YYMMDD, right, strike x 1000
# Bits seen in the flags column of order-level files (values 0, 2, 8, 40, 128, 130, 168). None changes how a
# row is applied to the book, so they are not carried. Any other bit stops the conversion.
MBO_FLAG_BITS = 2 | 8 | 32 | 128
FILL_RULES = ("cancel-carries-fill", "fill-reduces")
# Source stat_type -> (NWT stat_type, which column holds the value). Confirmed against the export's reference page.
STAT_TYPES = {
    "1": (1, "price"),  # opening price -> open
    "5": (2, "price"),  # trading session high price -> high
    "4": (3, "price"),  # trading session low price -> low
    "11": (4, "price"),  # close price -> close
    "3": (5, "price"),  # settlement price -> settlement
    "6": (7, "quantity"),  # cleared volume -> volume
    "9": (8, "quantity"),  # open interest -> open interest
}
SOURCE_SETTLEMENT = "3"

DEFINITION_COLUMNS = (
    "ts_recv", "ts_event", "publisher_id", "instrument_id", "raw_symbol", "security_update_action",
    "instrument_class", "min_price_increment", "expiration", "underlying_id", "channel_id", "currency",
    "exchange", "asset", "cfi", "underlying", "strike_price",
)  # fmt: skip
EVENT_COLUMNS = ("ts_recv", "ts_event", "publisher_id", "instrument_id", "action", "side", "price", "size", "symbol")
TOP_COLUMNS = ("bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00")


def need(ok, why):
    if not ok:
        raise ValueError(why)


class Located(ValueError):
    """An error whose message already names the source file and line."""


class NoCurrency(ValueError):
    """A definition row has no currency and no --currency was given."""


@contextmanager
def located(source, line=None):
    """Put the source file name and line number in front of any conversion error raised inside."""
    try:
        yield
    except Located:
        raise
    except ValueError as error:
        text = f"{source.name} line {line or source.reader.line_num}: {error}"
        raise (NoCurrency if isinstance(error, NoCurrency) else Located)(text) from None


def option(args, name):
    return getattr(args, name, None)


def required(args, name, why):
    value = option(args, name)
    need(isinstance(value, str) and value, f"missing --{name.replace('_', '-')}: {why}")
    return value


# ------------------------------------------------------------------ source


class Source:
    """One CSV file read as a stream: rows as dictionaries, the current line number, a SHA-256 of the lines read."""

    def __init__(self, path, columns, max_rows=None):
        self.name = os.path.basename(path)
        self.max_rows, self.rows, self.hash = max_rows, 0, hashlib.sha256()
        self.file = open(path, "rb")
        self.reader = csv.reader(self.lines())
        self.header = next(self.reader, None)
        need(self.header, f"{self.name}: empty file, no header row")
        need(len(set(self.header)) == len(self.header), f"{self.name}: repeated column name")
        missing = [name for name in columns if name not in self.header]
        need(not missing, f"{self.name}: missing column(s) {', '.join(missing)}")

    def lines(self):
        for line in self.file:
            self.hash.update(line)
            yield line.decode("utf-8")

    def lists(self):
        """Rows as lists, in header order. Stops after max_rows rows without reading any further line."""
        try:
            while self.max_rows is None or self.rows < self.max_rows:
                row = next(self.reader, None)
                if row is None:
                    break
                if not row:  # a blank line
                    continue
                need(len(row) == len(self.header), f"{self.name} line {self.reader.line_num}: wrong number of columns")
                self.rows += 1
                yield row
        finally:
            self.file.close()

    def __iter__(self):
        for row in self.lists():
            yield dict(zip(self.header, row))

    def sha256(self):
        return self.hash.hexdigest()


def price(text):
    """Decimal text to a price x 10^9; empty text is the null price."""
    if text == "":
        return NULL_I64
    value = parse_decimal(text)
    need(value != NULL_I64, f"price out of range: {text!r}")
    return value


def quantity(text):
    value = parse_decimal(text)
    need(value >= 0, f"negative quantity: {text!r}")
    return value


def timestamp(text):
    return NULL if text == "" else parse_timestamp_ns(text)


def number(text, limit=NULL):
    need(text.isascii() and text.isdigit() and int(text) < limit, f"not an unsigned integer in range: {text!r}")
    return int(text)


def head_of(row):
    """The NWT record header fields that come straight from a source row. The channel is 0 when the file has none."""
    head = dict(
        publisher_id=number(row["publisher_id"], NULL_U32 + 1),
        channel_id=number(row.get("channel_id", "0"), NULL_U32 + 1),
        instrument_id=number(row["instrument_id"]),
        ts_event=timestamp(row["ts_event"]),
        ts_recv=timestamp(row.get("ts_recv", "")),
    )
    need(head["publisher_id"] and head["instrument_id"], "publisher_id and instrument_id must not be 0")
    return head


# ------------------------------------------------------------------ output


class Output:
    """One output container. Encoded records are spooled to a temporary file, because the manifest and the
    provenance (publishers seen, counts, source hash) are complete only after the last source row."""

    def __init__(self, types):
        self.spool = tempfile.TemporaryFile()
        self.types, self.publishers = set(types), set()
        self.sequencer, self.records = nwt.Sequencer(), Counter()

    def add(self, typ, head, texts=None, levels=None, **body):
        sequence = self.sequencer.next(head["publisher_id"], head["channel_id"])
        record = nwt.make_record(typ, sequence=sequence, texts=texts, levels=levels, **head, **body)
        self.spool.write(nwt.encode_record(record))
        self.types.add(typ)
        self.publishers.add(head["publisher_id"])
        self.records[nwt.S[typ]["name"]] += 1

    def finish(self, path, dataset, stream_id, provenance):
        publishers = [{"id": p, "name": f"publisher-{p}", "venue": ""} for p in sorted(self.publishers)]
        manifest = nwt.build_manifest(dataset, PRODUCER, publishers, self.types)
        text = json.dumps(provenance, separators=(",", ":"), ensure_ascii=False)
        try:
            with open(path, "wb") as out:
                writer = nwt.Writer(out, manifest, stream_id, CREATED_NS, provenance=text)
                self.spool.seek(0)
                while head := self.spool.read(4):
                    writer.write_raw(head + self.spool.read(int.from_bytes(head, "little") - 4))
                writer.close()
        except BaseException:
            Path(path).unlink(missing_ok=True)  # never leave a partial container behind
            raise
        finally:
            self.spool.close()


class Job:
    """What every kind shares: the options, the source, the counts, the definitions and the final write."""

    def __init__(self, kind, schema, src_path, args, columns, types):
        self.kind, self.schema, self.args = kind, schema, args
        self.dataset = required(args, "dataset", "the dataset name for the manifest, for example REAL.XNAS.ITCH")
        limit = option(args, "max_rows")
        self.max_rows = None if limit is None else number(str(limit))
        self.src_path = src_path
        self.source = Source(src_path, columns, self.max_rows)
        self.skipped, self.notes = Counter(), Counter()
        self.policy = [
            "Prices, sizes and timestamps are exact; nothing is rounded.",
            "Source publisher and instrument IDs are kept; the channel is the source channel_id, or 0 when the file has none.",
            "NWT sequences restart at 1 per (publisher, channel); the source sequence number is not carried.",
            "Source flags are not carried.",
        ]
        self.extra = {}
        self.out = Output(types)
        self.definitions = None

    def use_definitions(self):
        """Call before the first row of a market-data kind: definitions are written ahead of each instrument's records."""
        self.definitions = Definitions(self)

    def define(self, out, head, row):
        """False when the instrument cannot be defined and --skip-undefined says to leave its rows out."""
        return self.definitions.before(out, head, row)

    def provenance(self, out, role):
        value = {
            "source_format": "vendor CSV export",
            "source_schema": self.schema,
            "source_sha256": self.source.sha256(),
            "source_rows": self.source.rows,
            "converter": f"tools/nwt_convert_market.py {self.kind}",
            "output": role,
            "conversion_policy": " ".join(self.policy),
            "records_written": dict(sorted(out.records.items())),
            "rows_skipped": dict(sorted(self.skipped.items())),
            "values_rounded": 0,
            "notes": dict(sorted(self.notes.items())),
            "license_reference": "Licensed vendor data. Check the licence before redistributing.",
        }
        value["policy_options"] = policy_options(self.args)
        if self.definitions and self.definitions.source:
            value["definitions_sha256"] = self.definitions.source.sha256()
        value.update(self.extra)
        return value

    def write(self, out, path, role):
        """Write one container and return its provenance, which is also the summary for the caller."""
        value = self.provenance(out, role)
        digest = hashlib.sha256(f"{self.kind}\0{role}\0{value['source_sha256']}".encode()).digest()
        out.finish(path, self.dataset, digest[:16], value)
        return value

    def finish(self, path):
        return self.write(self.out, path, "main")


# ------------------------------------------------------------- definitions


def definition_records(row, job, publisher_id=None, channel_id=None):
    """(type, head, body, texts) for one definition row: INSTRUMENT_DEF, then OPTION_DEF for a call or a put.

    Returns [] for a row that deletes a definition, which NWT cannot express."""
    args = job.args
    update = row["security_update_action"]
    need(update in ("A", "M", "D"), f"unknown security_update_action {update!r}")
    if update == "D":
        job.skipped["definition rows that delete an instrument"] += 1
        return []
    cls = row["instrument_class"]
    need(cls in ASSET_CLASS, f"unknown instrument class {cls!r}")
    head = head_of(row)
    if publisher_id is not None:  # written ahead of a market record: that record's publisher and channel
        head.update(publisher_id=publisher_id, channel_id=channel_id)
    currency = row["currency"] or option(args, "currency")
    if not (isinstance(currency, str) and currency):
        raise NoCurrency("the row has no currency: pass --currency, or --skip-undefined to leave the instrument out")
    unit = required(args, "quantity_unit", "the source has no unit for order sizes (for example share or contract)")
    increment, strike = price(row["min_price_increment"]), price(row["strike_price"])
    need(increment == NULL_I64 or increment > 0, "min_price_increment is not positive")
    expiration, underlying = timestamp(row["expiration"]), number(row["underlying_id"])
    need(row["raw_symbol"], "empty raw_symbol")
    body = dict(
        price_increment=increment,
        quantity_increment=NULL,  # the source has lot sizes, not a size increment
        contract_multiplier=NULL_I64,  # the source has a contract size in a unit of measure, not a price multiplier
        expiration_ns=expiration,
        underlying_instrument_id=underlying,
        strike=strike,
        asset_class=ASSET_CLASS[cls],
    )
    texts = dict(
        symbol=row["raw_symbol"], venue=row["exchange"] or option(args, "venue") or "", currency=currency,
        quantity_unit=unit,
    )  # fmt: skip
    records = [(6, head, body, texts)]
    if cls not in OPTION_RIGHT:
        return records
    if underlying == 0 and not row["underlying"]:  # OPTION_DEF needs an underlying ID or symbol
        job.notes["option rows with no underlying ID or symbol: INSTRUMENT_DEF only, no OPTION_DEF"] += 1
        return records
    need(expiration != NULL and strike != NULL_I64, "option row without an expiration or a strike")
    osi = row["raw_symbol"] if len(row["raw_symbol"]) == 21 and OSI.fullmatch(row["raw_symbol"]) else ""
    root = row["asset"] or osi[:6].rstrip()
    need(root, "option row without a root (empty asset column)")
    cfi = row["cfi"]
    option_body = dict(
        underlying_instrument_id=underlying,
        expiration_ns=expiration,
        strike=strike,
        contract_multiplier=NULL_I64,
        right=OPTION_RIGHT[cls],
        # Only from a filled option CFI code; never inferred from the symbol.
        exercise_style=EXERCISE_STYLE.get(cfi[2], 0) if len(cfi) == 6 and cfi[0] == "O" else 0,
        settlement=0,
        closing_type=0,
        option_flags=0,
    )
    option_texts = dict(root=root, underlying_symbol=row["underlying"], osi_symbol=osi, currency=currency)
    return records + [(11, head, option_body, option_texts)]


class Definitions:
    """Writes each instrument's INSTRUMENT_DEF (and OPTION_DEF) immediately before its first record.

    With --definitions FILE the rows of the venue's definition file are used (the last row of an instrument
    wins). Without it a minimal INSTRUMENT_DEF is built from the row's symbol and the policy options.

    An instrument whose definition row has no currency cannot be defined unless --currency supplies one. That
    stops the conversion, or with --skip-undefined leaves out the instrument's rows and counts them."""

    def __init__(self, job):
        self.job, self.rows, self.done, self.source = job, {}, {}, None  # done: output -> defined instruments
        self.undefined = set()
        path = option(job.args, "definitions")
        if path:
            need(isinstance(path, str), "--definitions needs a file")
            # A definition file can hold millions of rows: keep only the instruments this conversion will meet.
            wanted = {row["instrument_id"] for row in Source(job.src_path, ("instrument_id",), job.max_rows)}
            self.source = Source(path, DEFINITION_COLUMNS)
            at = self.source.header.index("instrument_id")
            for row in self.source.lists():
                if row[at] in wanted:
                    self.rows[row[at]] = (self.source.reader.line_num, dict(zip(self.source.header, row)))
            job.policy.append(
                "Each instrument's definition comes from the venue's definition file and is written before its first record."
            )
        else:
            required(job.args, "currency", "without --definitions the instrument currency is a policy option")
            required(job.args, "quantity_unit", "the source has no unit for order sizes (for example share or contract)")
            job.policy.append(
                "Each instrument gets a minimal INSTRUMENT_DEF before its first record: the row's symbol, "
                "asset class unspecified, and the currency, quantity unit and venue given as options."
            )

    def before(self, out, head, row):
        key = (head["publisher_id"], head["instrument_id"])  # definition scope: every channel of the publisher
        done = self.done.setdefault(out, set())
        if key in done:
            return True
        if key in self.undefined:
            self.job.skipped["rows of instruments left out by --skip-undefined"] += out is self.job.out
            return False
        if self.source:
            found = self.rows.get(row["instrument_id"])
            need(found, f"instrument {row['instrument_id']} is not in the definitions file")
            line, definition = found
            try:
                with located(self.source, line):
                    records = definition_records(definition, self.job, head["publisher_id"], head["channel_id"])
                    need(records, "the last definition row of a traded instrument deletes it")
            except NoCurrency:
                if option(self.job.args, "skip_undefined") is not True:
                    raise
                self.undefined.add(key)
                self.job.notes["instruments left out by --skip-undefined (no currency in the definition row)"] += 1
                return self.before(out, head, row)
        else:
            args = self.job.args
            need(row.get("symbol"), "the row has no symbol: pass --definitions FILE")
            body = dict(
                price_increment=NULL_I64, quantity_increment=NULL, contract_multiplier=NULL_I64, expiration_ns=NULL,
                underlying_instrument_id=0, strike=NULL_I64, asset_class=0,
            )  # fmt: skip
            texts = dict(
                symbol=row["symbol"], venue=option(args, "venue") or "", currency=args.currency,
                quantity_unit=args.quantity_unit,
            )  # fmt: skip
            records = [(6, dict(head, ts_event=NULL, ts_recv=NULL), body, texts)]
        done.add(key)
        for typ, definition_head, body, texts in records:
            out.add(typ, definition_head, texts=texts, **body)
        return True


def policy_options(args):
    """The options that decide what is written, as given on the command line (a bare flag is true)."""
    names = ("currency", "quantity_unit", "venue", "fill_rule", "skip_undefined", "max_rows")
    return {name: option(args, name) for name in names if option(args, name) is not None}


def convert_definition(src_path, out_path, args):
    """Definitions -> INSTRUMENT_DEF, and OPTION_DEF for calls and puts."""
    job = Job("csv-definition", "definition", src_path, args, DEFINITION_COLUMNS, (6,))
    required(args, "quantity_unit", "the source has no unit for order sizes (for example share or contract)")
    job.policy += [
        "Asset class: stock 1, future 2, call and put 3, every other source class 0 (unspecified).",
        "Currency is the row's currency, or --currency where the row has none; the quantity unit is --quantity-unit.",
        "Exercise style comes only from a filled option CFI code (third letter A or E); otherwise unknown.",
        "quantity_increment and contract_multiplier are null: the source has no equivalent column.",
    ]
    for row in job.source:
        try:
            with located(job.source):
                records = definition_records(row, job)
        except NoCurrency:
            if option(args, "skip_undefined") is not True:
                raise
            job.skipped["definition rows with no currency (left out by --skip-undefined)"] += 1
            continue
        for typ, head, body, texts in records:
            job.out.add(typ, head, texts=texts, **body)
    return job.finish(out_path)


# --------------------------------------------------------- order-level book


class Book:
    """Live orders of one (publisher, channel, instrument) and the aggregate size and count at each price."""

    def __init__(self):
        self.valid = False  # true after the first clear: an ADD alone cannot prove the book is complete
        self.orders = {}  # order_id -> [side, price, remaining quantity]
        self.levels = {}  # (side, price) -> [aggregate quantity, order count]
        self.trades = 0

    def shift(self, side, order_price, change, count):
        level = self.levels.setdefault((side, order_price), [0, 0])
        level[0] += change
        level[1] += count
        if level[1] == 0:
            del self.levels[side, order_price]
        return side, order_price

    def delta(self, side, order_price):
        size, count = self.levels.get((side, order_price), (0, 0))
        if count:
            return 15, dict(price=order_price, quantity=size, order_count=count, action=1, side=side, delta_flags=0)
        return 15, dict(price=order_price, quantity=0, order_count=NULL_U32, action=2, side=side, delta_flags=0)

    def clear(self):
        self.valid = True
        self.orders.clear()
        self.levels.clear()
        return [
            (4, dict(order_id=0, price=NULL_I64, quantity=0, priority=NULL, action=4, side=0, mbo_flags=0)),
            (15, dict(price=NULL_I64, quantity=0, order_count=NULL_U32, action=3, side=0, delta_flags=0)),
        ]

    def add(self, order_id, side, order_price, size):
        self.orders[order_id] = [side, order_price, size]
        self.shift(side, order_price, size, 1)
        body = dict(order_id=order_id, price=order_price, quantity=size, priority=NULL, action=1, side=side, mbo_flags=0)
        return [(4, body), self.delta(side, order_price)]

    def remove(self, order_id):
        side, order_price, size = self.orders.pop(order_id)
        self.shift(side, order_price, -size, -1)
        body = dict(order_id=order_id, price=NULL_I64, quantity=0, priority=NULL, action=3, side=0, mbo_flags=0)
        return [(4, body), self.delta(side, order_price)]

    def replace(self, order_id, order_price, size):
        order = self.orders[order_id]
        side, old_price, old_size = order
        self.shift(side, old_price, -old_size, -1)
        self.shift(side, order_price, size, 1)
        order[1:] = order_price, size
        body = dict(order_id=order_id, price=order_price, quantity=size, priority=NULL, action=2, side=side, mbo_flags=0)
        moved = [self.delta(side, old_price)] if old_price != order_price else []
        return [(4, body)] + moved + [self.delta(side, order_price)]

    def reduce(self, order_id, size):
        """Take `size` off an order: MODIFY with what remains, or DELETE when nothing remains."""
        _, order_price, remaining = self.orders[order_id]
        need(
            size <= remaining,
            f"size {nwt.pretty_decimal(size)} is more than the order's remaining {nwt.pretty_decimal(remaining)}",
        )
        return self.replace(order_id, order_price, remaining - size) if size < remaining else self.remove(order_id)


def mbo_items(source, fill_rule, skipped, notes):
    """Apply order-level rows in order. Yields (row, head, items) per source row; an item is (type, body):
    type 4 MBO, type 1 TRADE, and type 15 for the BOOK_DELTA records derived from the same change."""
    need(fill_rule in FILL_RULES, f"--fill-rule must be one of: {', '.join(FILL_RULES)}")
    books = {}
    for row in source:
        with located(source):
            head = head_of(row)
            action, flags = row["action"], number(row["flags"])
            need(flags & ~MBO_FLAG_BITS == 0, f"flags value {flags} has a bit this converter does not know")
            book = books.setdefault((head["publisher_id"], head["channel_id"], head["instrument_id"]), Book())
            items = []
            if action == "N":
                skipped["rows with no book effect (action N)"] += 1
            elif action == "R":
                items = book.clear()
            elif action == "T":
                size = quantity(row["size"])
                if row["price"] == "" or size == 0:
                    skipped["trade rows without a price or a size"] += 1
                else:
                    need(row["side"] in ("A", "B", "N"), f"unknown side {row['side']!r}")
                    book.trades += 1  # the source has no trade ID: 1, 2, 3, ... per instrument, in file order
                    items = [(1, dict(
                        price=price(row["price"]), quantity=size, trade_id=book.trades, original_sequence=0,
                        action=1, aggressor=SIDE.get(row["side"], 0), conditions=0,
                    ))]  # fmt: skip
            elif action in ("A", "C", "M", "F"):
                order_id, size = number(row["order_id"]), quantity(row["size"])
                live = order_id in book.orders
                if action == "F" and fill_rule == "cancel-carries-fill":
                    notes["fill rows (no book effect: the cancel row that follows carries the size)"] += 1
                else:
                    need(book.valid, "order event before the instrument's first clear (R) row")
                    need(order_id != 0, "order_id is 0")
                if action in ("A", "M"):
                    need(row["side"] in SIDE, f"unknown side {row['side']!r}")
                    side, order_price = SIDE[row["side"]], price(row["price"])
                    need(order_price != NULL_I64 and size > 0, "order without a price or a size")
                    if action == "A":
                        need(not live, f"add for order {order_id}, which is already in the book")
                        items = book.add(order_id, side, order_price, size)
                    elif not live:  # the row states the whole order, so it is written as an ADD
                        notes["modify rows for an order not in the book (written as ADD)"] += 1
                        items = book.add(order_id, side, order_price, size)
                    elif book.orders[order_id][0] != side:  # MODIFY must keep the side
                        items = book.remove(order_id) + book.add(order_id, side, order_price, size)
                    else:
                        items = book.replace(order_id, order_price, size)
                elif action == "C" or fill_rule == "fill-reduces":
                    need(live, f"{'cancel' if action == 'C' else 'fill'} for order {order_id}, which is not in the book")
                    items = book.reduce(order_id, size)
            else:
                raise ValueError(f"unknown action {action!r}")
        deltas = [body for typ, body in items if typ == 15]
        if deltas:
            deltas[-1]["delta_flags"] = 1  # LAST_IN_EVENT: the last delta derived from this source row
        yield row, head, items


def convert_mbo(src_path, out_path, args):
    """Order-level book -> MBO and TRADE; with --emit-deltas also a derived BOOK_DELTA file."""
    job = Job("csv-mbo", "mbo", src_path, args, EVENT_COLUMNS + ("order_id", "flags", "channel_id"), (4, 1, 6))
    fill_rule = option(args, "fill_rule") or FILL_RULES[0]
    emit = option(args, "emit_deltas")
    deltas_path = (str(Path(out_path).with_suffix("")) + ".deltas.nwt") if emit is True else emit
    need(deltas_path != out_path, "--emit-deltas must name a different file")
    deltas = Output((15, 6)) if emit else None
    job.use_definitions()
    job.policy += [
        "The source gives size changes; NWT MBO carries the remaining size, so every live order is tracked.",
        "Clear (R) -> CLEAR. Add (A) -> ADD. Cancel (C) -> MODIFY with the remaining size, or DELETE when nothing "
        "remains. Modify (M) -> MODIFY; a side change -> DELETE then ADD; a modify for an order not in the book -> ADD.",
        "Fill rule cancel-carries-fill: a fill (F) row does not change the book; the cancel row that follows it "
        "carries the filled size."
        if fill_rule == FILL_RULES[0]
        else "Fill rule fill-reduces: a fill (F) row takes its size off the order, like a cancel.",
        "Trade (T) -> TRADE NEW with trade IDs 1, 2, 3, ... per instrument in file order; the side column is the aggressor.",
        "Priority is null: the source gives no queue rank.",
    ]
    levels = {}  # (publisher, channel, instrument) -> side -> prices, to hold the BOOK_DELTA limit of 1024 levels
    for row, head, items in mbo_items(job.source, fill_rule, job.skipped, job.notes):
        with located(job.source):
            if not items or not job.define(job.out, head, row):
                continue
            for typ, body in items:
                if typ != 15:
                    job.out.add(typ, head, **body)
                elif deltas:
                    sides = levels.setdefault((head["publisher_id"], head["channel_id"], head["instrument_id"]), {})
                    if body["action"] == 3:
                        sides.clear()
                    elif body["action"] == 2:
                        sides[body["side"]].discard(body["price"])
                    else:
                        prices = sides.setdefault(body["side"], set())
                        prices.add(body["price"])
                        need(len(prices) <= 1024, "more than 1024 price levels on one side: BOOK_DELTA cannot carry it")
                    job.define(deltas, head, row)
                    deltas.add(15, head, **body)
    job.extra["policy_options"] = dict(policy_options(args), fill_rule=fill_rule)
    summary = job.finish(out_path)
    if deltas:
        job.policy.append(
            "DERIVED: the BOOK_DELTA records are not in the source. Each one is the aggregate size and order count "
            "at a price after one order-level row was applied; LAST_IN_EVENT marks the last delta of each source row."
        )
        try:
            summary = dict(summary, deltas=job.write(deltas, deltas_path, "deltas"))
        except BaseException:
            Path(out_path).unlink(missing_ok=True)
            raise
    return summary


# ------------------------------------------------------------ top of book


def quote_side(row, prefix, level, job):
    """(price, quantity, order count) of one side of one level, under the QUOTE presence rules."""
    side_price = price(row[f"{prefix}_px_{level}"])
    size = quantity(row[f"{prefix}_sz_{level}"])
    if side_price == NULL_I64:
        need(size == 0, f"{prefix} level {level} has a size but no price")
        return NULL_I64, 0, 0
    need(size > 0, f"{prefix} level {level} has a price but size 0")
    count = number(row.get(f"{prefix}_ct_{level}", "0"), NULL_U32)
    if count == 0 and f"{prefix}_ct_{level}" in row:
        job.notes["present sides with a source order count of 0 (written as a null count)"] += 1
    return side_price, size, count or NULL_U32


def top_of_book(row, job):
    bid, ask = quote_side(row, "bid", "00", job), quote_side(row, "ask", "00", job)
    return dict(
        bid_price=bid[0], ask_price=ask[0], bid_quantity=bid[1], ask_quantity=ask[1],
        bid_order_count=bid[2], ask_order_count=ask[2],
    )  # fmt: skip


def events(job, actions="ACMRTFN"):
    """(row, head) per source row of a top-of-book or depth file, with the definition written first."""
    job.use_definitions()
    for row in job.source:
        with located(job.source):
            need(row["action"] in tuple(actions), f"unknown action {row['action']!r}")
            head = head_of(row)
            defined = job.define(job.out, head, row)
        if defined:
            yield row, head


def trade_of(row, job):
    """(price, quantity, aggressor) of a trade row, or None when the row has no price or no size."""
    need(row["side"] in ("A", "B", "N"), f"unknown side {row['side']!r}")
    size = quantity(row["size"])
    if row["price"] == "" or size == 0:
        job.skipped["trade rows without a price or a size (no trade record)"] += 1
        return None
    return price(row["price"]), size, SIDE.get(row["side"], 0)


def convert_mbp1(src_path, out_path, args):
    """Top of book -> QUOTE for every row, and TRADE_QUOTE for trade rows."""
    job = Job("csv-mbp1", "mbp-1", src_path, args, EVENT_COLUMNS + TOP_COLUMNS + ("bid_ct_00", "ask_ct_00"), (2, 18, 6))
    job.policy += [
        "Every row -> QUOTE with the row's book columns (the top of book after the event).",
        "A trade (T) row also -> TRADE_QUOTE: on a trade row the book columns are the top of book at the trade. "
        "trade_id is 0 (the source has none); the side column is the aggressor.",
        "An absent side has no price in the source. A present side with a source order count of 0 gets a null count.",
        "TRADE records for the same prints come from the order-level file and go to a different container.",
    ]
    for row, head in events(job):
        with located(job.source):
            top = top_of_book(row, job)
            job.out.add(2, head, quote_flags=0, **top)
            trade = trade_of(row, job) if row["action"] == "T" else None
            if trade:
                job.out.add(18, head, price=trade[0], quantity=trade[1], trade_id=0, aggressor=trade[2], conditions=0, **top)
    return job.finish(out_path)


def convert_mbp10(src_path, out_path, args):
    """Ten-level depth -> one depth-limited BOOK_SNAPSHOT per row."""
    job = Job("csv-mbp10", "mbp-10", src_path, args, EVENT_COLUMNS + TOP_COLUMNS, (5, 6))
    depth = [name[7:] for name in job.source.header if name.startswith("bid_px_")]
    job.policy += [
        f"Every row -> BOOK_SNAPSHOT with the row's {len(depth)} levels and the depth-limited flag set.",
        "Trailing levels that are empty on both sides are dropped. A row with an empty level above a filled one, "
        "or with bid or ask prices out of order, stops the conversion.",
        "Trade rows restate the book; the trade print itself is not carried by this kind.",
    ]
    for row, head in events(job):
        with located(job.source):
            sides = [[quote_side(row, prefix, level, job) for level in depth] for prefix in ("bid", "ask")]
            filled = []
            for side, name, step in zip(sides, ("bid", "ask"), (-1, 1)):
                prices = [level[0] for level in side if level[0] != NULL_I64]
                need(all(level[0] != NULL_I64 for level in side[: len(prices)]), f"{name}: an empty level above a filled one")
                need(all((b - a) * step > 0 for a, b in zip(prices, prices[1:])), f"{name} prices are out of order")
                filled.append(len(prices))
            levels = [
                dict(bid_price=b[0], ask_price=a[0], bid_quantity=b[1], ask_quantity=a[1], bid_count=b[2], ask_count=a[2])
                for b, a in list(zip(*sides))[: max(filled)]
            ]
            if row["action"] == "T":
                job.notes["trade rows (book restated; the print is not carried)"] += 1
            job.out.add(5, head, levels=levels, book_flags=1)
    return job.finish(out_path)


def convert_cmbp1(src_path, out_path, args):
    """Consolidated top of book -> BEST_QUOTE with the venue that set each side."""
    job = Job("csv-cmbp1", "cmbp-1", src_path, args, EVENT_COLUMNS + TOP_COLUMNS + ("bid_pb_00", "ask_pb_00"), (19, 6))
    job.policy += [
        "Every row -> BEST_QUOTE, event-driven (interval_ns 0). bid_publisher_id and ask_publisher_id are the "
        "source's venue IDs for each side, 0 on an absent side. Every ID is declared in the manifest as publisher-<id>.",
        "The source has no order counts: a present side has a null count.",
        "Trade rows restate the best quote under the publisher of the row; the trade print itself is not carried by this kind.",
    ]
    for row, head in events(job):
        with located(job.source):
            top = top_of_book(row, job)
            venues = {}
            for side in ("bid", "ask"):
                venue = number(row[f"{side}_pb_00"], NULL_U32)
                venues[side] = venue if top[f"{side}_price"] != NULL_I64 else 0
                if venues[side]:
                    job.out.publishers.add(venues[side])
            if row["action"] == "T":
                job.notes["trade rows (best quote restated; the print is not carried)"] += 1
            job.out.add(
                19, head, quote_flags=0, bid_publisher_id=venues["bid"], ask_publisher_id=venues["ask"],
                interval_ns=0, **top,
            )  # fmt: skip
    return job.finish(out_path)


# -------------------------------------------------------------------- bars


def trade_tally(path, wanted):
    """{(publisher, instrument, minute start): [trade rows, summed size]} for the wanted minutes, and the file's hash.

    The bars are built from the capture time of the trade rows, so the minute is taken from ts_recv."""
    source = Source(path, ("ts_recv", "publisher_id", "instrument_id", "action", "size"))
    at = {name: source.header.index(name) for name in ("ts_recv", "publisher_id", "instrument_id", "action", "size")}
    tally = {}
    for row in source.lists():
        if row[at["action"]] != "T":
            continue
        with located(source):
            time = parse_timestamp_ns(row[at["ts_recv"]])
            key = (row[at["publisher_id"]], row[at["instrument_id"]], time - time % MINUTE)
            if key in wanted:
                entry = tally.setdefault(key, [0, 0])
                entry[0] += 1
                entry[1] += quantity(row[at["size"]])
    return tally, source.sha256()


def convert_ohlcv(src_path, out_path, args):
    """One-minute bars -> BAR, with the trade count taken from the venue's trade rows."""
    columns = ("ts_event", "rtype", "publisher_id", "instrument_id", "open", "high", "low", "close", "volume", "symbol")
    job = Job("csv-ohlcv", "ohlcv-1m", src_path, args, columns, (3, 6))
    trades = required(
        args, "trades",
        "the venue's top-of-book or order-level file; the source bars have no trade count and none is ever invented",
    )  # fmt: skip
    job.policy += [
        "The source timestamp is the start of the minute: the BAR interval is [start, start + 60 s) and ts_event is its end.",
        "trade_count is the number of trade (T) rows of the --trades file whose capture time (ts_recv) falls in the "
        "minute, for the same publisher and instrument. Their summed size must equal the bar's volume, or the conversion fails.",
    ]
    bars = []
    for row in job.source:
        with located(job.source):
            need(row["rtype"] == "33", f"rtype {row['rtype']!r} is not a one-minute bar")
            head = head_of(row)
            need(head["ts_event"] != NULL and head["ts_event"] % MINUTE == 0, "bar time is not the start of a minute")
            bars.append((job.source.reader.line_num, row, head))
    tally, job.extra["trades_sha256"] = trade_tally(
        trades, {(row["publisher_id"], row["instrument_id"], head["ts_event"]) for _, row, head in bars}
    )
    job.use_definitions()
    for line, row, head in bars:
        with located(job.source, line):
            start, volume = head["ts_event"], quantity(row["volume"])
            count, traded = tally.get((row["publisher_id"], row["instrument_id"], start), (0, 0))
            need(
                count > 0 and traded == volume,
                f"bar volume {row['volume']} is not the summed size of the {count} trade rows of its minute",
            )
            body = {name: price(row[name]) for name in ("open", "high", "low", "close")}
            need(NULL_I64 not in body.values() and volume > 0, "bar without a price or a volume")
            need(body["low"] <= min(body["open"], body["close"]), "low is above the open or the close")
            need(body["high"] >= max(body["open"], body["close"]), "high is below the open or the close")
            head = dict(head, ts_event=start + MINUTE)
            if not job.define(job.out, head, row):
                continue
            job.out.add(
                3, head, interval_start_ns=start, interval_end_ns=start + MINUTE, volume=volume,
                trade_count=count, bar_flags=0, **body,
            )  # fmt: skip
    return job.finish(out_path)


# -------------------------------------------------------------- statistics


def convert_statistics(src_path, out_path, args):
    """Venue statistics -> STATISTICS."""
    columns = (
        "ts_recv", "ts_event", "publisher_id", "instrument_id", "ts_ref", "price", "quantity", "stat_type",
        "channel_id", "update_action", "stat_flags", "symbol",
    )  # fmt: skip
    job = Job("csv-statistics", "statistics", src_path, args, columns, (13, 6))
    job.use_definitions()
    job.policy += [
        "Source stat_type -> NWT stat_type: 1 opening price -> 1 open; 5 session high -> 2 high; 4 session low -> 3 low; "
        "11 close price -> 4 close; 3 settlement price -> 5 settlement; 6 cleared volume -> 7 volume; "
        "9 open interest -> 8 open interest. Any other source type stops the conversion.",
        "update_action 1 -> SET, 2 -> DELETE. An empty ts_ref is null.",
        "On a settlement price, source stat_flags bit 0 means final: a settlement without it is written with the "
        "preliminary bit set. Any other flag value, or a flag on another type, stops the conversion.",
        "A row with no value (an empty price, or the source's null quantity) is skipped and counted.",
    ]
    for row in job.source:
        with located(job.source):
            need(row["stat_type"] in STAT_TYPES, f"unknown stat_type {row['stat_type']!r}")
            stat_type, column = STAT_TYPES[row["stat_type"]]
            need(row["update_action"] in ("1", "2"), f"unknown update_action {row['update_action']!r}")
            source_quantity = "" if row["quantity"] == SOURCE_NULL_QUANTITY else row["quantity"]
            final = row["stat_flags"] == "1" and row["stat_type"] == SOURCE_SETTLEMENT
            need(row["stat_flags"] == "0" or final, f"stat_flags {row['stat_flags']!r} on stat_type {row['stat_type']}")
            value = dict(price=NULL_I64, quantity=NULL, stat_flags=0)
            if row["update_action"] == "1":
                other = source_quantity if column == "price" else row["price"]
                need(other == "", f"a {column} statistic that also carries a value in the other column")
                if (row["price"] if column == "price" else source_quantity) == "":
                    job.skipped["statistics rows with no value"] += 1
                    continue
                if column == "price":
                    value["price"] = price(row["price"])
                    value["stat_flags"] = int(row["stat_type"] == SOURCE_SETTLEMENT and not final)
                else:
                    value["quantity"] = quantity(source_quantity)
            head = head_of(row)
            if not job.define(job.out, head, row):
                continue
            job.out.add(13, head, ts_ref=timestamp(row["ts_ref"]), stat_type=stat_type, action=int(row["update_action"]), **value)
    return job.finish(out_path)


# ------------------------------------------------------------ command line

KINDS = {
    "csv-definition": convert_definition,
    "csv-mbo": convert_mbo,
    "csv-mbp1": convert_mbp1,
    "csv-mbp10": convert_mbp10,
    "csv-cmbp1": convert_cmbp1,
    "csv-ohlcv": convert_ohlcv,
    "csv-statistics": convert_statistics,
}


def add_kinds(registry):
    registry.update(KINDS)


def parse_options(tokens):
    """--name value, --name=value and bare --flag (True), as tools/nwt_convert.py passes them."""
    args, i = SimpleNamespace(), 0
    while i < len(tokens):
        need(tokens[i].startswith("--") and len(tokens[i]) > 2, f"expected an --option, found {tokens[i]!r}")
        name, equals, value = tokens[i][2:].partition("=")
        if not equals:
            flag = i + 1 == len(tokens) or tokens[i + 1].startswith("--")
            value = True if flag else tokens[i + 1]
            i += 0 if flag else 1
        name = name.replace("-", "_")
        need(name.isidentifier() and not hasattr(args, name), f"bad or repeated option {tokens[i]!r}")
        setattr(args, name, value)
        i += 1
    return args


def main(argv):
    try:
        need(len(argv) >= 3 and argv[0] in KINDS, f"usage: nwt_convert_market.py KIND SRC OUT --dataset NAME [options]; kinds: {', '.join(KINDS)}")
        summary = KINDS[argv[0]](argv[1], argv[2], parse_options(argv[3:]))
    except ERRORS as error:
        print(f"NWT error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
