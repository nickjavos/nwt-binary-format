# Field reference

This page explains how the format encodes values and lists the fields of the structures that every container shares: the common record header, the container header, the metadata, the frame header, the index entries and the end structure. For each field it gives the offset, the type, the width, the unit, the null value and the validation rules. Use it while you write a decoder or an encoder, and when a value in a file needs an explanation. The fields of each record type are on its own page; start from [Record types](records/INDEX.md). The [Specification](SPECIFICATION.md) states the rules in full, and [Working with the examples](FEED-COOKBOOK.md) shows how to build and run the reference codecs.

## How values are encoded

### Three kinds of type

Three different numbers are called a type or a version. Each selects a different thing, and none of them is a message code of an exchange.

| Number | Stored in | Selects |
|---|---|---|
| Container version | `major` and `minor` of the container header | The outer format |
| Frame kind | `kind` of the frame header | `DATA`, `INDEX` or `END` |
| Record type and schema version | `record_type` and `schema_version` of the record header | The record layout: `TRADE`, `QUOTE` and the other record types |

### Constants and conversions

| Convention | Rule |
|---|---|
| Byte order | Little-endian for every multi-byte integer |
| Price, strike, multiplier | `i64` holding the value × 10⁹, exactly |
| Quantity, volume | `u64` holding the value × 10⁹, in the quantity unit of the instrument definition |
| Timestamp | `u64` nanoseconds since the Unix epoch on the POSIX time scale, never milliseconds or microseconds |
| Null of a signed field | `INT64_MIN`, which is `-9223372036854775808` |
| Null of an unsigned 64-bit field | `UINT64_MAX`, which is `18446744073709551615` |
| Null of a count | `UINT32_MAX`, which is `4294967295`, only where the record type permits it |
| Padding | Zero bytes up to the next multiple of 8 |
| Text | UTF-8 without NUL. A length counts bytes. Texts follow in the order of their length fields |
| Booleans | None in the record layouts. The metadata uses JSON booleans |

To encode a decimal value, multiply it by 10⁹. The price 123.45 is stored as `123450000000` and the size 0.5 as `500000000`. A quantity of exactly 1 is stored as `1000000000` even when the venue reports whole lots. Parse decimal text with decimal or integer arithmetic. The currency and the quantity unit are two separate properties of an instrument.

A few fields are plain whole numbers and are not scaled: counts, identifiers, `round_lot`, `shares_outstanding` and `interval_ns`.

### How to read a field table

The field table of each record type, on its [record page](records/INDEX.md), lists the fields that follow the 48-byte common record header, in wire order. The tables of the structures below use the same columns.

| Column | Content |
|---|---|
| Offset | Byte offset from the start of the record. The first field after the header is at 48, and each offset is the sum of the widths before it |
| Field | Field name, as in the schema |
| Type | `u8`, `u16`, `u32` and `u64` are unsigned integers, `i64` is a signed two's-complement integer, and `bytes[N]` is a block of N bytes |
| Bytes | Width of the field in bytes |
| Meaning | Unit, null value, allowed values and validation rules |

Four rules apply to the field table of every record type:

- **Text.** A record type with text lists its text fields after the fixed fields. Each text has a length field in the fixed part of the record. The texts follow the fixed part in the order of their length fields, with no terminator and no separator.
- **Record size.** A record without text has a fixed size. A record with text occupies `align8(fixed size + text bytes)`, where `align8` rounds up to the next multiple of 8 and the gap is filled with zero bytes. A `BOOK_SNAPSHOT` occupies `56 + 48 × levels` bytes.
- **Enumerations and flags.** A value or a flag bit that the table does not list is invalid.
- **Reserved fields.** Every byte of a `reserved` field is zero. Do not store application data there.

The field tables of the record types are generated from the schema, [records.json](files/records.json), so every offset and width matches it. The schema describes a field by its name, its width in bytes, its signedness, an optional kind (`price`, `quantity` or `time`) and its meaning:

<!-- nwt-file: schemas/records.json lines=116-175 -->

