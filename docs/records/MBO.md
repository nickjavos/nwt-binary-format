# MBO

An `MBO` record (type 4, 88 bytes) is one change to an order-level book: an order added, modified or deleted, the book cleared, or a snapshot marker. A producer emits it for every order event of a market-by-order source. The six actions are `ADD`, `MODIFY`, `DELETE`, `CLEAR`, `SNAPSHOT_BEGIN` and `SNAPSHOT_END`. `quantity` is the quantity that remains in the order, never a delta.

## Fields

<!-- nwt-fields: MBO -->

## Rules

- The identity of a book is `(publisher, channel, instrument)`.
- `ADD` and `MODIFY` require a nonzero order ID, side 1 or 2, a non-null price and a positive non-null quantity.
- `MODIFY` replaces the price, quantity and priority and keeps the side. A change of side is a `DELETE` followed by an `ADD`.
- An order ID is unique among the live orders of a book. It can be reused after `DELETE`.
- `DELETE` requires the ID of an existing order, side 0, a null price, zero quantity and a null priority. It removes the whole order.
- `CLEAR`, `SNAPSHOT_BEGIN` and `SNAPSHOT_END` require order ID 0, side 0, a null price, zero quantity and a null priority.
- `CLEAR` sets the book to a valid empty state.
- A smaller `priority` is earlier in the queue at the same side and price. When non-null values tie, iterate in ascending order ID so that the result is deterministic. That tie-break is a convention of the consumer, not the priority of the exchange.
- When the source does not supply priority, arrival order is not definitive queue priority, and a producer does not present it as such.
- Bids are ordered by descending price and asks by ascending price.
- A `TRADE` record does not change `MBO` state. An execution arrives as `MODIFY` or `DELETE`.
- A `MODIFY` or `DELETE` of an unknown order and an `ADD` of a live order ID are semantic errors. A consumer cannot ignore them silently.
- Snapshot rules are in [`MBO` snapshot transaction](../specification/ordering-gaps-snapshots-and-replay.md#mbo-snapshot-transaction).
- A book is valid only after `CLEAR` or a completed snapshot. `ADD` alone does not prove a complete book.
- A snapshot is built privately between `SNAPSHOT_BEGIN` and `SNAPSHOT_END` and can cross `DATA` frames. Only `SNAPSHOT_END` commits it.

[State and recovery](../STATE-AND-RECOVERY.md) shows the book states and what a `GAP` does to them.

## Example

<!-- nwt-example: 4 -->

## Write and decode

`record 4` writes the `mbo-clear` vector (88 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 4 work/type-4-python.bin
python3 examples/python/nwt_example.py decode-record work/type-4-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 4 work/type-4-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-4-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 4 work/type-4-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-4-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 4 work/type-4-cpp.bin
work/nwt-cpp decode-record work/type-4-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `mbo-clear` | `fixtures/records/012-mbo-clear.bin` | `CLEAR`: declares a valid empty book. |
| `mbo-add` | `fixtures/records/013-mbo-add.bin` | `ADD` of bid order 101 with a known priority. |
| `mbo-modify` | `fixtures/records/014-mbo-modify.bin` | `MODIFY` of order 101: new price, remaining quantity and priority, same side. |
| `mbo-delete` | `fixtures/records/015-mbo-delete.bin` | `DELETE` of order 101: null price, quantity 0, null priority, side 0. |
| `mbo-snapshot-begin` | `fixtures/records/016-mbo-snapshot-begin.bin` | `SNAPSHOT_BEGIN`: opens a snapshot that replaces the book. |
| `mbo-snapshot-bid` | `fixtures/records/017-mbo-snapshot-bid.bin` | `ADD` of a bid order inside the snapshot. |
| `mbo-snapshot-ask` | `fixtures/records/018-mbo-snapshot-ask.bin` | `ADD` of an ask order inside the snapshot, with an unknown priority (`UINT64_MAX`). |
| `mbo-snapshot-end` | `fixtures/records/019-mbo-snapshot-end.bin` | `SNAPSHOT_END`: commits the snapshot. In the container that `write` produces, this snapshot crosses a `DATA` frame boundary. |
| `mbo-recovery-begin` | `fixtures/records/035-mbo-recovery-begin.bin` | `SNAPSHOT_BEGIN` of the snapshot sent after the `GAP` vectors. |
| `mbo-recovery-add` | `fixtures/records/036-mbo-recovery-add.bin` | The single order of the recovery snapshot. |
| `mbo-recovery-end` | `fixtures/records/037-mbo-recovery-end.bin` | `SNAPSHOT_END` of the recovery snapshot. The book is valid again. |
| `mbo-clear` | `fixtures/golden/records/025-mbo-clear.bin` | The `MBO` `CLEAR` of the conformance file. |
| `mbo-add` | `fixtures/golden/records/026-mbo-add.bin` | The `MBO` `ADD` of the conformance file: one bid order. |
