# Frames

Everything after the metadata is a sequence of frames. A frame is a 64-byte header, a payload and zero padding to an 8-byte boundary. The header states the kind of the frame, the codec and the size of the payload, and it carries the checksums.

![A frame is a 64-byte header, a payload and zero padding; the payload is stored raw or as one Zstandard frame, and the raw payload is a run of whole records covered by a CRC-32C](../diagrams/frame-anatomy.svg "A frame: header, payload and padding, and what each CRC-32C covers")

## Frame header

Every frame begins with this 64-byte header.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `magic` | bytes | 4 | `4e 57 46 31`, the ASCII text `NWF1` |
| 4 | `envelope_version` | u8 | 1 | 1 |
| 5 | `kind` | u8 | 1 | 1 `DATA`, 2 `INDEX`, 3 `END` |
| 6 | `codec` | u8 | 1 | 0 raw, 1 Zstandard |
| 7 | `flags` | u8 | 1 | 0 |
| 8 | `header_bytes` | u16 | 2 | 64 |
| 10 | `reserved` | u16 | 2 | 0 |
| 12 | `stored_bytes` | u32 | 4 | Payload bytes as stored or transmitted |
| 16 | `raw_bytes` | u32 | 4 | Payload bytes after decompression |
| 20 | `record_count` | u32 | 4 | Number of records in a `DATA` frame; otherwise 0 |
| 24 | `frame_seq` | u64 | 8 | Starts at 0 and increases by 1 for every frame of any kind |
| 32 | `min_event_ns` | u64 | 8 | Smallest non-null `ts_event` in a `DATA` frame |
| 40 | `max_event_ns` | u64 | 8 | Largest non-null `ts_event` in a `DATA` frame |
| 48 | `payload_crc32c` | u32 | 4 | CRC of the raw payload |
| 52 | `header_crc32c` | u32 | 4 | CRC of the 64 header bytes with this field set to zero |
| 56 | `reserved` | u64 | 8 | 0 |

- The total stored size of a frame is `64 + align8(stored_bytes)`.
- The padding after the payload is outside the compression and outside the payload CRC. A reader validates that it is zero.
- For codec 0, `stored_bytes` equals `raw_bytes`.
- `stored_bytes` and `raw_bytes` are each at most 16,777,216.
- Decompression produces exactly `raw_bytes` bytes.
- A reader rejects an unknown kind, an unknown envelope version, an unknown codec and nonzero flags.
- `frame_seq` never wraps.
- A frame has no optionality bit. A reader cannot skip a frame with an unsupported codec and claim complete decoding.

**Order of frames.** `DATA` frames precede all `INDEX` frames. Zero or more contiguous `INDEX` frames precede exactly one `END` frame. A `DATA` frame cannot follow an `INDEX` frame. An empty container is valid: metadata followed directly by `END`.

## DATA frames

A `DATA` frame contains one or more complete records.

- `record_count` is at least 1. It equals the number of records parsed, and it cannot exceed `floor(raw_bytes / 48)`.
- `raw_bytes` is at least 48, is a multiple of 8 and equals the sum of the record lengths.
- `min_event_ns` and `max_event_ns` cover every non-null `ts_event` in the frame, including control records.
- If every `ts_event` in the frame is null, both bounds are null. Otherwise both bounds are non-null and exact, with minimum ≤ maximum.
- A record with a null timestamp can share a frame with non-null bounds. A time filter handles such records separately. The bounds do not show that every record has a timestamp.

## INDEX frames

An `INDEX` frame uses codec 0, `record_count` = 0 and null timestamp bounds. Its payload is one or more 40-byte entries with no count prefix. The entry count is `raw_bytes / 40`, and `raw_bytes` is a positive multiple of 40.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `data_frame_seq` | u64 | 8 | `frame_seq` of the `DATA` frame |
| 8 | `data_frame_offset` | u64 | 8 | Offset of that frame header from container byte 0 |
| 16 | `min_event_ns` | u64 | 8 | `min_event_ns` of that frame |
| 24 | `max_event_ns` | u64 | 8 | `max_event_ns` of that frame |
| 32 | `raw_bytes` | u32 | 4 | `raw_bytes` of that frame |
| 36 | `record_count` | u32 | 4 | `record_count` of that frame |

- If a container has `INDEX` frames, their concatenated entries list every `DATA` frame exactly once, in ascending `frame_seq` order, with values identical to the frame headers.
- A container can hold several `INDEX` frames to stay within the frame size maximum.
- An entry cannot refer to metadata, to an `INDEX` frame, to the `END` frame or to bytes outside the container.
- An empty container has no `INDEX` frames.

**Using the index.**

- The index selects candidate frames. It is not a checkpoint of state.
- Timestamp ranges of frames can overlap or go backward. Binary search by timestamp is invalid unless monotonic order is established separately, for example by a manifest `ordering` of `ts_event` that a validator has checked. See [MANIFEST](metadata.md#manifest).
- A general reader examines all index ranges and reads the selected frames in their original order.
- A reader needs an explicit policy for records with null timestamps. Frame bounds do not identify every frame that holds one.
- A seek to a trade or a quote still needs the instrument definitions that precede it. `MBO` needs an earlier complete snapshot or `CLEAR` and every update after it.
- A consumer that seeks without that context labels its results as raw or partial. It cannot claim a reconstructed valid book.
- [`FRAME_SUMMARY`](../records/FRAME_SUMMARY.md) adds the record types and the instrument range of each frame. It does not carry state.

## END frame

The `END` frame uses codec 0, `record_count` = 0 and null timestamp bounds. Its payload is 32 bytes, so the frame is exactly 96 bytes.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `first_index_offset` | u64 | 8 | Offset of the first `INDEX` frame, or 0 when there is none |
| 8 | `total_data_frames` | u64 | 8 | Number of `DATA` frames |
| 16 | `total_records` | u64 | 8 | Number of records in all `DATA` frames |
| 24 | `completion_status` | u32 | 4 | 0 normal, 1 aborted by the producer |
| 28 | `reserved` | u32 | 4 | 0 |

- The counts include optional records that a reader does not know. They match the container.
- A nonzero `first_index_offset` identifies the first `INDEX` frame, and every frame from there to `END` is an `INDEX` frame.
- The `frame_seq` of `END` equals the number of `DATA` and `INDEX` frames before it.
- No bytes follow `END` in one NWT object, not even another container. Concatenation needs an external bundle format or separate objects.

**Reading from the end.** A seekable reader can read the last 96 bytes to find the index. It validates `END` and every bound that `END` refers to. This shortcut does not validate the content of the file or the completeness of the index. A strict full validator compares the counts, sequences, entries and payloads with a sequential scan.

**Completion.**

- A normal `END` means the producer completed the container on purpose. It does not certify that the source had no gaps.
- An aborted `END` preserves a structurally complete prefix and reports unsuccessful completion.
- End of input without `END` is an incomplete container, even exactly on a frame boundary. A reader can expose a verified prefix only with an explicit incomplete result.
- A live connection has no `END` yet and is in progress. A clean transport close does not replace `END`.
