# cat

Prints every record of a container as one JSON object per line.

```bash
python3 tools/nwt.py cat FILE [--pretty]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `--pretty` | Prints prices and quantities as decimals with nine fractional digits, times as `YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ`, and null values as JSON `null` |

An object starts with `type_name`, then the header fields, the body fields and the texts, in schema order. Without `--pretty`, every value is the stored integer as a decimal string. A `BOOK_SNAPSHOT` has a `levels` array. Reserved fields are left out.

`cat` prints the records of a frame after that frame has passed its checks. When a later frame is damaged, the records before it are already printed and the command exits with status 1, so rely on the exit status, not on the amount of output. When the program at the other end of a pipe closes it early, as `head` does, `cat` stops with status 0.

```bash
python3 tools/nwt.py cat fixtures/real-market/equity-quotes.nwt --pretty | head -n 2
```

```text
{"type_name":"INSTRUMENT_DEF","record_bytes":"128","record_type":"6","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T07:05:06.677514564Z","ts_recv":"2025-09-16T07:05:06.677677658Z","sequence":"1","price_increment":null,"quantity_increment":null,"contract_multiplier":null,"expiration_ns":null,"underlying_instrument_id":"0","strike":null,"asset_class":"1","symbol_bytes":"4","venue_bytes":"4","currency_bytes":"3","quantity_unit_bytes":"5","symbol":"NVDA","venue":"XNAS","currency":"USD","quantity_unit":"share"}
{"type_name":"QUOTE","record_bytes":"96","record_type":"2","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:00:00.015298471Z","ts_recv":"2025-09-16T08:00:00.015462508Z","sequence":"2","bid_price":null,"ask_price":"186.000000000","bid_quantity":"0.000000000","ask_quantity":"100.000000000","bid_order_count":"0","ask_order_count":"1","quote_flags":"0"}
```
