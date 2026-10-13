# Ordering, gaps, snapshots and replay

## Delivery order

- Byte order is the authoritative delivery order. Frame order and record order are preserved.
- Timestamps can move backward.
- The sequences of channels do not define a total order across channels.
- A merge tool chooses and documents its ordering policy, and it assigns new container and record identities.

## Initial state

A market-data consumer begins with unknown books and unknown status.

- `QUOTE` initializes top-of-book state.
- `BOOK_SNAPSHOT` initializes aggregate state. [`BOOK_DELTA`](../records/BOOK_DELTA.md) then changes it one price level at a time.
- `BEST_QUOTE` and `TRADE_QUOTE` keep their own state and do not replace `QUOTE` state.
- `MBO` state begins with `CLEAR` or a completed snapshot for each book. `ADD` records alone cannot prove that the book is complete.

## MBO snapshot transaction

1. `SNAPSHOT_BEGIN` starts a private, empty working book for the instrument. A nested `SNAPSHOT_BEGIN` is invalid.
2. Until `SNAPSHOT_END`, every `MBO` record for that book is an `ADD`. Order IDs are unique in the working book. Records of other instruments and of other record types can be interleaved.
3. `SNAPSHOT_END` commits the complete working book atomically and marks the `MBO` state valid. An empty snapshot is allowed.
4. A `GAP` for the channel, the end of input or `END` while a snapshot is open aborts it. A completed container with an open snapshot is semantically invalid. A `GAP` discards the working snapshot and marks the book invalid. A stray `SNAPSHOT_END` after that is invalid.

- A snapshot can cross `DATA` frames.
- A reader never exposes the working snapshot as a complete book.
- A configured maximum snapshot size can stop decoding with a resource error. Partial state is never published silently.

## Recovery after a gap

- After a `GAP`, `MBO` changes without `CLEAR` or `SNAPSHOT_BEGIN` cannot restore state. A semantic consumer reports such changes as unavailable for reliable reconstruction.
- A producer sends `CLEAR` or a complete snapshot before it resumes ordinary `MBO` changes.
- A recovery snapshot establishes state at its snapshot point at the source. It does not recover missing trade history.
- The producer reconciles source updates around the snapshot point before it emits the normalized stream.

**Lost frames and lost source data.** The two are different. A missing NWT frame or a missing output sequence is a damaged or incomplete transfer, and strict decoding fails on it. A well-formed `GAP` reports a loss at the source within an intact transfer. A consumer cannot turn damaged bytes into a trusted `GAP` record.

## Deduplication

- For retries that are identical byte for byte, the deduplication keys are `(stream_id, frame_seq)` and `(stream_id, publisher, channel, sequence)`.
- Reuse of an identity with different bytes is an integrity or protocol error.
- Across containers that were generated independently, these keys do not identify the same market event. An application needs an identity specific to the source to deduplicate.
