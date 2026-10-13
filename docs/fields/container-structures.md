# Container structures

A container is a 64-byte container header, a metadata block, a run of frames and one `END` frame. The tables below describe each structure outside the records. Offsets count from the start of the structure.

Every CRC field holds a CRC-32C. A header CRC covers the whole 64-byte header with its own CRC field set to zero. The other checksum fields of that header keep their stored values during the calculation.

The kit includes the decoded values of these fields for an example container:

<!-- nwt-file: fixtures/container-fields.json lines=1-20 -->

## Container header

The container header is the first 64 bytes of a file or stream. The first frame starts at byte `64 + metadata_bytes`.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `magic` | `bytes[8]` | 8 | `4e 57 54 42 49 4e 0d 0a`, the ASCII text `NWTBIN` followed by CR and LF |
| 8 | `major` | `u16` | 2 | 1 |
| 10 | `minor` | `u16` | 2 | 1 when the manifest declares any record type 10–22, otherwise 0. A reader accepts both values |
| 12 | `header_bytes` | `u16` | 2 | 64 |
| 14 | `flags` | `u16` | 2 | 0 |
| 16 | `metadata_bytes` | `u32` | 4 | Size of the metadata block, including the padding of every element. A multiple of 8, from 8 to 1,048,576 |
| 20 | `metadata_crc32c` | `u32` | 4 | CRC-32C of all metadata bytes, padding included |
| 24 | `stream_id` | `bytes[16]` | 16 | Opaque nonzero 128-bit identifier of this container. A byte string, not an integer |
| 40 | `created_ns` | `u64` | 8 | Creation time in nanoseconds since the Unix epoch, or `UINT64_MAX` |
| 48 | `reserved` | `u64` | 8 | 0 |
| 56 | `header_crc32c` | `u32` | 4 | CRC-32C of the 64 header bytes with this field set to zero |
| 60 | `reserved` | `u32` | 4 | 0 |

## Metadata element

The metadata block is a sequence of elements. Each element is an 8-byte header, a value and zero padding to a multiple of 8 bytes.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `type` | `u16` | 2 | 1 is `MANIFEST`, 2 is `PROVENANCE`. Values from 32768 to 65534 are private |
| 2 | `flags` | `u16` | 2 | Bit 0 is `REQUIRED`. The other bits are zero |
| 4 | `value_bytes` | `u32` | 4 | Length of the value alone, without this header and without the padding |
| 8 | `value` | `bytes[value_bytes]` | `value_bytes` | The value. JSON for `MANIFEST` and `PROVENANCE` |
| 8 + `value_bytes` | `padding` | `bytes` | 0 to 7 | Zero bytes up to `align8(8 + value_bytes)` |

## MANIFEST properties

The `MANIFEST` value is a JSON object that declares the publishers and the record types of the container. Every property is required except `ordering`. The [Specification](../SPECIFICATION.md) gives the full rules.

| Property | JSON type | Meaning |
|---|---|---|
| `dataset` | string | Stable namespace of the data, 1 to 255 UTF-8 bytes |
| `producer` | string | Name and version of the producer, 1 to 255 bytes |
| `profile` | string | `market-data` or `generic-events`. The files of this kit use `market-data` |
| `clock` | string | `posix-ns` |
| `publishers` | array | At most 4096 entries with unique nonzero identifiers |
| `publishers[].id` | integer | The value that `publisher_id` of a record refers to, a nonzero `u32` |
| `publishers[].name` | string | 1 to 255 bytes |
| `publishers[].venue` | string | 0 to 255 bytes |
| `schemas` | array | 1 to 4096 entries. Each pair of type and version appears once |
| `schemas[].type` | integer | Record type, 1 to 65534 |
| `schemas[].version` | integer | 1 to 255. 1 for the standard record types |
| `schemas[].required` | boolean | When `true`, a reader that does not know the record type refuses to interpret the records. Always `true` for `MBO`, `BOOK_SNAPSHOT`, `INSTRUMENT_DEF`, `STATUS`, `GAP` and `BOOK_DELTA`, always `false` for `FRAME_SUMMARY` |
| `schemas[].name` | string | Name of the record type, 1 to 255 bytes |
| `schemas[].spec_uri` | string | 1 to 2048 bytes. `urn:nwt:spec:1.0` for types 1–9 and `urn:nwt:spec:1.1` for types 10–22 |
| `ordering` | string | Optional. `none` when absent, `ts_event` or `instrument,ts_event`. A statement about the order of the records that a validator checks |

