
import json
from copy import deepcopy

NULL_U64 = (1 << 64) - 1
NULL_I64 = -(1 << 63)
NULL_COUNT = (1 << 32) - 1
ASSET_OPTION = 3
MARKET_TYPES = (1, 2, 3, 4, 5, 7, 13, 14, 15, 16, 18, 19)
INSTRUMENT_TYPES = (11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22)
PRICE_STATS = (1, 2, 3, 4, 5, 6)
ANALYTICS = ("implied_volatility", "delta", "gamma", "theta", "vega", "rho")
MAX_LEVELS = 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sorted_json_object(text):

    def pairs(items):
        keys = [k for k, _ in items]
        require(len(set(keys)) == len(keys), "details has a duplicate key")
        require(keys == sorted(keys), "details keys are not sorted")
        return dict(items)

    value = json.loads(text, object_pairs_hook=pairs)
    require(isinstance(value, dict), "details must be one JSON object")


def overlaps(a, b):
    return (b[1] is None or a[0] < b[1]) and (a[1] is None or b[0] < a[1])


def present_side(price, quantity, count):
    if price == NULL_I64:
        require(quantity == count == 0, "absent side must have zero size/count")
        return False
    require(0 < quantity < NULL_U64, "present side requires positive size")
    require(0 < count <= NULL_COUNT, "present side count must be positive or null")
    return True


