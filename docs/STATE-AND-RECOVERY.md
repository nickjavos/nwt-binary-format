# State and recovery

This page describes the state a consumer keeps while it reads NWT market data, and how it restores that state after a loss. It is for engineers who build order books, trade tapes or reference stores from NWT records. The rules come from the [Specification](specification/ordering-gaps-snapshots-and-replay.md); their reference implementation is `examples/python/market_state.py`.

## State a consumer keeps

A consumer starts with no state: every order book, quote and trading status is unknown. Each record then creates, replaces or ends one piece of state. The key is the set of fields that identifies that piece.

![Market records, INSTRUMENT_DEF, OPTION_DEF, SYMBOL_MAP, CORPORATE_ACTION, SECURITY_DEF and LISTING attach to one key, publisher_id with instrument_id; VENUE_DEF is keyed by mic](diagrams/data-model-keys.svg "The keys that join the records of one instrument")

| Record type | State | Key | Replaced or ended by |
|---|---|---|---|
| `INSTRUMENT_DEF` | Definition of an instrument: identity and units | Publisher, instrument | A later definition with the same key. Its currency and quantity unit stay the same. |
| `TRADE` | Lifecycle of one trade | Publisher, channel, instrument, `trade_id` | `CORRECT` replaces the values; `CANCEL` ends the trade. |
| `QUOTE` | Top of book | Publisher, channel, instrument | The next `QUOTE`; `GAP` invalidates it. |
| `BAR` | Set of completed bar intervals | Publisher, channel, instrument, interval | Nothing. A second bar for the same interval is an error. |
| `MBO` | Order-level book | Publisher, channel, instrument | `CLEAR` or a completed snapshot; `GAP` invalidates it. |
| `BOOK_SNAPSHOT`, `BOOK_DELTA` | Aggregate book: price levels on each side | Publisher, channel, instrument | The next `BOOK_SNAPSHOT`; `GAP` invalidates it. |
| `STATUS` | Trading status | Publisher, channel, instrument | The next `STATUS`; `GAP` invalidates it. |
| `GAP` | Recovery IDs seen so far | Container | The end of the container. |
| `VENUE_DEF` | Venue | Publisher, `mic` | A later record with the same key. |
| `OPTION_DEF` | Terms of an option contract | Publisher, instrument | A later record with the same key. |
| `LISTING` | Listing of an instrument | Publisher, instrument | A later record with the same key. |
| `STATISTICS` | Latest value of one statistic | Publisher, channel, instrument, `stat_type`, `ts_ref` | The next `SET`; `DELETE` withdraws it. |
| `OPTION_ANALYTICS` | Latest analytics of an option | Publisher, channel, instrument | The next record. |
| `IMBALANCE` | Latest auction imbalance | Publisher, channel, instrument | The next record. |
| `SYMBOL_MAP` | Validity intervals of a symbol | Publisher, `symbology`, symbol | Nothing. Intervals of one symbol do not overlap. |
| `BEST_QUOTE` | Best quote, separate from the `QUOTE` state | Publisher, channel, instrument | The next `BEST_QUOTE`; `GAP` invalidates it. |
| `SECURITY_DEF` | Security master record | Publisher, instrument | A later record with the same key. |
| `CORPORATE_ACTION` | Corporate action | Publisher, `unique_id` | A later record with the same key. |

`SYSTEM`, `TRADE_QUOTE` and `FRAME_SUMMARY` carry no state. A `TRADE_QUOTE` is a trade print together with the quote at that moment; it changes neither the trade lifecycle nor the `QUOTE` state.

A market record needs an `INSTRUMENT_DEF` for its publisher and instrument earlier in the container. The market record types are `TRADE`, `QUOTE`, `BAR`, `MBO`, `BOOK_SNAPSHOT`, `STATUS`, `STATISTICS`, `OPTION_ANALYTICS`, `BOOK_DELTA`, `IMBALANCE`, `TRADE_QUOTE` and `BEST_QUOTE`. The layouts and field rules of every type are in the [Specification](specification/record-types.md).

## Sequence numbers and ordering

NWT has three counters. They measure different things and are never substituted for one another.

| Counter | Carried in | Counts | A hole means |
|---|---|---|---|
| `frame_seq` | Frame header | Frames of the container, from 0 | A transfer failure |
| `sequence` | Record header | Records of one publisher and channel in the container, from 1, across instruments and record types | A transfer failure |
| `first_missing_source_sequence`, `last_missing_source_sequence` | `GAP` record | Messages of the source feed, in the numbering of the source | A source failure that the producer reports |

