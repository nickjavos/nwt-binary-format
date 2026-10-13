# Worked sequence

The conformance file [all-records.nwt](files/samples/all-records.nwt) holds 47 records in frames of 3. Publisher 1, channel 0 carries sequences 1–46.

| `sequence` | Records | State after |
|---|---|---|
| 1–2 | `INSTRUMENT_DEF` for instruments 2001 and 2002 | Two instruments are defined: an equity and an option. |
| 3–14 | 3 `VENUE_DEF`, 4 `LISTING`, 2 `OPTION_DEF`, 3 `SYMBOL_MAP` | Reference records are stored by key. No order book exists yet. |
| 15 | `TRADE` `NEW`, `trade_id` 1, 149.25 and 100 | Trade 1 is active. |
| 16–18 | `QUOTE` 149.24 bid, 149.26 ask; `BAR`; `STATUS` open | Top of book, one bar interval and the trading status are known. |
| 19 | `BOOK_SNAPSHOT` with 2 levels | The aggregate book is valid: bids 149.24 and 149.23, asks 149.26 and 149.27. |
| 20 | `BOOK_DELTA` `SET`, bid 149.25, quantity 100 | Bids are 149.25, 149.24 and 149.23. |
| 21 | `BOOK_DELTA` `SET`, ask 149.26, quantity 250, `LAST_IN_EVENT` | The ask at 149.26 has quantity 250. The event that began with sequence 20 is complete. |
| 22 | `BOOK_DELTA` `DELETE`, bid 149.23 | Bids are 149.25 and 149.24. |
| 23 | `BOOK_DELTA` `CLEAR`, `side` 2 | The ask side is empty. |
| 24 | `BOOK_DELTA` `CLEAR`, `side` 0 | The whole book is empty and still valid. |
| 25–26 | `MBO` `CLEAR`; `MBO` `ADD` order 9001, bid 149.24, quantity 100 | The order-level book is valid with one live order. |
| 27–30 | `STATISTICS` `SET`: open, settlement and volume of 2001, open interest of 2002 | Four statistics are stored. |
| 31 | `STATISTICS` `DELETE` of the settlement | Three statistics remain. |
| 32–40 | 3 `OPTION_ANALYTICS`, 2 `IMBALANCE`, 2 `TRADE_QUOTE`, 2 `BEST_QUOTE` | The latest analytics, imbalance and best quote are stored. |
| 41 | `GAP`, reason 1, source sequences 500–509, `recovery_id` 1 | Top of book, best quote, trading status, the aggregate book and the order-level book of the channel are unknown. Definitions, trade 1, statistics and reference records stay. |
| 42–46 | 2 `SECURITY_DEF`, 3 `CORPORATE_ACTION` | Reference records are stored by key. |

The record between sequences 41 and 42 in file order is a `SYSTEM` heartbeat with publisher 0 and channel 0. It has `sequence` 1, because it belongs to the scope of the container and not to publisher 1.

The gap record, as [cat](../tools/cat.md) prints it:

```bash
python3 tools/nwt.py cat fixtures/golden/all-records.nwt --pretty | sed -n 41p
```

```text
{"type_name":"GAP","record_bytes":"80","record_type":"8","schema_version":"1","flags":"0","publisher_id":"1","channel_id":"0","instrument_id":"0","ts_event":"2025-10-09T08:54:21.000001000Z","ts_recv":"2025-10-09T08:54:21.000001100Z","sequence":"41","first_missing_source_sequence":"500","last_missing_source_sequence":"509","reason":"1","recovery_id":"1"}
```

No record after sequence 41 restores an order book, so the file ends with the order books of the channel unknown.

The container that the reference codecs write with `write` shows an order-level snapshot and a recovery. It holds 49 records of publisher 1, channel 0, in frames of 3.

| `sequence` | Records | State after |
|---|---|---|
| 12 | `MBO` `CLEAR` | The order-level book is valid and empty. |
| 13–15 | `ADD` order 101, bid 123.00; `MODIFY` to 123.50; `DELETE` | The book holds order 101, then its new price, then no order. |
| 16–18 | `SNAPSHOT_BEGIN`; `ADD` order 201, bid 123.00; `ADD` order 202, ask 124.00 | A working book holds two orders. The committed book is still the empty one. These three records fill one frame. |
| 19 | `SNAPSHOT_END`, in the next frame | The working book is committed: orders 201 and 202 are live. |
| 20–22 | 3 `BOOK_SNAPSHOT`: two levels, no level, one level with the depth-limited flag | The aggregate book is replaced three times. |
| 23–28 | 6 `STATUS` | The trading status is replaced six times. |
| 29–32 | 4 `GAP`, reasons 1–4, `recovery_id` 1–4 | From sequence 29 the order-level book, the aggregate book, the top of book and the trading status are unknown. |
| 33 | `QUOTE` | The top of book is valid again. |
| 34 | `BOOK_SNAPSHOT` | The aggregate book is valid again. |
| 35–37 | `SNAPSHOT_BEGIN`; `ADD` order 301; `SNAPSHOT_END`, across two frames | The order-level book is valid again with order 301. |
| 38 | `STATUS` | The trading status is valid again. |
| 39–42 | `SYSTEM` heartbeat, info, warning and error | No state changes. Sequences 40–42 name `recovery_id` 4 in `related_recovery_id`. |

The frame that ends with sequence 18 passes every check and is committed while the snapshot is open. The new book becomes visible only with sequence 19.