class MarketState:
    def __init__(self, publishers=None):
        self.publishers = publishers
        self.definitions = {}
        self.trades = {}
        self.bars = set()
        self.mbo = {}
        self.working = {}
        self.quotes = {}
        self.depth = {}
        self.status = {}
        self.gaps = set()
        self.sequences = {}
        self.events = []
        self.books = {}
        self.venues = {}
        self.options = {}
        self.statistics = {}
        self.analytics = {}
        self.imbalances = {}
        self.symbol_maps = {}
        self.best_quotes = {}
        self.securities = {}
        self.actions = {}

    def apply(self, record):
        f = {k: int(v) for k, v in record["fields"].items()}
        texts = record["texts"]
        typ = f["record_type"]
        pub, channel, inst = f["publisher_id"], f["channel_id"], f["instrument_id"]
        key = (pub, channel, inst)
        scope = (pub, channel)
        seq = f["sequence"]
        require(seq == self.sequences.get(scope, 0) + 1, "sequence continuity")
        self.sequences[scope] = seq
        require(typ in range(1, 23) and f["schema_version"] == 1, "supported schema")
        require(f["flags"] & ~3 == 0, "record flags")
        if "reserved" in f:
            require(f["reserved"] == 0, "record reserved")
        if typ <= 7 or typ in INSTRUMENT_TYPES:
            require(pub != 0 and inst != 0, "instrument scope")
        if typ in MARKET_TYPES:
            require((pub, inst) in self.definitions, "definition must precede data")

        if typ == 6:
            require(0 <= f["asset_class"] <= 7, "asset class")
            for name, null in [
                ("price_increment", NULL_I64),
                ("quantity_increment", NULL_U64),
                ("contract_multiplier", NULL_I64),
            ]:
                require(f[name] == null or f[name] > 0, "positive increment/multiplier")
            previous = self.definitions.get((pub, inst))
            if previous:
                require(
                    all(
                        previous["texts"][n] == texts[n]
                        for n in ("currency", "quantity_unit")
                    ),
                    "unit identity changed",
                )
            self.definitions[(pub, inst)] = deepcopy(record)
            if (pub, inst) in self.options:
                self.option_agrees(f, self.options[(pub, inst)])

        elif typ == 1:
            action = f["action"]
            require(action in (1, 2, 3) and f["aggressor"] in (0, 1, 2), "trade enums")
            require(f["conditions"] & ~1 == 0 and f["trade_id"] != 0, "trade fields")
            trade_key = key + (f["trade_id"],)
            if action == 1:
                require(
                    trade_key not in self.trades and f["original_sequence"] == 0,
                    "duplicate/new reference",
                )
                self.trades[trade_key] = {"original": seq, "active": True}
            else:
                require(trade_key in self.trades, "missing original trade")
                trade = self.trades[trade_key]
                require(
                    trade["active"] and f["original_sequence"] == trade["original"],
                    "invalid lifecycle reference",
                )
            if action == 2:
                require(
                    f["price"] == NULL_I64
                    and f["quantity"] == NULL_U64
                    and f["aggressor"] == f["conditions"] == 0,
                    "cancel payload",
                )
                self.trades[trade_key]["active"] = False
            else:
                require(
                    f["price"] != NULL_I64 and 0 < f["quantity"] < NULL_U64,
                    "trade price/quantity",
                )
                self.trades[trade_key]["price"] = f["price"]
                self.trades[trade_key]["quantity"] = f["quantity"]

        elif typ == 2:
            require(f["quote_flags"] & ~1 == 0, "quote flags")
            for side in ("bid", "ask"):
                present_side(
                    f[side + "_price"], f[side + "_quantity"], f[side + "_order_count"]
                )
            self.quotes[key] = deepcopy(record)

        elif typ == 3:
            start, end = f["interval_start_ns"], f["interval_end_ns"]
            require(start < end < NULL_U64 and f["ts_event"] == end, "bar interval")
            bar_key = key + (start, end)
            require(bar_key not in self.bars, "duplicate bar")
            self.bars.add(bar_key)
            require(f["bar_flags"] in (0, 1), "bar flags")
            prices = [f[x] for x in ("open", "high", "low", "close")]
            if f["bar_flags"]:
                require(
                    all(x == NULL_I64 for x in prices)
                    and f["volume"] == f["trade_count"] == 0,
                    "empty bar",
                )
            else:
                require(
                    NULL_I64 not in prices
                    and f["low"] <= f["open"] <= f["high"]
                    and f["low"] <= f["close"] <= f["high"],
                    "OHLC bounds",
                )
                require(
                    0 < f["volume"] < NULL_U64 and 0 < f["trade_count"] < NULL_COUNT,
                    "bar volume/count",
                )

        elif typ == 4:
            action, order = f["action"], f["order_id"]
            require(
                action in range(1, 7)
                and f["side"] in (0, 1, 2)
                and f["mbo_flags"] == 0,
                "MBO enums",
            )
            if key in self.working:
                require(action in (1, 6), "only ADD/END allowed during snapshot")
            if action in (3, 4, 5, 6):
                require(
                    f["side"] == 0
                    and f["price"] == NULL_I64
                    and f["quantity"] == 0
                    and f["priority"] == NULL_U64,
                    "MBO control payload",
                )
            if action in (4, 5, 6):
                require(order == 0, "control order ID")
            if action == 4:
                self.mbo[key] = {}
            elif action == 5:
                self.working[key] = {}
            elif action == 6:
                require(key in self.working, "snapshot end without begin")
                self.mbo[key] = self.working.pop(key)
            else:
                require(order != 0, "order ID")
                require(
                    key in self.working or key in self.mbo,
                    "MBO is not initialized or needs recovery",
                )
                book = self.working[key] if key in self.working else self.mbo[key]
                if action == 1:
                    require(order not in book, "duplicate live order")
                else:
                    require(order in book, "unknown order")
                if action == 3:
                    del book[order]
                else:
                    require(
                        f["side"] in (1, 2)
                        and f["price"] != NULL_I64
                        and 0 < f["quantity"] < NULL_U64,
                        "MBO price/side/quantity",
                    )
                    if action == 2:
                        require(
                            book[order]["side"] == f["side"],
                            "modify cannot change side",
                        )
                    book[order] = deepcopy(f)

        elif typ == 5:
            levels = [
                {k: int(v) for k, v in level.items()} for level in record["levels"]
            ]
            require(
                len(levels) == f["levels"] <= 1024 and f["book_flags"] & ~1 == 0,
                "depth fields",
            )
            for side in ("bid", "ask"):
                previous = None
                absent = False
                for level in levels:
                    require(level["reserved"] == 0, "level reserved")
                    price = level[side + "_price"]
                    is_present = present_side(
                        price, level[side + "_quantity"], level[side + "_count"]
                    )
                    if is_present:
                        require(not absent, "absent levels must be a suffix")
                        if previous is not None:
                            require(
                                price < previous if side == "bid" else price > previous,
                                "depth rank ordering",
                            )
                        previous = price
                    else:
                        absent = True
            if levels:
                require(
                    any(
                        levels[-1][side + "_price"] != NULL_I64
                        for side in ("bid", "ask")
                    ),
                    "trailing empty paired level",
                )
            self.depth[key] = deepcopy(record)
            book = {"limited": bool(f["book_flags"] & 1), 1: {}, 2: {}}
            for level in levels:
                for side, name in ((1, "bid"), (2, "ask")):
                    if level[name + "_price"] != NULL_I64:
                        book[side][level[name + "_price"]] = (level[name + "_quantity"], level[name + "_count"])
            self.books[key] = book

        elif typ == 7:
            require(
                f["status"] in range(6)
                and f["reason"] in range(5)
                and f["status_flags"] == 0,
                "status enum/flags",
            )
            self.status[key] = f["status"]

        elif typ == 8:
            require(
                pub != 0 and inst == 0 and f["reason"] in range(1, 5),
                "GAP scope/reason",
            )
            a, b = f["first_missing_source_sequence"], f["last_missing_source_sequence"]
            require((a == b == NULL_U64) or (a <= b < NULL_U64), "GAP range")
            recovery = f["recovery_id"]
            require(
                recovery != 0 and recovery not in self.gaps, "recovery ID uniqueness"
            )
            self.gaps.add(recovery)
            for mapping in (
                self.mbo,
                self.working,
                self.quotes,
                self.depth,
                self.status,
                self.books,
                self.best_quotes,
            ):
                for old in list(mapping):
                    if old[:2] == scope:
                        del mapping[old]

        elif typ == 9:
            require(inst == 0 and (pub != 0 or channel == 0), "SYSTEM scope")
            code = f["code"]
            require(
                code in range(1, 5) and f["severity"] == max(0, code - 2),
                "SYSTEM code/severity",
            )
            related = f["related_recovery_id"]
            require(related == 0 or related in self.gaps, "unknown recovery reference")
            if code == 1:
                require(texts["text"] == "" and related == 0, "heartbeat payload")

        else:
            self.apply_extended(typ, f, texts, key)

        self.events.append(
            {
                "sequence": seq,
                "type": typ,
                "valid_mbo_books": len(self.mbo),
                "open_snapshots": len(self.working),
            }
        )

    @staticmethod
    def option_agrees(definition, option):
        require(definition["asset_class"] == ASSET_OPTION, "OPTION_DEF needs an option INSTRUMENT_DEF")
        for name in ("expiration_ns", "strike", "underlying_instrument_id"):
            require(definition[name] == option[name], "OPTION_DEF disagrees with INSTRUMENT_DEF on " + name)

    def apply_delta(self, key, f):
        action, side, price, quantity, count = f["action"], f["side"], f["price"], f["quantity"], f["order_count"]
        require(action in (1, 2, 3) and side in (0, 1, 2), "delta enums")
        if action == 3:
            require(price == NULL_I64 and quantity == 0 and count == NULL_COUNT, "CLEAR payload")
            if side == 0:
                book = self.books.setdefault(key, {"limited": False, 1: {}, 2: {}})
                book[1].clear()
                book[2].clear()
            else:
                require(key in self.books, "BOOK_DELTA needs a valid book")
                self.books[key][side].clear()
            return
        require(key in self.books, "BOOK_DELTA needs a valid book")
        require(side in (1, 2) and price != NULL_I64, "delta side/price")
        book = self.books[key]
        levels = book[side]
        if action == 1:
            require(0 < quantity < NULL_U64 and 0 < count <= NULL_COUNT, "SET size/count")
            levels[price] = (quantity, count)
            require(len(levels) <= MAX_LEVELS, "book side exceeds 1024 levels")
        else:
            require(quantity == 0 and count == NULL_COUNT, "DELETE payload")
            require(price in levels or book["limited"], "DELETE of a missing level")
            levels.pop(price, None)

    def apply_extended(self, typ, f, texts, key):
        pub, channel, inst = key
        if typ == 10:
            require(pub != 0 and inst == 0, "VENUE_DEF scope")
            require(f["kind"] != 1 or texts["mic"] == texts["operating_mic"], "operating venue needs equal MICs")
            for name in ("mic", "operating_mic", "country"):
                text = texts[name]
                require(text.isascii() and text.isalnum() and text == text.upper(), name + " must be A-Z or 0-9")
            self.venues[(pub, texts["mic"])] = f

        elif typ == 11:
            require(f["expiration_ns"] != NULL_U64 and f["strike"] != NULL_I64, "option expiration/strike")
            require(f["contract_multiplier"] == NULL_I64 or f["contract_multiplier"] > 0, "positive multiplier")
            require(f["underlying_instrument_id"] != 0 or texts["underlying_symbol"] != "", "option underlying")
            definition = self.definitions.get((pub, inst))
            if definition:
                self.option_agrees({k: int(v) for k, v in definition["fields"].items()}, f)
            self.options[(pub, inst)] = f

        elif typ == 12:
            flags = f["financial_flags"]
            require(flags & 14 == 0 or flags & 1, "financial flags 1-3 need bit 0")

        elif typ == 13:
            stat, price_type = f["stat_type"], f["stat_type"] in PRICE_STATS
            require(stat in range(1, 9) and f["action"] in (1, 2) and f["stat_flags"] & ~1 == 0, "statistics enums")
            stat_key = key + (stat, f["ts_ref"])
            if f["action"] == 1:
                has_price, has_quantity = f["price"] != NULL_I64, f["quantity"] != NULL_U64
                require(has_price == price_type and has_quantity != price_type, "statistics SET value")
                self.statistics[stat_key] = (f["price"], f["quantity"])
            else:
                require(f["price"] == NULL_I64 and f["quantity"] == NULL_U64 and f["stat_flags"] == 0, "DELETE payload")
                self.statistics.pop(stat_key, None)

        elif typ == 14:
            require(int(self.definitions[(pub, inst)]["fields"]["asset_class"]) == ASSET_OPTION, "analytics need option")
            require(any(f[name] != NULL_I64 for name in ANALYTICS), "analytics are all null")
            for name in ("implied_volatility", "gamma"):
                require(f[name] == NULL_I64 or f[name] >= 0, name + " is negative")
            require(f["delta"] == NULL_I64 or -(10**9) <= f["delta"] <= 10**9, "delta out of range")
            self.analytics[key] = f

        elif typ == 15:
            self.apply_delta(key, f)

        elif typ == 16:
            require(f["reference_price"] != NULL_I64 and f["imbalance_quantity"] != NULL_U64, "imbalance values")
            require((f["imbalance_side"] == 0) == (f["imbalance_quantity"] == 0), "imbalance side/quantity")
            self.imbalances[key] = f

        elif typ == 17:
            start, end = f["valid_from_ns"], f["valid_to_ns"]
            require(start != NULL_U64 and (end == NULL_U64 or end > start), "symbol map interval")
            interval = (start, None if end == NULL_U64 else end)
            if f["symbology"] != 5:
                name = (pub, f["symbology"], texts["symbol"])
                for old in self.symbol_maps.get(name, []):
                    require(not overlaps(interval, old[:2]), "overlapping symbol intervals")
                self.symbol_maps.setdefault(name, []).append(interval + (inst,))

        elif typ == 18:
            require(f["price"] != NULL_I64 and 0 < f["quantity"] < NULL_U64, "trade-quote price/quantity")
            for side in ("bid", "ask"):
                present_side(f[side + "_price"], f[side + "_quantity"], f[side + "_order_count"])

        elif typ == 19:
            for side in ("bid", "ask"):
                present = present_side(f[side + "_price"], f[side + "_quantity"], f[side + "_order_count"])
                venue = f[side + "_publisher_id"]
                require(present or venue == 0, "an absent side has no venue")
                require(venue == 0 or self.publishers is None or venue in self.publishers, "undeclared venue")
            require(f["interval_ns"] == 0 or f["ts_event"] != NULL_U64, "sampled quote needs ts_event")
            self.best_quotes[key] = f

        elif typ == 20:
            require(pub == channel == inst == 0, "FRAME_SUMMARY scope")
            require(f["ts_event"] == f["ts_recv"] == NULL_U64, "FRAME_SUMMARY timestamps")

        elif typ == 21:
            listed, delisted = f["listing_ns"], f["delisting_ns"]
            require(NULL_U64 in (listed, delisted) or delisted >= listed, "delisting before listing")
            self.securities[(pub, inst)] = f

        elif typ == 22:
            if texts["details"]:
                sorted_json_object(texts["details"])
            self.actions[(pub, texts["unique_id"])] = f

    def finish(self):
        require(not self.working, "unfinished snapshot at END")
        return {
            "definitions": len(self.definitions),
            "trade_ids": len(self.trades),
            "bars": len(self.bars),
            "valid_mbo_books": len(self.mbo),
            "gap_events": len(self.gaps),
        }


def validate(records, publishers=None):
    state = MarketState(publishers)
    for record in records:
        state.apply(record)
    return state.finish()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from nwt_example import read_container

    try:
        path = Path(sys.argv[1])
        require(path.stat().st_size <= 64 * 1024 * 1024, "example file limit")
        print(json.dumps(validate(read_container(path.read_bytes())), indent=2))
    except (ValueError, KeyError, OSError) as error:
        print(f"NWT semantic error: {error}", file=sys.stderr)
        sys.exit(1)