## Common record header

Every record starts with these 48 bytes. The offsets in the tables of the record types continue from 48.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `record_bytes` | `u32` | 4 | Size of the whole record in bytes, from the first byte of this header through the final padding. A multiple of 8, from 48 to 1,048,576. The encoder computes it. |
| 4 | `record_type` | `u16` | 2 | Record type, 1 to 22 for the standard record types. Selects the layout of the fields after this header. |
| 6 | `schema_version` | `u8` | 1 | 1 for every standard record type. Another value is another wire layout. |
| 7 | `flags` | `u8` | 1 | Bit 0 is `REPLAY`, bit 1 is `SUSPECT`. Bits 2–7 are zero. |
| 8 | `publisher_id` | `u32` | 4 | Publisher, as declared in the manifest. Nonzero for types 1–8, 10–19, 21 and 22. `SYSTEM` can use 0 together with channel 0. `FRAME_SUMMARY` always uses 0. |
| 12 | `channel_id` | `u32` | 4 | Logical partition chosen by the producer. 0 is valid. |
| 16 | `instrument_id` | `u64` | 8 | Opaque instrument identifier, scoped by dataset and publisher. Nonzero for types 1–7, 11–19, 21 and 22. Zero for `GAP`, `SYSTEM`, `VENUE_DEF` and `FRAME_SUMMARY`. |
| 24 | `ts_event` | `u64` | 8 | Event time at the source, in nanoseconds since the Unix epoch. `UINT64_MAX` when it is unavailable. For a `BAR` it is the end of the interval. |
| 32 | `ts_recv` | `u64` | 8 | Capture time at the producer, in nanoseconds since the Unix epoch. `UINT64_MAX` when it is unavailable. |
| 40 | `sequence` | `u64` | 8 | Position of the record in the output of one container, publisher and channel. Starts at 1, increases by 1, never wraps. |

Four points apply to the header:

- `record_type` is not a message code of the source exchange, and `sequence` is not an exchange sequence number. A `GAP` record reports a loss at the source.
- `REPLAY` marks a record that the producer identifies as historical or replayed. `SUSPECT` marks a record with a known quality problem at the source. Neither flag changes the layout or relaxes validation.
- Sequence continuity is checked separately for each pair of publisher and channel.
- `ts_event` can move backward from one record to the next, and `ts_recv` is not necessarily later than `ts_event`.

The fields of each record type that follow this header are listed on the pages of [Record types](records/INDEX.md).

## Container structures

A container is a 64-byte container header, a metadata block, a run of frames and one `END` frame. The tables below describe each structure outside the records. Offsets count from the start of the structure.

Every CRC field holds a CRC-32C. A header CRC covers the whole 64-byte header with its own CRC field set to zero. The other checksum fields of that header keep their stored values during the calculation.

The kit includes the decoded values of these fields for an example container:

<!-- nwt-file: fixtures/container-fields.json lines=1-20 -->

### Container header

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

### Metadata element

The metadata block is a sequence of elements. Each element is an 8-byte header, a value and zero padding to a multiple of 8 bytes.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `type` | `u16` | 2 | 1 is `MANIFEST`, 2 is `PROVENANCE`. Values from 32768 to 65534 are private |
| 2 | `flags` | `u16` | 2 | Bit 0 is `REQUIRED`. The other bits are zero |
| 4 | `value_bytes` | `u32` | 4 | Length of the value alone, without this header and without the padding |
| 8 | `value` | `bytes[value_bytes]` | `value_bytes` | The value. JSON for `MANIFEST` and `PROVENANCE` |
| 8 + `value_bytes` | `padding` | `bytes` | 0 to 7 | Zero bytes up to `align8(8 + value_bytes)` |

### MANIFEST properties

The `MANIFEST` value is a JSON object that declares the publishers and the record types of the container. Every property is required except `ordering`. The [Specification](SPECIFICATION.md) gives the full rules.

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

### PROVENANCE properties

