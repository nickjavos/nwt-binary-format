# Order-level book state

An `MBO` record changes the order-level book of one publisher, channel and instrument. The book holds live orders by order ID and is in one of three states.

![An order-level book has three states, Unknown, Snapshot open and Valid; the MBO actions move it between them and a GAP returns it to Unknown](../diagrams/order-book-state.svg "States of an order-level book and the MBO actions that move it")

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

The Specification defines these rules in [MBO](../records/MBO.md) and [MBO snapshot transaction](../specification/ordering-gaps-snapshots-and-replay.md#mbo-snapshot-transaction).
