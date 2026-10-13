# Keeping state and recovering from gaps

A consumer that builds order books, quotes or a trade tape applies the records in byte order and keeps state for each publisher, channel and instrument. An order-level book starts as unknown. It becomes valid after an `MBO` `CLEAR` or after a snapshot that runs from `SNAPSHOT_BEGIN` to `SNAPSHOT_END`.

![An order-level book has three states, Unknown, Snapshot open and Valid; the MBO actions move it between them and a GAP returns it to Unknown](../diagrams/order-book-state.svg "States of an order-level book and the MBO actions that move it")

A `GAP` record reports that the producer lost data from the source. It makes the order books, the quotes and the trading status of its publisher and channel unknown. Each of them becomes valid again when its own record arrives. An aggregate book is also valid again after a `BOOK_DELTA` with action `CLEAR` and `side` 0, and an order-level book after an `MBO` `CLEAR`. A damaged or missing frame is a different event: it is a transfer failure, and the reader stops.

![After a GAP record the top of book, the best quote, the aggregate book, the order-level book and the trading status are unknown until QUOTE, BEST_QUOTE, BOOK_SNAPSHOT, a completed snapshot and STATUS restore them](../diagrams/recovery.svg "What a GAP record invalidates and which record restores each state")

[State and recovery](../STATE-AND-RECOVERY.md) · [Specification: Ordering, gaps, snapshots and replay](../specification/ordering-gaps-snapshots-and-replay.md)
