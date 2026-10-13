# Store profile

A store file is a normal container written with the choices below. There is no separate store format. The [Store profile](../STORE.md) document describes the tools that write and query store files.

| Choice | Setting | Reason |
|---|---|---|
| Frame size | 1,048,576 raw bytes by default, up to 16,777,216 | Fewer headers and better compression |
| Codec | Zstandard, with codec 0 for a frame that does not shrink | File size and read speed |
| `INDEX` | Always written | Seek by time |
| `FRAME_SUMMARY` | Always written | Skip frames by record type and instrument without reading them |
| `ordering` | Declared in the manifest when it holds | Makes binary search by time valid |

- Records are never reordered. Byte order is the delivery order, and definitions, snapshots and trade lifecycles depend on it.
- A tool that re-frames or recompresses a file keeps the record order and gives the new file a new stream ID.
- Such a tool declares an `ordering` only when the input already has it.

To answer a query from a store file, a reader takes these steps:

1. Read the last 96 bytes, the `END` frame, and validate it.
2. Read the `INDEX` frames that `END` points to.
3. Read the summary frames, found as described in [`FRAME_SUMMARY`](../records/FRAME_SUMMARY.md).
4. Choose frames by time range, type mask and instrument range.
5. Read only the chosen frames, in their original order.

The reader needs one primitive: read N bytes at offset X. The same code therefore works on a local file, on object storage with range requests and on any other source with that primitive.

The result of such a read is partial in the sense of [`INDEX` frames](frames.md#index-frames): earlier definitions and book state can be missing, and the reader labels the result accordingly.
