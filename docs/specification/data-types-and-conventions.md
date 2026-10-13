# Data types and conventions

## Representation

- All integers are little-endian. Signed integers use two's complement.
- `u8`, `u16`, `u32`, `u64` and `i64` have their stated widths. `bytes[N]` is exactly N bytes.
- There are no implicit padding bytes of a compiler. Offsets in layout tables are byte offsets from the start of the structure.
- Reserved fields and padding are zero. A strict reader rejects a nonzero value.
- Standard record payloads contain no floating-point values and no variable-length integers.

## Alignment

`align8(n) = (n + 7) & ~7`, computed with checked arithmetic.

- Metadata elements, frame starts and the starts of uncompressed records are aligned to 8 bytes relative to their enclosing buffer.
- Compressed bytes have no record alignment until they are decompressed.
- Alignment in the file does not establish memory alignment in an arbitrary network buffer.

## Text

- Text is well-formed UTF-8. It is not NUL-terminated.
- A text length counts bytes, not characters.
- An embedded NUL and invalid UTF-8 are prohibited in text fields.
- Identifiers are case-sensitive and compared byte for byte. We recommend that producers use NFC normalization.

## Time

A timestamp is a `u64` count of nanoseconds since 1970-01-01T00:00:00 on the POSIX time scale. Leap seconds are not counted as additional seconds.

- The null timestamp is `UINT64_MAX`. Zero is the epoch, not null.
- A timestamp before the epoch cannot be represented.
- Time from a source that uses another clock scale is converted to this scale before encoding. A leap-smear policy, if one is used, is described in the metadata.
- `ts_event` is the source event time, or null when it is unavailable.
- `ts_recv` is the capture time at the producer, or null when it is unavailable.
- The two times need not be ordered. A consumer cannot infer network delay from them unless the relationship between the clocks is known.
- A late event keeps its original timestamp.

## Decimal values and null values

| Logical type | Wire type | Meaning | Null |
|---|---|---|---|
| Price | `i64` | Integer × 10⁻⁹, in the currency of the definition | `INT64_MIN` |
| Quantity | `u64` | Integer × 10⁻⁹, in the quantity unit of the definition | `UINT64_MAX` |
| Multiplier | `i64` | Integer × 10⁻⁹ | `INT64_MIN` |
| Count | `u32` | Integral count | `UINT32_MAX` |
| Identifier | Stated unsigned width | Opaque value in a namespace | Stated with each field |

The null values are `INT64_MIN` = −9,223,372,036,854,775,808, `UINT64_MAX` = 18,446,744,073,709,551,615 and `UINT32_MAX` = 4,294,967,295. An all-zero value is not a null.

- The price 123.45 is encoded as `123450000000`. The quantity 10 is encoded as `10000000000`.
- A price of zero and a negative price are valid. A non-null quantity is nonnegative.
- The largest price is about 9.22 billion currency units. The largest quantity is about 18.45 billion units.
- A producer rejects a value that is out of range, or uses a different registered schema. Silent clamping, wrapping and rounding are not allowed.
- An input with more than nine fractional digits needs an explicit conversion policy outside this format. A conversion that rounds reports the loss to the caller and describes it in `PROVENANCE`.
- For arithmetic, we recommend checked intermediates wider than 64 bits.

## Identifiers

- A publisher ID is a `u32`. An instrument ID, an order ID and a trade ID are `u64`.
- Publisher 0 and instrument 0 are reserved for the container and system scope, where a record type allows them. Other identifiers can use their full range unless a schema says otherwise.
- An instrument is identified by `(dataset, publisher_id, instrument_id)`, not by its symbol alone.
- The producer owns that namespace. Within the history of one dataset, an instrument ID is never reused for a different economic instrument.
