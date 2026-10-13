# How values are encoded

## Three kinds of type

Three different numbers are called a type or a version. Each selects a different thing, and none of them is a message code of an exchange.

| Number | Stored in | Selects |
|---|---|---|
| Container version | `major` and `minor` of the container header | The outer format |
| Frame kind | `kind` of the frame header | `DATA`, `INDEX` or `END` |
| Record type and schema version | `record_type` and `schema_version` of the record header | The record layout: `TRADE`, `QUOTE` and the other record types |

## Constants and conversions

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

## How to read a field table

The field table of each record type, on its [record page](../records/INDEX.md), lists the fields that follow the 48-byte common record header, in wire order. The tables of the structures below use the same columns.

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
