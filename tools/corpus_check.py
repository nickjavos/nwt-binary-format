#!/usr/bin/env python3

import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "examples/python", ROOT / "tools"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
import nwt_example as nwt
import nwt_convert_market as market

KIND = {
    "definition": "csv-definition", "mbo": "csv-mbo", "mbp-1": "csv-mbp1", "mbp-10": "csv-mbp10",
    "cmbp-1": "csv-cmbp1", "ohlcv-1m": "csv-ohlcv", "statistics": "csv-statistics",
}
TRADE_SCHEMAS = ("mbp-1", "mbo", "cmbp-1")
FALLBACK_CURRENCY = {"equities": "USD", "xcbf.pitch": "USD"}
ERRORS = market.ERRORS


def best(levels, side):
    prices = [level_price for level_side, level_price in levels if level_side == side]
    if not prices:
        return nwt.NULL_I64, 0, 0
    top = max(prices) if side == 1 else min(prices)
    return (top, *levels[side, top])


def check_mbo_against_top(mbo_path, top_path, args, rows=20000):
    top = {}
    source = market.Source(top_path, market.EVENT_COLUMNS + market.TOP_COLUMNS + ("sequence",), rows)
    last = None
    for row in source:
        last = (row["publisher_id"], row["instrument_id"], row["sequence"])
        counts = [market.number(row[f"{side}_ct_00"]) for side in ("bid", "ask")]
        sides = [(market.price(row[f"{s}_px_00"]), market.quantity(row[f"{s}_sz_00"]), n) for s, n in zip(("bid", "ask"), counts)]
        top[last] = (tuple(sides), row["action"] == "T")
    top.pop(last, None)
    orders, levels = {}, {}
    rebuilt, at_trade, key = {}, {}, None
    source = market.Source(mbo_path, market.EVENT_COLUMNS + ("order_id", "flags", "channel_id", "sequence"), rows)
    fill_rule = getattr(args, "fill_rule", None) or market.FILL_RULES[0]
    for row, head, items in market.mbo_items(source, fill_rule, Counter(), Counter()):
        book = (row["publisher_id"], row["instrument_id"])
        book_orders, book_levels = orders.setdefault(book, {}), levels.setdefault(book, {})
        for typ, body in items:
            if typ != 4:
                continue
            action, order_id = body["action"], body["order_id"]
            if action == 4:
                book_orders.clear()
                book_levels.clear()
                continue
            if order_id in book_orders:
                side, old_price, old_quantity = book_orders.pop(order_id)
                level = book_levels[side, old_price]
                level[0] -= old_quantity
                level[1] -= 1
                if level[1] == 0:
                    del book_levels[side, old_price]
            if action in (1, 2):
                side = body["side"]
                book_orders[order_id] = (side, body["price"], body["quantity"])
                level = book_levels.setdefault((side, body["price"]), [0, 0])
                level[0] += body["quantity"]
                level[1] += 1
        key = (*book, row["sequence"])
        rebuilt[key] = (best(book_levels, 1), best(book_levels, 2))
        if row["action"] == "T":
            at_trade[key] = rebuilt[key]
    rebuilt.pop(key, None)
    # A top-of-book trade row shows the book at the trade, before the fill and cancel of the same sequence.
    book_at = lambda k: at_trade.get(k, rebuilt[k]) if top[k][1] else rebuilt[k]
    shared = [k for k in rebuilt if k in top and k[2] != "0"]
    wrong = [k for k in shared if book_at(k) != top[k][0]]
    examples = [f"sequence {k[2]}: rebuilt {book_at(k)}, top of book {top[k][0]}" for k in wrong[:5]]
    return len(shared), len(wrong), examples


def corpus(root):
    found = []
    for path in sorted(root.glob("*/*.csv")):
        parts = path.stem.split("_")
        if len(parts) == 3 and parts[0] == path.parent.name and parts[1] in KIND:
            found.append((parts[0], parts[1], parts[2], path))
        else:
            print(f"notice: {path.parent.name}/{path.name} does not follow <venue>_<schema>_<class>.csv; left out")
    return found


def check_file(venue, schema, cls, path, files, rows, work):
    from market_state import validate

    equities = any(v == venue and c == "equities" for v, _, c in files)
    options = dict(
        dataset="REAL." + venue.upper(), max_rows=str(rows), quantity_unit="share" if equities else "contract"
    )
    currency = FALLBACK_CURRENCY.get("equities" if equities else cls) or FALLBACK_CURRENCY.get(venue)
    if currency:
        options["currency"] = currency
    definitions = files.get((venue, "definition", "all"))
    if schema != "definition" and definitions:
        options["definitions"] = str(definitions)
    if schema == "ohlcv-1m":
        trades = next((files[venue, s, cls] for s in TRADE_SCHEMAS if (venue, s, cls) in files), None)
        if trades is None:
            return 0, 0, 0, "FAIL: the venue has no file with trade rows for this class"
        options["trades"] = str(trades)
    args = SimpleNamespace(**options)
    out = os.path.join(work, "check.nwt")
    try:
        summary = market.KINDS[KIND[schema]](str(path), out, args)
        with open(out, "rb") as f:
            records = list(nwt.complete_records(nwt.open_reader(f)))
        written = sum(summary["records_written"].values())
        skipped = sum(summary["rows_skipped"].values())
        if len(records) != written:
            return summary["source_rows"], len(records), skipped, f"FAIL: {written} records written, {len(records)} read back"
        validate(records)
        result = "ok"
        top = files.get((venue, "mbp-1", cls))
        if schema == "mbo" and top:
            compared, wrong, examples = check_mbo_against_top(str(path), str(top), args, rows)
            result = f"ok; top of book equal at {compared} shared sequences"
            if wrong:
                result = f"FAIL: top of book differs at {wrong} of {compared} shared sequences; {examples[0]}"
        return summary["source_rows"], written, skipped, result
    except ERRORS as error:
        return 0, 0, 0, "FAIL: " + " ".join(str(error).split())
    finally:
        Path(out).unlink(missing_ok=True)


def main(argv):
    rows = int(argv[argv.index("--rows") + 1]) if "--rows" in argv else 20000
    samples = os.environ.get("NWT_SAMPLES_DIR")
    if not samples:
        print("notice: NWT_SAMPLES_DIR is not set; the corpus check needs the sample folder and was skipped")
        return 0
    root = Path(samples)
    found = corpus(root / "normalized" if (root / "normalized").is_dir() else root)
    files = {(venue, schema, cls): path for venue, schema, cls, path in found}
    print("| Venue | Schema | Class | Rows in | Records out | Skipped | Result |")
    print("|---|---|---|---:|---:|---:|---|", flush=True)
    failures = 0
    with tempfile.TemporaryDirectory() as work:
        for venue, schema, cls, path in found:
            rows_in, records, skipped, result = check_file(venue, schema, cls, path, files, rows, work)
            failures += result.startswith("FAIL")
            line = f"| {venue.upper()} | {schema} | {cls} | {rows_in} | {records} | {skipped} | {result.replace('|', '/')} |"
            print(line, flush=True)
    print(f"{len(found) - failures} of {len(found)} files passed; {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
