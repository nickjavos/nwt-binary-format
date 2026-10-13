# query

Prints the records that match a filter and reads only the frames that can hold a match.

```bash
python3 tools/nwt.py query FILE [--type TYPES] [--instrument IDS] [--from TIME] [--to TIME] [--pretty]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read, with an `INDEX` |
| `--type`, `--instrument`, `--from`, `--to` | [Filters](run-it.md#filters) |
| `--pretty` | Same as for [cat](cat.md) |

`query` reads the `END` frame, then the `INDEX`, then the `FRAME_SUMMARY` frames at the end of the file. It keeps the `DATA` frames whose time range, type mask and instrument range can hold a match, reads those, and prints the matching records as JSON Lines in file order. The result equals `cat` with the same filter applied. On a file without `FRAME_SUMMARY` records it skips frames by time only.

`query` checks the frames it reads: the frame header, the payload CRC-32C and every record it prints. Run `validate` to check the whole file.

The first line of output goes to standard error. It labels the result as partial: the definitions and the book state before the frames that were read are not part of it.

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type TRADE_QUOTE --from 2025-09-16T08:03:04.5303Z --to 2025-09-16T08:03:04.5304Z --pretty
```

```text
# partial: earlier definitions and book state are not included
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530356100Z","ts_recv":"2025-09-16T08:03:04.530521940Z","sequence":"734","price":"177.290000000","quantity":"78.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530358866Z","ts_recv":"2025-09-16T08:03:04.530522753Z","sequence":"736","price":"177.290000000","quantity":"250.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
```

[Store profile](../STORE.md#how-a-reader-seeks-by-time-and-instrument) describes the read path step by step.