- **The order of the bytes is the delivery order.** A consumer applies records in the order of the bytes. Timestamps can move backward, and the sequences of two channels do not define an order between the channels.
- **`sequence` is an output position, not an exchange sequence number.** The scope with publisher 0 and channel 0 belongs to the container: `SYSTEM` records of the container and `FRAME_SUMMARY` records count there.
- **A new container restarts the sequences.** A filtered, merged or re-framed export is a new container with a new stream ID and its own sequences from 1. Its sequences have no holes, so a hole never stands for a source gap.
- **Retries are deduplicated by identity.** For a retry that is identical byte for byte, the keys are stream ID with `frame_seq`, and stream ID with publisher, channel and `sequence`. The same identity with different bytes is an error.

The rules are in [Record header](specification/record-header.md), [Delivery order](specification/ordering-gaps-snapshots-and-replay.md#delivery-order) and [Deduplication](specification/ordering-gaps-snapshots-and-replay.md#deduplication) of the Specification.

## Order-level book state

An `MBO` record changes the order-level book of one publisher, channel and instrument. The book holds live orders by order ID and is in one of three states.

![An order-level book has three states, Unknown, Snapshot open and Valid; the MBO actions move it between them and a GAP returns it to Unknown](diagrams/order-book-state.svg "States of an order-level book and the MBO actions that move it")

| State | Meaning |
|---|---|
| Unknown | The consumer cannot tell which orders are live. This is the state at the start of a container and after a `GAP`. |
| Valid | The committed book equals the book of the source. It can be empty. |
| Snapshot open | A private working book is being filled between `SNAPSHOT_BEGIN` and `SNAPSHOT_END`. A book that was valid before stays visible, with its age, until the snapshot commits. |

Each event moves the book from one state to the next. A combination that the table does not list is an error.

| State | Event | Next state | Effect |
|---|---|---|---|
| Unknown | `CLEAR` | Valid | Starts an empty book. |
| Unknown | `SNAPSHOT_BEGIN` | Snapshot open | Starts an empty working book. |
| Valid | `ADD` | Valid | Adds the order under an order ID that is not live in the book. |
| Valid | `MODIFY` | Valid | Replaces the price, quantity and priority of a live order. The side stays the same. |
| Valid | `DELETE` | Valid | Removes a live order. |
| Valid | `CLEAR` | Valid | Empties the book. |
| Valid | `SNAPSHOT_BEGIN` | Snapshot open | Starts an empty working book beside the committed book. |
| Snapshot open | `ADD` | Snapshot open | Adds the order to the working book. |
| Snapshot open | `SNAPSHOT_END` | Valid | Replaces the committed book with the working book in one step. |
| Any | `GAP` on the channel | Unknown | Discards the committed book and the working book. |

The quantity of `ADD` and `MODIFY` is the remaining size of the order, not a change. A `TRADE` record does not change the book: an execution arrives as `MODIFY` or `DELETE`.

A snapshot is a transaction:

1. `SNAPSHOT_BEGIN` starts a private, empty working book for the instrument.
2. Until `SNAPSHOT_END`, every `MBO` record for that book is an `ADD`. Records of other instruments and of other record types can come in between.
3. `SNAPSHOT_END` commits the working book. An empty snapshot is valid.
4. A snapshot can span several `DATA` frames. The consumer does not show the working book as a complete book, however many frames it has committed.

These inputs are errors. The table gives the message of the reference implementation for each.

| Input | Message |
|---|---|
| `ADD`, `MODIFY` or `DELETE` on an unknown book | `MBO is not initialized or needs recovery` |
| `ADD` with an order ID that is live | `duplicate live order` |
| `MODIFY` or `DELETE` of an order that is not in the book | `unknown order` |
| `MODIFY` that changes bid to ask or ask to bid | `modify cannot change side` |
| `MODIFY`, `DELETE`, `CLEAR` or a second `SNAPSHOT_BEGIN` while a snapshot is open | `only ADD/END allowed during snapshot` |
| `SNAPSHOT_END` without `SNAPSHOT_BEGIN` | `snapshot end without begin` |
| `END` of the container while a snapshot is open | `unfinished snapshot at END` |

`CLEAR` is a statement of the producer that the book of the source is empty. A consumer does not use it to repair a book it has lost.

The transitions in the reference implementation:

<!-- nwt-file: examples/python/market_state.py lines=179-231 -->

The Specification defines these rules in [MBO](records/MBO.md) and [MBO snapshot transaction](specification/ordering-gaps-snapshots-and-replay.md#mbo-snapshot-transaction).

## Aggregate book with snapshots and deltas

The aggregate book holds price levels, not orders: for each side, a quantity and an order count per price. `BOOK_SNAPSHOT` and `BOOK_DELTA` work on the same book.

- `BOOK_SNAPSHOT` replaces the whole book with at most 1,024 levels per side. It is complete in one record. A snapshot with 0 levels is an empty book.
- `BOOK_DELTA` changes one price level, or clears a side. Levels are keyed by price, not by rank.
- The book is valid after a `BOOK_SNAPSHOT`, or after a `BOOK_DELTA` with action `CLEAR` and `side` 0. A `GAP` on the channel invalidates it. Any other delta on a book that is not valid is the error `BOOK_DELTA needs a valid book`.

| Action | Fields | Effect |
|---|---|---|
| `SET` | Non-null price, quantity above 0, `side` 1 or 2 | Adds the level, or replaces its quantity and order count. |
| `DELETE` | Non-null price, quantity 0, null order count | Removes the level. The level is in the book, unless the book is depth-limited. |
| `CLEAR` | Null price, quantity 0, null order count | Empties one side, or the whole book when `side` is 0. |

- The flag `LAST_IN_EVENT` in `delta_flags` marks the last delta of one event of the source. A consumer that publishes the book to others does so after that delta.
- A snapshot with the depth-limited flag in `book_flags` reports the top ranks only. The book stays depth-limited until the next snapshot without the flag, and a `DELETE` for a price that the book does not hold is valid in that time.
- A side never holds more than 1,024 levels, so the book can always be sent again as one `BOOK_SNAPSHOT`.
- A book whose best bid is above its best ask is not an error.
- A `BOOK_SNAPSHOT` does not restore the order-level book, and an `MBO` record does not change the aggregate book.

The delta rules in the reference implementation:

<!-- nwt-file: examples/python/market_state.py lines=340-364 -->

The Specification defines these rules in [BOOK_SNAPSHOT](records/BOOK_SNAPSHOT.md) and [BOOK_DELTA](records/BOOK_DELTA.md).

## Quotes and trading status

- `QUOTE` replaces the top of book of its instrument. A side is absent when its price is null; then its quantity and order count are 0. A present side has a quantity above 0.
- `BEST_QUOTE` keeps a state of its own. It names the publisher of each side in `bid_publisher_id` and `ask_publisher_id`, and it does not replace the `QUOTE` state.
- `STATUS` replaces the trading status of its instrument. It does not clear an order book.
- `OPTION_ANALYTICS` and `IMBALANCE` replace the latest record of their instrument.

A `GAP` on the channel invalidates the top of book, the best quote and the trading status of every instrument of that publisher and channel. Each is valid again when its next record arrives.

## Trades and corrections

A trade is identified by `trade_id` within its publisher, channel and instrument. Its lifecycle is `NEW`, then any number of `CORRECT`, then at most one `CANCEL`.

| Action | Fields | Effect |
|---|---|---|
| `NEW` | Non-null price, quantity above 0, `original_sequence` 0 | Starts the trade under a `trade_id` that is not in use. |
| `CORRECT` | Full replacement price, quantity, aggressor and conditions | Replaces the values of the trade. |
| `CANCEL` | Null price, null quantity, aggressor 0, conditions 0 | Ends the trade. A later `CORRECT` or `CANCEL` for it is an error. |

`CORRECT` and `CANCEL` carry the `trade_id` of the trade and, in `original_sequence`, the `sequence` of its `NEW` record. They never point at an earlier correction.

The first trade of the container that the reference codecs write with `write` goes through the whole lifecycle; the second has a negative price:

| `sequence` | Action | `trade_id` | `original_sequence` | Price and quantity |
|---|---|---|---|---|
| 2 | `NEW` | 42 | 0 | 123.45 and 10 |
| 3 | `CORRECT` | 42 | 2 | 123.46 and 12 |
| 4 | `CANCEL` | 42 | 2 | Null and null |
| 5 | `NEW` | 43 | 0 | −1.25 and 0.5 |

After sequence 4 the consumer holds trade 42 as canceled, with its history, and after sequence 5 trade 43 as active.

All records of a lifecycle are in the same container and the same channel. An export that contains a correction also contains the `NEW` record and the corrections before it, even when they lie outside the requested time range. The Specification defines these rules in [TRADE](records/TRADE.md).

## Reference data and statistics

Reference records describe venues, instruments, symbols and corporate events. The reference record types are `VENUE_DEF`, `OPTION_DEF`, `LISTING`, `SYMBOL_MAP`, `SECURITY_DEF` and `CORPORATE_ACTION`.

- A reference record needs no `INSTRUMENT_DEF` before it, and it does not replace one.
- A later record with the same key replaces the earlier one. The keys are in the table of [State a consumer keeps](#state-a-consumer-keeps).
- `OPTION_DEF` and `INSTRUMENT_DEF` for the same instrument agree: the asset class of the definition is option, and expiration, strike and underlying instrument are equal. The check runs whichever record comes first.
- `SYMBOL_MAP` gives a half-open interval, from `valid_from_ns` up to but not including `valid_to_ns`, in which a symbol names an instrument. Two intervals of the same publisher, symbology and symbol do not overlap. Root symbols, symbology 5, are exempt: one root names many instruments at a time.
- The `details` text of a `CORPORATE_ACTION`, when it is not empty, is one JSON object with sorted keys and no duplicate key.
- A `GAP` does not invalidate reference data.

A statistic is a reference value of a session, not a trade. `ts_ref` names the session or the date it belongs to.

- `SET` gives the value. Price statistics (open, high, low, close, settlement, VWAP) carry a price and a null quantity. Quantity statistics (volume, open interest) carry a quantity and a null price.
- `DELETE` withdraws the value. Its price and its quantity are null.
- A consumer that keeps the latest `SET` per key and removes the key on `DELETE` holds the current statistics.

## Gaps and recovery

### Transfer failure versus source failure

A transfer failure and a source failure are different events, and a consumer handles them differently.

| Event | What the consumer sees | What it means |
|---|---|---|
| Transfer failure | A header or payload CRC-32C that does not match, a `frame_seq` or `sequence` out of step, or the end of input before `END` | Bytes of the container are damaged or missing. Nothing after the last verified frame is trusted. |
| Source failure | A `GAP` record in a frame that passes every check | The transfer is intact. The producer lost data of the source feed and says so. |

A consumer never turns damaged bytes into a `GAP` of its own. Only the producer writes `GAP` records.

### Recovery after a source gap

A `GAP` record has a non-zero publisher and instrument 0. It applies to every instrument of its publisher and channel.

![After a GAP record the top of book, the best quote, the aggregate book, the order-level book and the trading status are unknown until QUOTE, BEST_QUOTE, BOOK_SNAPSHOT, a completed snapshot and STATUS restore them](diagrams/recovery.svg "What a GAP record invalidates and which record restores each state")

1. Record the `recovery_id` and the reason. The two source sequence fields are both null or both set; when set, they name the first and the last missing message of the source.
2. Discard the state of the channel that a gap invalidates: order-level books with any open snapshot, aggregate books, top of book, best quote and trading status.
3. Keep the state that a gap does not touch: definitions, reference data, statistics and the trade lifecycles.
4. Mark trades and bars of the affected interval as possibly incomplete. This mark stays after the order books are valid again.
5. Restore each piece of state when its own record arrives. The pieces recover independently; the table below names the record that restores each one.
6. Until an order book is valid again, treat `MBO` changes and `BOOK_DELTA` records for it as errors. An `ADD` after a gap does not prove that the order-level book is complete.
7. Use `related_recovery_id` of later `SYSTEM` records to match diagnostics to the gap.

| State | Valid again after |
|---|---|
| Order-level book | `MBO` `CLEAR`, or a snapshot from `SNAPSHOT_BEGIN` to `SNAPSHOT_END` |
| Aggregate book | `BOOK_SNAPSHOT`, or `BOOK_DELTA` `CLEAR` with `side` 0 |
| Top of book | `QUOTE` |
| Best quote | `BEST_QUOTE` |
| Trading status | `STATUS` |

A recovery snapshot gives the order book at the snapshot point of the source. It does not bring back the trades that were lost, and it does not complete the bars of the interval. The Specification defines these rules in [GAP](records/GAP.md) and [Recovery after a gap](specification/ordering-gaps-snapshots-and-replay.md#recovery-after-a-gap).

### Recovery after a transfer failure

1. Stop decoding at the first frame that fails a check. Do not apply any record of that frame.
2. Keep the position after the last frame that passed every check: its byte offset and its `frame_seq`.
3. Fetch the bytes again from that frame boundary, from the same immutable container: the same stream ID, with header and metadata verified. The bytes and the sequences are the same as in the first transfer.
4. Continue applying records from that frame. Skip a frame you have already applied by its stream ID and `frame_seq`.

A file without `END` is incomplete even when it stops exactly at a frame boundary. A container whose `END` reports the status aborted is complete as a transfer and unfinished as a data set: the producer stopped early. The Specification covers this in [Resume and byte ranges](specification/transport-and-recovery.md#resume-and-byte-ranges).

## Selective reads, summaries and state

A reader that uses `INDEX` frames and `FRAME_SUMMARY` records to read only some frames also skips the state that the other frames build. Such a read is correct for questions that need no earlier state, and incomplete for questions that do.

| Question | Frames it needs |
|---|---|
| Trades or quotes of one instrument in a time range, as raw records | The frames that can hold a match |
| Units and identity of those records | Also the frames with the `INSTRUMENT_DEF` records |
| The order-level book at a time | Every frame from the last `CLEAR` or completed snapshot of the book, in file order |
| The aggregate book at a time | Every frame from the last `BOOK_SNAPSHOT` of the book, in file order |
| The current statistic, listing or security record | Every frame that can hold a record with that key |

A store file changes which frames are cheap to find. It does not change the rules of replay: the result of a selective read is labelled partial and is not presented as a reconstructed order book. The [Store profile](STORE.md#what-a-partial-read-returns) describes what such a read returns.

## Application transaction boundary

A frame is the unit of integrity, and a consumer makes it the unit of commitment.

1. Verify the whole frame first: the header CRC-32C, the payload CRC-32C and the structure of every record.
2. Apply the records of the frame to a staged copy of the state.
3. Commit the staged state only when every record of the frame passes its rules. Otherwise discard it.
4. Keep an open snapshot private across commits. It becomes visible with `SNAPSHOT_END`, which can arrive several frames later.
5. Store the committed NWT position, stream ID and `frame_seq`, in the same transaction as the application state it produced.

A position alone does not make side effects happen exactly once. The position and the effects are committed together, or the effects are made safe to repeat.

`MarketState.apply` in the reference implementation changes its state while it checks a record. When it raises an error, discard that `MarketState` instance and rebuild the state from a verified position.

## Worked sequence

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

The gap record, as [cat](tools/cat.md) prints it:

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

## Run the state rules

`examples/python/market_state.py` reads a container, applies every record to a `MarketState` and prints a summary of the final state:

```bash
python3 examples/python/market_state.py fixtures/golden/all-records.nwt
```

```text
{
  "definitions": 2,
  "trade_ids": 1,
  "bars": 1,
  "valid_mbo_books": 0,
  "gap_events": 1
}
```

For the container of the second table:

```bash
python3 examples/python/nwt_example.py write work/types-1-9.nwt
python3 examples/python/market_state.py work/types-1-9.nwt
```

```text
{
  "definitions": 8,
  "trade_ids": 2,
  "bars": 2,
  "valid_mbo_books": 1,
  "gap_events": 4
}
```

[validate](tools/validate.md) runs the same rules on any container and names the record that breaks one. A container that holds order records without the definition of their instrument fails on its first record:

```bash
python3 tools/nwt.py extract fixtures/real-market/equity-orders.nwt work/orders-only.nwt --type MBO
python3 tools/nwt.py validate work/orders-only.nwt
```

```text
NWT error: record 1 (MBO, sequence 1): definition must precede data
```

From Python, pass decoded records to `market_state.validate`, or call `MarketState.apply` for each record and `MarketState.finish` at the end of the container:

```python
import sys
sys.path.insert(0, "examples/python")
import market_state
import nwt_example as nwt

with open("fixtures/golden/all-records.nwt", "rb") as f:
    reader = nwt.open_reader(f)
    publishers = {p["id"] for p in reader.manifest["publishers"]}
    state = market_state.MarketState(publishers)
    for record in nwt.complete_records(reader):
        state.apply(record)             # raises ValueError with the name of the broken rule
    print(state.finish())               # also checks that no snapshot is open
```

```text
{'definitions': 2, 'trade_ids': 1, 'bars': 1, 'valid_mbo_books': 0, 'gap_events': 1}
```
