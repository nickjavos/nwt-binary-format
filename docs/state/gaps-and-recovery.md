# Gaps and recovery

## Transfer failure versus source failure

A transfer failure and a source failure are different events, and a consumer handles them differently.

| Event | What the consumer sees | What it means |
|---|---|---|
| Transfer failure | A header or payload CRC-32C that does not match, a `frame_seq` or `sequence` out of step, or the end of input before `END` | Bytes of the container are damaged or missing. Nothing after the last verified frame is trusted. |
| Source failure | A `GAP` record in a frame that passes every check | The transfer is intact. The producer lost data of the source feed and says so. |

A consumer never turns damaged bytes into a `GAP` of its own. Only the producer writes `GAP` records.

## Recovery after a source gap

A `GAP` record has a non-zero publisher and instrument 0. It applies to every instrument of its publisher and channel.

![After a GAP record the top of book, the best quote, the aggregate book, the order-level book and the trading status are unknown until QUOTE, BEST_QUOTE, BOOK_SNAPSHOT, a completed snapshot and STATUS restore them](../diagrams/recovery.svg "What a GAP record invalidates and which record restores each state")

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

A recovery snapshot gives the order book at the snapshot point of the source. It does not bring back the trades that were lost, and it does not complete the bars of the interval. The Specification defines these rules in [GAP](../records/GAP.md) and [Recovery after a gap](../specification/ordering-gaps-snapshots-and-replay.md#recovery-after-a-gap).

## Recovery after a transfer failure

1. Stop decoding at the first frame that fails a check. Do not apply any record of that frame.
2. Keep the position after the last frame that passed every check: its byte offset and its `frame_seq`.
3. Fetch the bytes again from that frame boundary, from the same immutable container: the same stream ID, with header and metadata verified. The bytes and the sequences are the same as in the first transfer.
4. Continue applying records from that frame. Skip a frame you have already applied by its stream ID and `frame_seq`.

A file without `END` is incomplete even when it stops exactly at a frame boundary. A container whose `END` reports the status aborted is complete as a transfer and unfinished as a data set: the producer stopped early. The Specification covers this in [Resume and byte ranges](../specification/transport-and-recovery.md#resume-and-byte-ranges).
