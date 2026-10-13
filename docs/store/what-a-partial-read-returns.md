# What a partial read returns

A selective read returns the matching records of the frames it read, and nothing of the frames it skipped. The instrument definitions, the snapshots and the trade history before the first frame it read are not part of the result. Such a result is raw and partial: it is not a reconstructed book, and a reader labels it so.

[query](../tools/query.md) writes this label on standard error before the first record:

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type TRADE_QUOTE --from 2025-09-16T08:03:04.5303Z --to 2025-09-16T08:03:04.5304Z --pretty
```

```text
# partial: earlier definitions and book state are not included
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530356100Z","ts_recv":"2025-09-16T08:03:04.530521940Z","sequence":"734","price":"177.290000000","quantity":"78.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530358866Z","ts_recv":"2025-09-16T08:03:04.530522753Z","sequence":"736","price":"177.290000000","quantity":"250.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
```

The sequences 734 and 736 are those of the file. The record with sequence 735 is a `QUOTE`, so it is not part of this selection.

To turn a selection into data you can interpret:

1. Read the definitions too. `--type INSTRUMENT_DEF` returns them, and their frames are found through the type mask.
2. For a book, read every frame from the last snapshot of that book, in file order, and replay the records. [State and recovery](../state/selective-reads-summaries-and-state.md) lists the frames each question needs.
3. For a file you hand to someone else, use [extract](../tools/extract.md). It reads the whole input and writes a new container with its own stream ID and sequences.