The `PROVENANCE` value is an optional JSON object that describes where the data came from. Its string properties are `source_format`, `source_version`, `converter`, `conversion_policy`, `clock_policy` and `license_reference`. Each is at most 4096 UTF-8 bytes.

These properties describe the data. They are not instructions, and they do not override a unit or a rule of the format. Other properties are allowed when they follow the JSON rules of the Specification. Credentials of a source do not belong in the metadata.

### Frame header

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

### INDEX entry

The payload of an `INDEX` frame is a run of 40-byte entries, one for each `DATA` frame.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `data_frame_seq` | `u64` | 8 | `frame_seq` of the `DATA` frame |
| 8 | `data_frame_offset` | `u64` | 8 | Offset of that frame header, counted from byte 0 of the container |
| 16 | `min_event_ns` | `u64` | 8 | `min_event_ns` of that frame |
| 24 | `max_event_ns` | `u64` | 8 | `max_event_ns` of that frame |
| 32 | `raw_bytes` | `u32` | 4 | `raw_bytes` of that frame |
| 36 | `record_count` | `u32` | 4 | `record_count` of that frame |

### END payload

The `END` frame closes a container. Its payload is 32 bytes.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `first_index_offset` | `u64` | 8 | Offset of the first `INDEX` frame from byte 0 of the container, or 0 when there is no `INDEX` frame |
| 8 | `total_data_frames` | `u64` | 8 | Number of `DATA` frames |
| 16 | `total_records` | `u64` | 8 | Number of records in all `DATA` frames |
| 24 | `completion_status` | `u32` | 4 | 0 for a normal end, 1 when the producer aborted |
| 28 | `reserved` | `u32` | 4 | 0 |

## Interpretation checklist

A correct decoder or encoder agrees with every point below.

### Sizes and lengths

- `record_bytes` counts the 48-byte header. `stored_bytes` and `raw_bytes` do not count the frame header.
- `stored_bytes` leaves out the frame padding. `metadata_bytes` includes the padding of every metadata element.
- A text length counts UTF-8 bytes, not characters. A limit of 255 bytes accepts 127 two-byte characters plus one ASCII byte and rejects one byte more.
- Every `reserved` field is zero. A record type can have more than one: `LISTING`, `SYMBOL_MAP`, `TRADE_QUOTE`, `FRAME_SUMMARY` and `CORPORATE_ACTION` do.
- Records are transferred inside a `.nwt` container. A conformance vector stored as a bare record in a `.bin` file has no manifest and no CRC.

### Nulls and numbers

- The meaning of `UINT64_MAX` depends on the field. It is the null of a time, a quantity or a priority, and it is a legal value of an order identifier or a trade identifier.
- The size and the order count of an absent quote side are zero, not null. A null ask price requires a zero ask size and a zero ask count.
- `shares_outstanding` of `SECURITY_DEF` is a whole number of shares, not a value scaled by 10⁹. `round_lot`, `order_count`, `option_id` and `serial_id` are plain counts too.
- `interval_ns` of `BEST_QUOTE` is a duration, not a timestamp.
- Every `STATISTICS` record has both `price` and `quantity`. Which of the two is null depends on `stat_type` and `action`.
- A null `ts_event` is valid where the record type allows it, for example in `LISTING`. A frame whose records all have a null `ts_event` has null bounds.
- `min_event_ns` is the smallest non-null event time of the frame. It is not necessarily the time of the first record.

### State and order

- Instrument definitions apply in byte order. Sorting the records by `ts_event` changes their interpretation.
- The quantity of an `MBO` `MODIFY` is the absolute remaining size. A `TRADE` does not reduce the order book.
- The state of `BEST_QUOTE` and `TRADE_QUOTE` is separate from the state of `QUOTE`. They do not replace it.
- Sequence checks, CRC checks and gap recovery continue when `REPLAY` or `SUSPECT` is set. The flags replace none of these.
- `details` of `CORPORATE_ACTION` passes through the codec as text. That it is one JSON object with sorted keys is a rule for producers and for the state rules, not for the codec.