## PROVENANCE properties

The `PROVENANCE` value is an optional JSON object that describes where the data came from. Its string properties are `source_format`, `source_version`, `converter`, `conversion_policy`, `clock_policy` and `license_reference`. Each is at most 4096 UTF-8 bytes.

These properties describe the data. They are not instructions, and they do not override a unit or a rule of the format. Other properties are allowed when they follow the JSON rules of the Specification. Credentials of a source do not belong in the metadata.

## Frame header

Every frame starts with this 64-byte header. A stored frame occupies `64 + align8(stored_bytes)` bytes.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `magic` | `bytes[4]` | 4 | `4e 57 46 31`, the ASCII text `NWF1` |
| 4 | `envelope_version` | `u8` | 1 | 1 |
| 5 | `kind` | `u8` | 1 | 1 is `DATA`, 2 is `INDEX`, 3 is `END` |
| 6 | `codec` | `u8` | 1 | 0 is raw, 1 is Zstandard |
| 7 | `flags` | `u8` | 1 | 0 |
| 8 | `header_bytes` | `u16` | 2 | 64 |
| 10 | `reserved` | `u16` | 2 | 0 |
| 12 | `stored_bytes` | `u32` | 4 | Payload size as stored or transmitted, without this header and without the frame padding |
| 16 | `raw_bytes` | `u32` | 4 | Payload size after decompression. Equal to `stored_bytes` for codec 0 |
| 20 | `record_count` | `u32` | 4 | Number of records in a `DATA` frame. 0 in the other kinds |
| 24 | `frame_seq` | `u64` | 8 | Starts at 0 and increases by 1 with every frame |
| 32 | `min_event_ns` | `u64` | 8 | Smallest non-null `ts_event` among the records of a `DATA` frame |
| 40 | `max_event_ns` | `u64` | 8 | Largest non-null `ts_event` among the records of a `DATA` frame |
| 48 | `payload_crc32c` | `u32` | 4 | CRC-32C of the raw payload |
| 52 | `header_crc32c` | `u32` | 4 | CRC-32C of the 64 header bytes with this field set to zero |
| 56 | `reserved` | `u64` | 8 | 0 |

## INDEX entry

The payload of an `INDEX` frame is a run of 40-byte entries, one for each `DATA` frame.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `data_frame_seq` | `u64` | 8 | `frame_seq` of the `DATA` frame |
| 8 | `data_frame_offset` | `u64` | 8 | Offset of that frame header, counted from byte 0 of the container |
| 16 | `min_event_ns` | `u64` | 8 | `min_event_ns` of that frame |
| 24 | `max_event_ns` | `u64` | 8 | `max_event_ns` of that frame |
| 32 | `raw_bytes` | `u32` | 4 | `raw_bytes` of that frame |
| 36 | `record_count` | `u32` | 4 | `record_count` of that frame |

## END payload

The `END` frame closes a container. Its payload is 32 bytes.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `first_index_offset` | `u64` | 8 | Offset of the first `INDEX` frame from byte 0 of the container, or 0 when there is no `INDEX` frame |
| 8 | `total_data_frames` | `u64` | 8 | Number of `DATA` frames |
| 16 | `total_records` | `u64` | 8 | Number of records in all `DATA` frames |
| 24 | `completion_status` | `u32` | 4 | 0 for a normal end, 1 when the producer aborted |
| 28 | `reserved` | `u32` | 4 | 0 |
