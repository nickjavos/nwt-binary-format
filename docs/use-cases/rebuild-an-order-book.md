# Rebuild an order book

**Goal.** Replay order-level records into an order book and read the best bid and the best ask at a chosen time.

**Input.** [equity-orders.nwt](files/samples/equity-orders.nwt): 1,818 `MBO` records and 123 `TRADE` records of one equity. [equity-quotes.nwt](files/samples/equity-quotes.nwt) holds the top of book of the same equity and day, and serves as the check. After the `INSTRUMENT_DEF`, the order file starts with an `MBO` record with `action` 4, `CLEAR`, which states that the book is empty. Two `ADD` records follow, `action` 1: an ask (`side` 2) at 186 and a bid (`side` 1) at 176.85:

<!-- nwt-file: fixtures/real-market/equity-orders.jsonl lines=2-4 -->

**Steps.**

1. Save this program as `work/top_of_book.py`. It applies every record up to 08:02:00 UTC to a `MarketState`, the implementation of the state rules in `examples/python/market_state.py`, and then reads the live orders of the book:

   ```python
   import sys
   sys.path[:0] = ["tools", "examples/python"]
   import market_state
   import nwt_example as codec
   import nwt as tool

   at = tool.parse_time("2025-09-16T08:02:00Z")
   key = (2, 0, 11667)                              # publisher, channel, instrument
   state = market_state.MarketState()

   with open("fixtures/real-market/equity-orders.nwt", "rb") as f:
       for record in codec.complete_records(codec.open_reader(f)):
           if int(record["fields"]["ts_event"]) > at:
               break                                # the records of this file are in ts_event order
           state.apply(record)                      # checks the record, then changes the book

   orders = state.mbo[key].values()                 # live orders of the book
   for name, side, best in (("bid", 1, max), ("ask", 2, min)):
       price = best(o["price"] for o in orders if o["side"] == side)
       level = [o for o in orders if o["side"] == side and o["price"] == price]
       quantity = sum(o["quantity"] for o in level)
       print(name, codec.pretty_decimal(price), "quantity", codec.pretty_decimal(quantity), "orders", len(level))
   print("live orders", len(orders))
   ```

   ```bash
   python3 work/top_of_book.py
   ```

   ```text
   bid 177.230000000 quantity 300.000000000 orders 3
   ask 177.290000000 quantity 100.000000000 orders 1
   live orders 1052
   ```

   `apply` raises an error when a record breaks a rule, for example an `ADD` for an order that is already live or a change to a book that has no `CLEAR` or snapshot before it.
2. Check the result against the top-of-book sample. The last `QUOTE` before 08:02:00 UTC in `equity-quotes.nwt` carries the same prices, quantities and order counts:

   ```bash
   python3 tools/nwt.py query fixtures/real-market/equity-quotes.nwt --type QUOTE --to 2025-09-16T08:02:00Z --pretty 2> /dev/null | tail -n 1
   ```

   ```text
   {"type_name":"QUOTE","record_bytes":"96","record_type":"2","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:01:59.372520717Z","ts_recv":"2025-09-16T08:01:59.372683640Z","sequence":"427","bid_price":"177.230000000","ask_price":"177.290000000","bid_quantity":"300.000000000","ask_quantity":"100.000000000","bid_order_count":"3","ask_order_count":"1","quote_flags":"0"}
   ```

**Result.** You have the full order book of the instrument at the chosen time, built from 1,052 live orders, and its top agrees with an independent top-of-book file. A book is valid only when the replay starts at a `CLEAR` or a completed snapshot and applies every record after it: [State and recovery](../STATE-AND-RECOVERY.md#order-level-book-state) gives the rules, and [Gaps and recovery](../STATE-AND-RECOVERY.md#gaps-and-recovery) covers a loss at the source.
