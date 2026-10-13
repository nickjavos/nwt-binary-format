# NWT Binary Format

## Version 1.1 — Proposed specification

**Document status:** implementation draft, revision 1.1-draft.1
**Date:** 13 October 2026
**Format identifier:** NWT
**Scope:** binary transport and storage of normalized market data and reference data, with an extension mechanism for other event data.

This document proposes a format. It does not describe an existing NWT standard or claim deployment or measured performance. “NWT” is treated as the requested product name; no expansion of the acronym is assumed. All NWT allocations and layouts below are design decisions in this draft.

NWT is a container of framed, checksummed records. A metadata block declares the schemas and publishers in use. Frames carry fixed-layout records with nanosecond timestamps, 64-bit instrument IDs and exact fixed-point decimals. The same bytes serve live transport and file storage.

**What revision 1.1 adds.** Thirteen record types (10–22) for reference data and market-data extras; an optional `ordering` property in the manifest; FRAME_SUMMARY records, a richer index that a 1.0 reader skips; and a **store profile**, a set of writer choices that make a file fast to query while using the same container. The container header, TLV encoding, frame envelope, record header, INDEX and END are unchanged. Types 1–9 and every byte of a 1.0 file keep their meaning, so a 1.0 file is a valid 1.1 input. Types 1–9 use the `spec_uri` `urn:nwt:spec:1.0`; types 10–22 use `urn:nwt:spec:1.1`.

This revision includes a [complete field reference](FIELD-REFERENCE.md), a [feed cookbook](FEED-COOKBOOK.md), an [implementation guide](IMPLEMENTATION-GUIDE.md), a [store guide](STORE.md) and a [tool guide](TOOLS.md).

## Contents

1. Requirements and conformance
2. Architecture and design decisions
3. Primitive types and numerical conventions
4. Container header
5. Metadata
6. Frame envelope
7. Record header
8. Standard record schemas
9. Ordering, gaps, snapshots, and replay
10. Compression and integrity
11. Index, summaries, store profile and end-of-stream
12. Transport and recovery
13. Schema evolution and registries
14. Decoder and encoder requirements
15. Security and operational limits
16. Interoperability and conversion
17. Examples and binary test vectors
18. Conformance test plan
19. Performance and implementation guidance
20. Release acceptance and future work
21. References
22. Developer kit and clarified implementation boundaries

## 1. Requirements and conformance

The words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** identify mandatory requirements, recommendations, and optional behavior. A recommendation may be departed from for a documented operational reason; a mandatory requirement may not.

NWT targets deterministic decoding, bounded memory use, mixed schemas, incremental streaming, nanosecond timestamps, precise decimal values, corruption detection, and a shared representation for live and historical data. It supports ordered byte streams and files. Datagram delivery, bidirectional subscription negotiation, authentication messages, distributed consensus, exactly-once application processing, and arbitrary precision decimals are outside this specification. Types 11, 21 and 22 carry the option, security-master and corporate-action fields listed in §8; anything beyond those fields, such as full terms and conditions or entitlement data, needs a private schema.

Conformance claims MUST identify the following capabilities:

| Capability | Requirement |
|---|---|
| Core reader | Container, metadata, codec 0, frame integrity, record envelopes, INDEX and END |
| Core writer | Emit fully valid containers and the schemas it advertises |
| Zstd reader/writer | Optional codec 1 support, explicitly advertised |
| Store reader/writer | The store profile of §11.4: INDEX, FRAME_SUMMARY, optional `ordering`, and selective frame reads |
| Market-data reader | Semantics of every standard schema listed in its supported subset |
| Lossless relay | Preserve all record bytes, including unknown optional records |
| Semantic consumer | Refuse unsupported required schemas; disclose skipped optional data |

A core reader may inspect opaque records without interpreting their payloads. It MUST NOT claim market-data semantic conformance merely because framing succeeds. Optional Zstd support means an uncompressed-only reader is conformant but cannot read every NWT file.

## 2. Architecture and design decisions

```text
Container
  64-byte container header
  metadata TLVs, padded individually to 8 bytes
  DATA frame 0
  DATA frame 1
  ...
  optional contiguous INDEX frames
  END frame, exactly 96 bytes

DATA frame
  64-byte frame header
  stored payload (raw records or one Zstd frame)
  zero padding to an 8-byte boundary

Uncompressed DATA payload
  48-byte record header + schema payload + optional zero padding
  next complete record
```

There is no global compression wrapper. Each DATA frame is independently decodable after its metadata is known. Records never cross frame boundaries. Metadata is immutable for a container; evolving instrument definitions appear as records. All declared schemas and publishers MUST be known in metadata before any records reference them.

Fixed layouts keep the event path simple. Frames provide batching, bounded decompression, and corruption boundaries at the cost of 64 bytes per batch and possible buffering latency. The 48-byte record header deliberately includes both timestamps, a 64-bit instrument ID, and a sequence number. This is a design tradeoff, not a claim about size or speed.

Design principles, in the order they were applied:

1. **Fixed layouts.** Every standard record has a fixed size or a size computed from stated lengths. A reader never scans for a terminator.
2. **Frames are the unit of integrity.** A frame carries one CRC over its raw payload. No record is trusted before its frame passes.
3. **Byte order is delivery order.** Records are never sorted. Definitions, snapshots and trade lifecycles depend on the order in which they arrive.
4. **Exact numbers.** Prices and quantities are integers scaled by 10^-9. There is no floating point on the wire.
5. **Nothing is inferred.** A fact the producer does not know is null or “unknown”. A consumer does not derive it from a symbol.
6. **Same container for transport and storage.** A store file (§11.4) is an ordinary container written with particular choices. Nothing is added to the container to support it.

Recommended suffix: `.nwt`, whether individual frames are compressed or not. Suggested private media type: `application/x-nwt`; this document does not claim an IANA registration.

## 3. Primitive types and numerical conventions

### 3.1 Representation

All integers are little-endian. Signed integers use two's complement. `u8/u16/u32/u64` and `i64` have their stated widths; `bytes[N]` is exactly N octets. There are no implicit compiler padding bytes. Offsets in layout tables are byte offsets from the beginning of that structure. Reserved fields and padding MUST be zero in this version; strict readers MUST reject nonzero values.

`align8(n) = (n + 7) & ~7`, computed with checked arithmetic. Container metadata, frame starts, and uncompressed record starts are 8-byte aligned relative to their enclosing buffer. Compressed bytes have no record alignment guarantee until decompressed. File-relative alignment does not establish actual memory alignment in an arbitrary network buffer.

Strings are well-formed UTF-8, not NUL-terminated. String lengths count bytes. Embedded NUL and invalid UTF-8 are prohibited in text fields. Identifiers are case-sensitive and compared byte-for-byte; producers SHOULD use NFC normalization. There are no floating-point values or varints in the standard record payloads.

### 3.2 Time

Timestamps are `u64` nanoseconds since 1970-01-01T00:00:00 on the POSIX time scale. They do not count leap seconds as additional seconds. The null timestamp is `UINT64_MAX`. Zero is the epoch, not null. Sources using another clock scale MUST be normalized before encoding; a leap-smear policy, if used, MUST be described in metadata.

`ts_event` is the source event time, or null when unavailable. `ts_recv` is the producer capture time, or null when unavailable. These times need not be ordered and MUST NOT be used to infer network delay without a known clock relationship. A late event retains its original timestamp. this version cannot represent pre-epoch timestamps.

### 3.3 Decimal values and nulls

| Logical type | Wire representation | Meaning | Null |
|---|---|---|---|
| Price | `i64` | integer × 10^-9 in the definition's currency | `INT64_MIN` |
| Quantity | `u64` | integer × 10^-9 in the definition's quantity unit | `UINT64_MAX` |
| Multiplier | `i64` | integer × 10^-9 | `INT64_MIN` |
| Count | `u32` | integral count | `UINT32_MAX` |
| Identifier | stated unsigned width | opaque namespace value | field-specific |

For example, price 123.45 is encoded as 123450000000; quantity 10 is 10000000000. Price zero and negative prices are valid. Non-null quantities are nonnegative. The largest representable price is approximately 9.22 billion currency units; the largest quantity is approximately 18.45 billion units. Producers MUST reject out-of-range values or use a different registered schema. They MUST NOT silently clamp, wrap, or round.

An input with more than nine fractional digits requires an explicit conversion policy outside this format. A conversion that rounds MUST report the loss to the caller and describe it in provenance metadata. Arithmetic SHOULD use checked intermediates wider than 64 bits. There is no universal all-zero null convention.

### 3.4 Identifiers

Publisher IDs are `u32`, instrument IDs and order/trade IDs are `u64`. Publisher 0 and instrument 0 are reserved for container/system scope where specifically allowed. Other identifiers may use their full range unless a schema says otherwise. An instrument is identified by `(dataset, publisher_id, instrument_id)`, not by symbol alone. The producer owns that namespace and MUST NOT reuse an instrument ID for a different economic instrument within the same dataset history.

## 4. Container header

The container starts at byte 0 and has this exact 64-byte header:

| Offset | Bytes | Type | Field | Meaning |
|---:|---:|---|---|---|
| 0 | 8 | bytes | magic | `4e 57 54 42 49 4e 0d 0a` (`NWTBIN\r\n`) |
| 8 | 2 | u16 | major | 1 |
| 10 | 2 | u16 | minor | 0 or 1, by the rule below |
| 12 | 2 | u16 | header_bytes | 64 |
| 14 | 2 | u16 | flags | 0 |
| 16 | 4 | u32 | metadata_bytes | Total padded metadata size |
| 20 | 4 | u32 | metadata_crc32c | CRC of all metadata bytes including padding |
| 24 | 16 | bytes | stream_id | Opaque nonzero 128-bit identifier |
| 40 | 8 | u64 | created_ns | Creation time, or null |
| 48 | 8 | u64 | reserved | 0 |
| 56 | 4 | u32 | header_crc32c | CRC of 64 bytes with this field zero |
| 60 | 4 | u32 | reserved | 0 |

`minor` is 1 when the manifest declares at least one of the standard types 10–22, and 0 otherwise. Declaring only private types (32768–65534) does not make it 1. A writer MUST set it by this rule. A reader accepts 0 and 1 and MUST reject a header whose `minor` disagrees with the declared types. The rule makes the minor number a reliable hint: a 1.0 file stays minor 0.

`metadata_bytes` MUST be a multiple of 8, at least 8, and at most 1,048,576. The first frame begins at `64 + metadata_bytes`. Header validation MUST precede trusting metadata lengths. CRC parameters are in §10.

`stream_id` is a byte string, not a little-endian integer or language-specific GUID structure. Its textual form is 32 lowercase hex characters in byte order. It MUST identify one immutable container byte sequence, including metadata and frames. A retransmission of the same bytes preserves it. A new connection producing different framing, a filtered export, repaired file, or recompressed file MUST use a new ID. Producers SHOULD generate it with a cryptographically strong random generator.

## 5. Metadata

### 5.1 TLV encoding

Each metadata element is `type:u16, flags:u16, value_bytes:u32, value, padding`. The header is 8 bytes; padding is `align8(8 + value_bytes) - (8 + value_bytes)` zero bytes. `value_bytes` excludes header and padding. Elements exactly fill `metadata_bytes`; no trailing material is permitted.

Flag bit 0 is `REQUIRED`. Other bits MUST be zero. A reader MUST reject an unknown required TLV. It MAY skip an unknown optional TLV after validating its bounds and padding. Types 0 and 65535 are invalid; 1–32767 are standard allocations and 32768–65534 are private. All TLV types are singleton; duplicate types are invalid, including unknown types.

| Type | Name | Requirement |
|---:|---|---|
| 1 | MANIFEST | Exactly one; REQUIRED bit MUST be set |
| 2 | PROVENANCE | Optional JSON object; REQUIRED bit MUST be clear |
| 32768–65534 | Private extension | Out-of-band definition; flag controls support requirement |

### 5.2 MANIFEST

The value is a UTF-8 JSON object without BOM. Duplicate object keys, NaN, infinity, malformed Unicode, and JSON nesting deeper than 16 levels MUST be rejected. The maximum is the metadata size limit. Standard JSON numbers in the manifest are restricted to exact integers from 0 through 4294967295; values needing more range MUST be strings with schema-defined syntax. Unknown object properties MAY be ignored and MUST NOT change the interpretation of existing fields.

Required top-level fields are:

| Field | Type | Rules |
|---|---|---|
| `dataset` | string | 1–255 UTF-8 bytes; stable namespace |
| `producer` | string | 1–255 bytes; producer name/version |
| `profile` | string | Exactly `market-data` or `generic-events` |
| `publishers` | array | Up to 4096 entries; IDs unique |
| `schemas` | array | 1–4096 entries; `(type,version)` unique |
| `clock` | string | Exactly `posix-ns` |

One optional top-level field is defined:

| Field | Type | Rules |
|---|---|---|
| `ordering` | string | `none` (default when absent), `ts_event`, or `instrument,ts_event`. A claim about byte order; see below |

`ordering` is a claim by the producer about the order of records in the container. `ts_event` means the non-null `ts_event` values are non-decreasing in byte order across the whole container; records with a null `ts_event` are exempt. `instrument,ts_event` means the `instrument_id` values are non-decreasing in byte order, and within one `instrument_id` the non-null `ts_event` values are non-decreasing. A producer MUST declare an ordering only when it holds. A validator checks the claim against a full scan, and a false claim is an error. A reader that does not know the property ignores it, so it changes no wire meaning. Binary search by time is valid only when a validated `ts_event` ordering is declared (§11.1).

Each publisher object contains `id` (1–4294967295), `name` (1–255 bytes), and `venue` (0–255 bytes). An empty publisher list is permitted only when every record uses the system scope. A venue is a producer-defined name, not necessarily a MIC.

Each schema object contains `type` (1–65534), `version` (1–255), `required` (boolean), `name` (1–255 bytes), and `spec_uri` (1–2048 bytes). Standard schemas use version 1 and their names from §8. The `spec_uri` is `urn:nwt:spec:1.0` for types 1–9 and `urn:nwt:spec:1.1` for types 10–22. A private schema MUST provide a stable URI identifying its exact external specification. A URI is an identifier, not an instruction to fetch or execute code. The registry is a declaration, not an embedded general-purpose schema language.

For built-in stateful types MBO, BOOK_SNAPSHOT, INSTRUMENT_DEF, STATUS, GAP and BOOK_DELTA, `required` MUST be true. For FRAME_SUMMARY, `required` MUST be false, so that a reader that does not know it can skip it. For the other standard types the producer chooses, according to the consumer contract. Every emitted `(type,version)` MUST be declared even if optional. Every nonzero publisher in a record MUST be declared. Extra unused declarations are permitted.

Example:

```json
{
  "dataset": "EXAMPLE.MARKET",
  "producer": "nwt-example/1.0",
  "profile": "market-data",
  "clock": "posix-ns",
  "publishers": [{"id": 1, "name": "Example Feed", "venue": "EXAMPLE"}],
  "schemas": [
    {"type": 1, "version": 1, "required": true, "name": "TRADE", "spec_uri": "urn:nwt:spec:1.0"},
    {"type": 6, "version": 1, "required": true, "name": "INSTRUMENT_DEF", "spec_uri": "urn:nwt:spec:1.0"}
  ]
}
```

`market-data` requires instrument definitions before use and the semantic rules in §8–9. `generic-events` permits system and private event schemas but MUST NOT contain built-in types 1–7 or 10–19; it does not relax framing or sequencing. GAP, SYSTEM and FRAME_SUMMARY are permitted in either profile. This draft places no profile restriction on SECURITY_DEF (21) and CORPORATE_ACTION (22), which are reference records. These rules keep application semantics explicit.

### 5.3 PROVENANCE

This is a JSON object using the same text and nesting constraints. Recommended optional string properties are `source_format`, `source_version`, `converter`, `conversion_policy`, `clock_policy`, and `license_reference`. Each string is at most 4096 bytes. It MUST NOT contain credentials. Provenance is descriptive and MUST NOT override normative wire semantics.

## 6. Frame envelope

### 6.1 Header layout

Every frame begins with this 64-byte header:

| Offset | Bytes | Type | Field | Meaning |
|---:|---:|---|---|---|
| 0 | 4 | bytes | magic | `4e 57 46 31` (`NWF1`) |
| 4 | 1 | u8 | envelope_version | 1 |
| 5 | 1 | u8 | kind | 1 DATA; 2 INDEX; 3 END |
| 6 | 1 | u8 | codec | 0 raw; 1 Zstd |
| 7 | 1 | u8 | flags | 0 |
| 8 | 2 | u16 | header_bytes | 64 |
| 10 | 2 | u16 | reserved | 0 |
| 12 | 4 | u32 | stored_bytes | Payload bytes as stored/transmitted |
| 16 | 4 | u32 | raw_bytes | Payload bytes after decompression |
| 20 | 4 | u32 | record_count | DATA records; otherwise 0 |
| 24 | 8 | u64 | frame_seq | Starts at 0; increments by 1 for every frame |
| 32 | 8 | u64 | min_event_ns | Minimum non-null DATA event timestamp |
| 40 | 8 | u64 | max_event_ns | Maximum non-null DATA event timestamp |
| 48 | 4 | u32 | payload_crc32c | CRC of raw payload |
| 52 | 4 | u32 | header_crc32c | CRC of 64 bytes with this field zero |
| 56 | 8 | u64 | reserved | 0 |

Total stored frame size is `64 + align8(stored_bytes)`. Padding is outside compression and outside the payload CRC; readers MUST validate that it is zero. For codec 0, `stored_bytes == raw_bytes`. Each length MUST be at most 16,777,216 bytes. Decompression MUST produce exactly `raw_bytes` bytes.

### 6.2 Kind-specific rules

DATA contains one or more complete records and has `record_count >= 1`. `raw_bytes >= 48`, is a multiple of 8, and equals the sum of record lengths. The advertised count MUST equal the parsed count. It cannot exceed `floor(raw_bytes / 48)`.

DATA timestamp bounds cover every non-null `ts_event` in the frame, including control records. If all are null, both bounds MUST be null. Otherwise both bounds MUST be non-null and exact, with minimum <= maximum. A null-timestamp record can coexist with non-null bounds; time filtering MUST handle it separately and cannot infer that all records have timestamps from the bounds alone.

INDEX and END MUST use codec 0, `record_count = 0`, and both timestamp bounds null. DATA frames precede all INDEX frames. Zero or more contiguous INDEX frames may precede one END. No DATA may follow INDEX. Empty containers are allowed: metadata followed directly by END. Unknown kinds, envelope versions, codecs, and nonzero flags MUST be rejected.

Frame sequences MUST NOT wrap. There is no frame-level optionality bit; a reader cannot safely skip a frame with an unsupported codec and claim complete decoding.

## 7. Record header

Every record starts with the following 48 bytes:

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 0 | 4 | u32 | record_bytes, including header and padding |
| 4 | 2 | u16 | record_type |
| 6 | 1 | u8 | schema_version |
| 7 | 1 | u8 | flags |
| 8 | 4 | u32 | publisher_id |
| 12 | 4 | u32 | channel_id |
| 16 | 8 | u64 | instrument_id |
| 24 | 8 | u64 | ts_event |
| 32 | 8 | u64 | ts_recv |
| 40 | 8 | u64 | sequence |

`record_bytes` MUST be a multiple of 8, at least 48, and at most 1,048,576. Fixed standard schemas require their exact specified length. Variable standard schemas require the exact computed padded length. Additional trailing fields are not permitted under an existing schema version.

Record flags: bit 0 `REPLAY`, bit 1 `SUSPECT`; bits 2–7 reserved and zero. REPLAY means the producer identifies the record as historical/replayed; it does not alter sequence or identity. SUSPECT means known source-quality concerns; it does not excuse a malformed record. Native retransmission of a container MUST preserve all bytes, including flags.

`sequence` identifies the normalized output position within `(stream_id, publisher_id, channel_id)`. It begins at 1 and increases exactly by 1 for each record in that scope, across instruments and types. Zero is invalid. A new container restarts these sequences. The maximum may be used once; another record in that scope requires a new container. `channel_id` 0 is allowed; channels are producer-defined logical partitions, not necessarily exchange channels.

These are output sequences, not exchange-native sequence numbers. Source gaps are reported by GAP records. Filtering, merging, and re-batching into a different container require new output sequences. A consumer MUST NOT interpret a missing sequence in a filtered export as a source-feed gap.

## 8. Standard record schemas

All schemas in this section use version 1. Body offsets below are absolute record offsets. Types 1–7 require nonzero publisher and instrument IDs. Their channel ID and the instrument's publisher MUST agree with the stream context. Types 8–9 and 10–22 have the scope rules given with each type. All enum values not explicitly assigned are reserved and invalid in these schema versions.

| Type | Name | Record bytes | Purpose |
|---:|---|---:|---|
| 1 | TRADE | 88 | Trade lifecycle |
| 2 | QUOTE | 96 | Best bid and ask replacement |
| 3 | BAR | 112 | Completed time bucket |
| 4 | MBO | 88 | Order-level book mutation and snapshot markers |
| 5 | BOOK_SNAPSHOT | 56 + 48 × levels | Aggregate depth replacement |
| 6 | INSTRUMENT_DEF | align8(112 + text bytes) | Instrument interpretation |
| 7 | STATUS | 64 | Trading status |
| 8 | GAP | 80 | Source discontinuity |
| 9 | SYSTEM | align8(64 + text bytes) | Heartbeat or diagnostic |
| 10 | VENUE_DEF | align8(96 + text bytes) | Trading venue or segment (market identifier code) |
| 11 | OPTION_DEF | align8(96 + text bytes) | Option contract terms |
| 12 | LISTING | align8(72 + text bytes) | Symbol-directory listing of one instrument |
| 13 | STATISTICS | 80 | Open, high, low, close, settlement, VWAP, volume, open interest |
| 14 | OPTION_ANALYTICS | 120 | Implied volatility and Greeks |
| 15 | BOOK_DELTA | 72 | Aggregate book change by price level |
| 16 | IMBALANCE | 104 | Auction imbalance |
| 17 | SYMBOL_MAP | align8(72 + text bytes) | Symbol valid for an instrument over a time interval |
| 18 | TRADE_QUOTE | 120 | One trade with the top of book immediately before it |
| 19 | BEST_QUOTE | 112 | Best bid and offer with the venue of each side |
| 20 | FRAME_SUMMARY | 104 | Per-frame summary for selective reads |
| 21 | SECURITY_DEF | align8(216 + text bytes) | Security-master record for one listing |
| 22 | CORPORATE_ACTION | align8(184 + text bytes) | One corporate-action event |

### 8.1 TRADE — type 1

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | price |
| 56 | 8 | u64 | quantity |
| 64 | 8 | u64 | trade_id |
| 72 | 8 | u64 | original_sequence |
| 80 | 1 | u8 | action: 1 NEW, 2 CANCEL, 3 CORRECT |
| 81 | 1 | u8 | aggressor: 0 unknown, 1 buyer, 2 seller |
| 82 | 2 | u16 | conditions: bit 0 off-book; remaining bits zero |
| 84 | 4 | u32 | reserved |

NEW requires non-null price, positive non-null quantity, nonzero `trade_id`, and `original_sequence = 0`. A trade ID is unique for the instrument within the publisher/channel scope of a container. If the source lacks an ID, the producer MUST assign one deterministically within that scope.

CORRECT carries the complete replacement price, quantity, aggressor, and conditions; price and quantity have the same constraints as NEW. CANCEL requires null price, null quantity, aggressor 0, and conditions 0. CANCEL and CORRECT use the same `trade_id` and point `original_sequence` to that trade's NEW sequence in the same container/channel/instrument. The NEW must precede them. Corrections may repeat; cancel terminates the trade and subsequent correction/cancel is invalid.

An export containing a correction MUST also include its original NEW and intervening lifecycle records, even if outside the requested time interval, or reject the export as unsupported. Cross-container corrections are deliberately unsupported in this version. Stateless consumers may expose lifecycle events; aggregators MUST apply them exactly once in sequence order.

### 8.2 QUOTE — type 2

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | bid_price |
| 56 | 8 | i64 | ask_price |
| 64 | 8 | u64 | bid_quantity |
| 72 | 8 | u64 | ask_quantity |
| 80 | 4 | u32 | bid_order_count |
| 84 | 4 | u32 | ask_order_count |
| 88 | 4 | u32 | quote_flags: bit 0 indicative; others zero |
| 92 | 4 | u32 | reserved |

This is a complete replacement of both sides of the top of book. An absent side MUST use null price, zero quantity, and zero count. A present side MUST use non-null price and positive non-null quantity; count is positive or null. Negative prices are allowed. Crossed or locked quotes are representable and MUST NOT be rejected merely because bid >= ask. An empty quote is valid and clears both sides. It does not clear MBO or aggregate-depth state maintained from other schemas.

### 8.3 BAR — type 3

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | interval_start_ns |
| 56 | 8 | u64 | interval_end_ns |
| 64 | 8 | i64 | open |
| 72 | 8 | i64 | high |
| 80 | 8 | i64 | low |
| 88 | 8 | i64 | close |
| 96 | 8 | u64 | volume |
| 104 | 4 | u32 | trade_count |
| 108 | 4 | u32 | bar_flags: bit 0 empty; others zero |

Intervals are half-open `[start,end)`, non-null, and start < end. `ts_event` MUST equal interval end. BAR represents completed trade-derived buckets only. A nonempty bar requires non-null OHLC, positive non-null volume and positive non-null count, `low <= open/close <= high`, and empty bit clear. An empty bar requires the empty bit, all four prices null, and zero volume/count. Empty bars MUST NOT forward-fill prices.

Each `(publisher, channel, instrument, start, end)` appears at most once per container. Revisable bars and explicit auction/quote-derived bars require a future or private schema. The aggregation policy, including off-book trades and correction cutoff, SHOULD be described in provenance.

### 8.4 MBO — type 4

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | order_id |
| 56 | 8 | i64 | price |
| 64 | 8 | u64 | quantity |
| 72 | 8 | u64 | priority |
| 80 | 1 | u8 | action |
| 81 | 1 | u8 | side: 0 none, 1 bid, 2 ask |
| 82 | 2 | u16 | mbo_flags: 0 |
| 84 | 4 | u32 | reserved |

Actions are 1 ADD, 2 MODIFY, 3 DELETE, 4 CLEAR, 5 SNAPSHOT_BEGIN, and 6 SNAPSHOT_END. Book identity is `(publisher, channel, instrument)`. ADD/MODIFY require nonzero order ID, side 1 or 2, non-null price, and positive non-null quantity. Quantity is the absolute remaining size, not a delta. MODIFY replaces price, quantity, and priority but MUST preserve side; a side change requires DELETE then ADD. Order IDs MUST be unique among live orders in a book; reuse after DELETE is permitted.

DELETE requires an existing order ID, side 0, null price, zero quantity, and null priority (`UINT64_MAX`). It removes the whole order. CLEAR, SNAPSHOT_BEGIN, and SNAPSHOT_END require ID 0, side 0, null price, zero quantity, and null priority.

`priority` is an ascending source-provided rank/key, or null if unavailable. Smaller values have earlier priority at the same side and price. If non-null keys tie, use ascending order ID for deterministic iteration; the tie-break MUST NOT be presented as known exchange priority. Price ordering is descending for bids and ascending for asks. Arrival order alone MUST NOT be represented as definitive queue priority when the source does not supply it.

CLEAR sets the book to a valid empty state. Snapshot rules are in §9. A trade record does not implicitly mutate MBO; executions must arrive as MODIFY/DELETE as appropriate. Unknown-order MODIFY/DELETE and duplicate live-order ADD are semantic errors, not silent no-ops.

### 8.5 BOOK_SNAPSHOT — type 5

This record replaces a ranked aggregate book of at most 1024 levels on each side. It is atomic and contained in one record.

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 2 | u16 | levels: 0–1024 |
| 50 | 2 | u16 | book_flags: bit 0 depth-limited; others zero |
| 52 | 4 | u32 | reserved |
| 56 | 48 × levels | array | paired bid/ask levels |

Each 48-byte element contains, at relative offsets 0/8/16/24/32/36/40: `bid_price:i64`, `ask_price:i64`, `bid_quantity:u64`, `ask_quantity:u64`, `bid_count:u32`, `ask_count:u32`, `reserved:u64`. Presence rules match QUOTE. Bids MUST be strictly decreasing in price, asks strictly increasing. Each side may have fewer levels than the other; absent elements MUST form a suffix on that side. The final element MUST have at least one present side, unless `levels = 0`. Duplicate price levels are invalid.

`levels = 0` represents an empty observed book. The depth-limited flag means deeper prices may exist beyond the reported ranks; consumers MUST NOT infer a full exchange book. Even a zero-level snapshot may be depth-limited if the producer cannot attest completeness. This record initializes/replaces aggregate state only; it cannot reconstruct individual orders or repair MBO state.

### 8.6 INSTRUMENT_DEF — type 6

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | price_increment |
| 56 | 8 | u64 | quantity_increment |
| 64 | 8 | i64 | contract_multiplier |
| 72 | 8 | u64 | expiration_ns |
| 80 | 8 | u64 | underlying_instrument_id |
| 88 | 8 | i64 | strike |
| 96 | 1 | u8 | asset_class |
| 97 | 7 | bytes | reserved |
| 104 | 2 | u16 | symbol_bytes |
| 106 | 2 | u16 | venue_bytes |
| 108 | 2 | u16 | currency_bytes |
| 110 | 2 | u16 | quantity_unit_bytes |
| 112 | variable | bytes | symbol, venue, currency, quantity_unit, then padding |

Asset classes: 0 unspecified, 1 equity, 2 future, 3 option, 4 FX, 5 crypto, 6 index, 7 fixed income. Symbol is 1–255 bytes; venue 0–255; currency 1–16; quantity unit 1–32. Currency and quantity unit are case-sensitive producer-defined codes, for example `USD`, `BTC`, `share`, `contract`, or `base-unit`; interoperating systems MUST agree on them. Non-applicable expiration and strike are null; no underlying is 0. A nonzero underlying refers to the same publisher's namespace but need not have a definition in this container.

Non-null price/quantity increments and multiplier MUST be positive. Null means unavailable. A fixed increment may be null for a venue with a variable tick schedule; this version does not encode that schedule. INSTRUMENT_DEF alone does not carry option rights, exercise style or settlement rules. OPTION_DEF (§8.11) carries them, SECURITY_DEF (§8.21) carries identifiers and listing facts, and CORPORATE_ACTION (§8.22) carries events. A producer that lacks a fact says “unknown”. A consumer MUST NOT infer these facts from the symbol.

Definition scope is `(publisher, instrument)` across all channels. A definition MUST precede any market record for that instrument in byte order. Market records are types 1–5, 7, 13, 14, 15, 16, 18 and 19. A later definition replaces the current definition for subsequent records, regardless of its timestamp. `ts_event` describes the source definition event, not permission to apply it retroactively. Dataset, economic identity, currency, and quantity unit MUST NOT change for an existing instrument ID. Symbol, increments, multiplier, and other reference attributes may change. Existing book values remain encoded in the same units; definition updates do not rescale stored orders.

### 8.7 STATUS — type 7

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 2 | u16 | status |
| 50 | 2 | u16 | reason |
| 52 | 4 | u32 | status_flags: 0 |
| 56 | 8 | u64 | reserved |

Status: 0 unknown, 1 pre-open, 2 open, 3 halted, 4 closed, 5 auction. Reason: 0 unspecified, 1 scheduled, 2 volatility, 3 regulatory, 4 technical. STATUS replaces the state for the book scope. It does not clear books or prohibit encoding trades during an auction/halt; reported data and administrative state may not be perfectly synchronized.

### 8.8 GAP — type 8

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | first_missing_source_sequence |
| 56 | 8 | u64 | last_missing_source_sequence |
| 64 | 4 | u32 | reason |
| 68 | 4 | u32 | reserved |
| 72 | 8 | u64 | recovery_id |

Publisher MUST be nonzero and instrument MUST be 0. GAP applies to every instrument in that publisher/channel. Reason: 1 source packet loss, 2 source reset, 3 producer overflow, 4 unknown discontinuity. Missing source bounds are inclusive; both MUST be null when not known, otherwise both non-null with first <= last. They are advisory source-native values, not NWT output sequence numbers. Sources whose sequence namespace cannot fit or cannot be represented as a single interval MUST use null bounds.

`recovery_id` is a nonzero producer-assigned identifier unique among GAP records in this container. It correlates diagnostics; it is not a snapshot identifier. GAP invalidates all book and trading-status state in its scope, including the aggregate book that BOOK_DELTA maintains. Valid QUOTE, BOOK_SNAPSHOT, MBO snapshot/CLEAR, and STATUS restore their respective state independently. Trade/bar completeness remains uncertain for the affected interval even after a book has recovered.

### 8.9 SYSTEM — type 9

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 2 | u16 | code: 1 heartbeat, 2 info, 3 warning, 4 error |
| 50 | 2 | u16 | text_bytes: 0–4096 |
| 52 | 1 | u8 | severity: 0 info, 1 warning, 2 error |
| 53 | 3 | bytes | reserved |
| 56 | 8 | u64 | related_recovery_id: 0 or a prior GAP ID |
| 64 | variable | bytes | UTF-8 text followed by zero padding |

Instrument MUST be 0. Publisher 0 requires channel 0 and means container scope; a nonzero publisher means its declared publisher/channel scope. Heartbeat/info require severity 0; warning requires 1; error requires 2. A heartbeat requires no text and related ID 0. Diagnostics are descriptive and MUST NOT trigger automatic commands, state repair, or schema changes. SYSTEM error does not terminate a container; END status reports termination.

### Types 10–22: common rules

These thirteen types are new in revision 1.1. All integers are little-endian. Prices and quantities use the conventions of §3.3: `i64` or `u64` scaled by 10^-9, with nulls `INT64_MIN` and `UINT64_MAX`; counts use `UINT32_MAX`. Reserved bytes are zero. Text is UTF-8 without NUL. Text lengths count bytes, appear in the record as length fields, and the texts follow in the order of the length fields, then zero padding to a multiple of 8. A length outside the stated limit is invalid, and the limit is checked before a length is written. Unassigned enum values and unassigned flag bits are invalid.

| Type | Name | Record bytes | `required` | Header scope |
|---:|---|---:|---|---|
| 10 | VENUE_DEF | align8(96 + text) | producer choice | publisher ≠ 0, instrument = 0 |
| 11 | OPTION_DEF | align8(96 + text) | producer choice | publisher ≠ 0, instrument ≠ 0 |
| 12 | LISTING | align8(72 + text) | producer choice | publisher ≠ 0, instrument ≠ 0 |
| 13 | STATISTICS | 80 | producer choice | market record |
| 14 | OPTION_ANALYTICS | 120 | producer choice | market record; the definition's asset class is option |
| 15 | BOOK_DELTA | 72 | MUST be true | market record |
| 16 | IMBALANCE | 104 | producer choice | market record |
| 17 | SYMBOL_MAP | align8(72 + text) | producer choice | publisher ≠ 0, instrument ≠ 0 |
| 18 | TRADE_QUOTE | 120 | producer choice | market record |
| 19 | BEST_QUOTE | 112 | producer choice | market record |
| 20 | FRAME_SUMMARY | 104 | MUST be false | publisher 0, channel 0, instrument 0 |
| 21 | SECURITY_DEF | align8(216 + text) | producer choice | publisher ≠ 0, instrument ≠ 0 |
| 22 | CORPORATE_ACTION | align8(184 + text) | producer choice | publisher ≠ 0, instrument ≠ 0 |

A **market record** has publisher ≠ 0 and instrument ≠ 0, and needs an INSTRUMENT_DEF for the instrument earlier in byte order, as types 1–5 and 7 do. Types 10–12, 17, 21 and 22 are **reference records**: they need no earlier INSTRUMENT_DEF and do not replace one. A reference record with identity `(publisher, instrument)` replaces an earlier record of the same type and identity; the identity of each type is stated below.

### 8.10 VENUE_DEF — type 10

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | created_ns (null allowed) |
| 56 | 8 | u64 | updated_ns (null allowed) |
| 64 | 8 | u64 | expiry_ns (null when the venue has no expiry) |
| 72 | 1 | u8 | kind: 1 operating, 2 segment |
| 73 | 1 | u8 | status: 1 active, 2 updated, 3 expired |
| 74 | 2 | u16 | mic_bytes: exactly 4 |
| 76 | 2 | u16 | operating_mic_bytes: exactly 4 |
| 78 | 2 | u16 | country_bytes: exactly 2 |
| 80 | 2 | u16 | category_bytes: 0 or 4 |
| 82 | 2 | u16 | acronym_bytes: 0–64 |
| 84 | 2 | u16 | city_bytes: 0–128 |
| 86 | 2 | u16 | name_bytes: 1–255 |
| 88 | 2 | u16 | legal_entity_bytes: 0–255 |
| 90 | 2 | u16 | lei_bytes: 0 or 20 |
| 92 | 4 | bytes | reserved |
| 96 | variable | bytes | mic, operating_mic, country, category, acronym, city, name, legal_entity, lei, padding |

Identity is `(publisher, mic)`; a later record replaces the earlier one. `kind = 1` requires `mic == operating_mic`. MIC and country are uppercase ASCII letters or digits. Dates are midnight UTC of the source date.

### 8.11 OPTION_DEF — type 11

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | underlying_instrument_id (0 when the underlying has no ID in this namespace) |
| 56 | 8 | u64 | expiration_ns (non-null) |
| 64 | 8 | i64 | strike (non-null) |
| 72 | 8 | i64 | contract_multiplier (null when unknown; otherwise positive) |
| 80 | 1 | u8 | right: 1 call, 2 put |
| 81 | 1 | u8 | exercise_style: 0 unknown, 1 American, 2 European |
| 82 | 1 | u8 | settlement: 0 unknown, 1 physical, 2 cash |
| 83 | 1 | u8 | closing_type: 0 unknown, 1 normal hours, 2 late hours |
| 84 | 1 | u8 | option_flags: bit 0 pending, bit 1 adjusted (non-standard deliverable) |
| 85 | 3 | bytes | reserved |
| 88 | 2 | u16 | root_bytes: 1–16 |
| 90 | 2 | u16 | underlying_symbol_bytes: 0–255 |
| 92 | 2 | u16 | osi_symbol_bytes: 0 or 21 |
| 94 | 2 | u16 | currency_bytes: 0–16 |
| 96 | variable | bytes | root, underlying_symbol, osi_symbol, currency, padding |

Identity is `(publisher, instrument)`; a later record replaces the earlier one. `underlying_instrument_id = 0` requires a non-empty `underlying_symbol`. If an INSTRUMENT_DEF exists for the same instrument, its asset class MUST be option and its expiration, strike and underlying MUST equal this record's. A producer that does not know a fact uses "unknown"; it MUST NOT infer exercise style or settlement from the symbol.

### 8.12 LISTING — type 12

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 4 | u32 | round_lot (count; null allowed) |
| 52 | 1 | u8 | listing_flags: bit 0 ETF, bit 1 test issue, bit 2 NextShares |
| 53 | 1 | u8 | market_tier: 0 unspecified, 1 global select, 2 global, 3 capital |
| 54 | 1 | u8 | financial_flags: bit 0 reported, bit 1 deficient, bit 2 delinquent, bit 3 bankrupt |
| 55 | 1 | u8 | reserved |
| 56 | 2 | u16 | symbol_bytes: 1–255 |
| 58 | 2 | u16 | name_bytes: 0–512 |
| 60 | 2 | u16 | listing_mic_bytes: 0 or 4 |
| 62 | 2 | u16 | cqs_symbol_bytes: 0–255 |
| 64 | 2 | u16 | alt_symbol_bytes: 0–255 |
| 66 | 6 | bytes | reserved |
| 72 | variable | bytes | symbol, name, listing_mic, cqs_symbol, alt_symbol, padding |

Identity is `(publisher, instrument)`. `financial_flags` bits 1–3 require bit 0. Value 1 means normal; 0 means the source does not report financial status.

### 8.13 STATISTICS — type 13 (80 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | ts_ref: start of the session or date the value refers to (null allowed) |
| 56 | 8 | i64 | price |
| 64 | 8 | u64 | quantity |
| 72 | 2 | u16 | stat_type |
| 74 | 1 | u8 | action: 1 SET, 2 DELETE |
| 75 | 1 | u8 | stat_flags: bit 0 preliminary |
| 76 | 4 | u32 | reserved |

`stat_type`: 1 open, 2 high, 3 low, 4 close, 5 settlement, 6 VWAP (price types); 7 volume, 8 open interest (quantity types). SET of a price type requires non-null price and null quantity; SET of a quantity type the reverse. DELETE requires both null and flags 0. The latest SET per `(instrument, stat_type, ts_ref)` replaces earlier ones; DELETE withdraws it.

### 8.14 OPTION_ANALYTICS — type 14 (120 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | implied_volatility (annualised; 1.0 = 100%) |
| 56 | 8 | i64 | delta |
| 64 | 8 | i64 | gamma (per 1.00 move in the underlying) |
| 72 | 8 | i64 | theta (currency per calendar day) |
| 80 | 8 | i64 | vega (currency per 0.01 change in volatility) |
| 88 | 8 | i64 | rho (currency per 0.01 change in rate) |
| 96 | 8 | i64 | underlying_price |
| 104 | 8 | i64 | theoretical_price |
| 112 | 1 | u8 | price_basis: 0 unspecified, 1 mid, 2 last, 3 bid, 4 ask, 5 settlement |
| 113 | 1 | u8 | model: 0 unspecified, 1 Black-Scholes-Merton, 2 Black-76, 3 binomial, 4 other |
| 114 | 6 | bytes | reserved |

Every `i64` here is × 10⁻⁹ and independently nullable. Non-null implied volatility and gamma are ≥ 0. Non-null delta is within −1 to +1. At least one of the six analytics MUST be non-null. No floating point on the wire: a producer rounds to nine decimals and the wire value is authoritative. Each record replaces the previous analytics for the instrument.

### 8.15 BOOK_DELTA — type 15 (72 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | price |
| 56 | 8 | u64 | quantity: new aggregate size at this price |
| 64 | 4 | u32 | order_count (null allowed) |
| 68 | 1 | u8 | action: 1 SET, 2 DELETE, 3 CLEAR |
| 69 | 1 | u8 | side: 1 bid, 2 ask, 0 both (CLEAR only) |
| 70 | 1 | u8 | delta_flags: bit 0 LAST_IN_EVENT |
| 71 | 1 | u8 | reserved |

BOOK_DELTA mutates the aggregate book that BOOK_SNAPSHOT replaces. Levels are keyed by price, not by rank.

- SET: non-null price, quantity 1 … `UINT64_MAX − 1`. Adds the level or replaces its size and count.
- DELETE: non-null price, quantity 0, null count. The level must exist, unless the book is depth-limited.
- CLEAR: null price, quantity 0, null count. Empties one side, or the whole book when side is 0.
- The book is valid after a BOOK_SNAPSHOT or a CLEAR with side 0. A delta against an invalid book is a semantic error. GAP invalidates the book.
- A depth-limited snapshot leaves the book depth-limited until the next non-limited snapshot.
- `LAST_IN_EVENT` marks the last delta of one source event.
- A producer MUST NOT grow a side beyond 1024 levels, so the state can always be re-sent as one BOOK_SNAPSHOT.
- A transiently crossed book is not an encoding error.

### 8.16 IMBALANCE — type 16 (104 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | auction_ns: scheduled auction time (null allowed) |
| 56 | 8 | i64 | reference_price (non-null) |
| 64 | 8 | i64 | near_price: indicative price from auction and continuous interest (null allowed) |
| 72 | 8 | i64 | far_price: indicative price from auction interest only (null allowed) |
| 80 | 8 | u64 | paired_quantity (null allowed) |
| 88 | 8 | u64 | imbalance_quantity (non-null) |
| 96 | 1 | u8 | imbalance_side: 0 none, 1 buy, 2 sell |
| 97 | 1 | u8 | auction_type: 0 unspecified, 1 opening, 2 closing, 3 reopening, 4 IPO, 5 intraday |
| 98 | 6 | bytes | reserved |

`imbalance_side = 0` requires `imbalance_quantity = 0`, and the reverse. The record is informational: it changes no book or status state. Each record replaces the previous imbalance for the instrument.

### 8.17 SYMBOL_MAP — type 17

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | valid_from_ns (non-null) |
| 56 | 8 | u64 | valid_to_ns (null means open-ended; otherwise greater than valid_from_ns) |
| 64 | 1 | u8 | symbology: 1 native, 2 OSI, 3 ISIN, 4 FIGI, 5 root, 6 continuous |
| 65 | 1 | u8 | reserved |
| 66 | 2 | u16 | symbol_bytes: 1–255 |
| 68 | 4 | bytes | reserved |
| 72 | variable | bytes | symbol, padding |

The header instrument is the mapped instrument. The interval is half-open. For symbologies 1–4 and 6, intervals for one `(publisher, symbology, symbol)` MUST NOT overlap: a symbol names one instrument at any time. Symbology 5 (root) is one-to-many. One instrument may have many symbols.

### 8.18 TRADE_QUOTE — type 18 (120 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | price (non-null) |
| 56 | 8 | u64 | quantity (positive, non-null) |
| 64 | 8 | u64 | trade_id (0 when unknown) |
| 72 | 8 | i64 | bid_price |
| 80 | 8 | i64 | ask_price |
| 88 | 8 | u64 | bid_quantity |
| 96 | 8 | u64 | ask_quantity |
| 104 | 4 | u32 | bid_order_count |
| 108 | 4 | u32 | ask_order_count |
| 112 | 1 | u8 | aggressor: 0 unknown, 1 buyer, 2 seller |
| 113 | 1 | u8 | reserved |
| 114 | 2 | u16 | conditions: bit 0 off-book |
| 116 | 4 | u32 | reserved |

One trade print with the top of book immediately before it. Quote-side presence rules match QUOTE. It is a derived sampling record: it has no correction or cancel lifecycle, and it does not initialise or replace QUOTE state. A producer MUST NOT emit TRADE and TRADE_QUOTE for the same prints on one channel.

### 8.19 BEST_QUOTE — type 19 (112 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | i64 | bid_price |
| 56 | 8 | i64 | ask_price |
| 64 | 8 | u64 | bid_quantity |
| 72 | 8 | u64 | ask_quantity |
| 80 | 4 | u32 | bid_order_count |
| 84 | 4 | u32 | ask_order_count |
| 88 | 4 | u32 | quote_flags: bit 0 indicative |
| 92 | 4 | u32 | bid_publisher_id (0 when the side is absent or the venue is unknown) |
| 96 | 4 | u32 | ask_publisher_id (same rule) |
| 100 | 4 | u32 | reserved |
| 104 | 8 | u64 | interval_ns: 0 event-driven; otherwise a sample taken at the interval end |

Best bid and offer with the venue that set each side, and optional interval sampling. Presence rules match QUOTE. Non-zero venue IDs MUST be declared publishers. With `interval_ns > 0`, `ts_event` equals the interval end. BEST_QUOTE keeps its own state and does not replace QUOTE state.

### 8.20 FRAME_SUMMARY — type 20 (104 bytes)

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | data_frame_seq |
| 56 | 8 | u64 | data_frame_offset, absolute from container byte 0 |
| 64 | 4 | u32 | stored_bytes |
| 68 | 1 | u8 | codec |
| 69 | 1 | u8 | summary_flags: bit 0 frame has a null ts_event; bit 1 non-null ts_event is non-decreasing within the frame |
| 70 | 2 | u16 | reserved |
| 72 | 8 | u64 | type_mask: bit n (1–63) set when standard type n is present; bit 0 set when any other type is present |
| 80 | 8 | u64 | min_instrument_id over non-zero instrument IDs (0 when none) |
| 88 | 8 | u64 | max_instrument_id (0 when none) |
| 96 | 8 | u64 | reserved |

The richer index, carried as ordinary optional records so that a 1.0 reader skips it.

- Header: publisher 0, channel 0, instrument 0, both timestamps null. Sequence continues the system scope.
- If present, FRAME_SUMMARY records fill one or more trailing DATA frames that contain nothing else ("summary frames").
- Together they describe every non-summary DATA frame exactly once, in ascending frame order, with values equal to the real frames.
- A reader finds them from END → INDEX → last DATA frame, walking backwards while a frame's first record is type 20.
- A validator checks every value against a full scan. A summary that disagrees with the file is an error.

### 8.21 SECURITY_DEF — type 21

Security-master record: one listing of one security, with its identifiers. Header: publisher ≠ 0, instrument ≠ 0 (the listing). `ts_event` is when the facts became effective. A reference record; `required` is the producer's choice. Record bytes: align8(216 + text).

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | listing_group_id (0 none) |
| 56 | 8 | u64 | security_id (0 none) |
| 64 | 8 | u64 | issuer_id (0 none) |
| 72 | 8 | u64 | listing_created_ns (null allowed) |
| 80 | 8 | u64 | listing_ns (null allowed) |
| 88 | 8 | u64 | delisting_ns (null allowed) |
| 96 | 8 | u64 | shares_outstanding: whole shares, not × 10⁻⁹ (null allowed) |
| 104 | 8 | u64 | shares_outstanding_ns (null allowed) |
| 112 | 8 | u64 | lot_size (quantity; null allowed) |
| 120 | 8 | i64 | par_value (price; null allowed) |
| 128 | 8 | i64 | votes_per_share (× 10⁻⁹; null allowed) |
| 136 | 8 | u64 | cik (0 none) |
| 144 | 4 | u32 | sic (0 none) |
| 148 | 4 | u32 | naics (0 none) |
| 152 | 1 | u8 | listing_source: 0 unknown, 1 main, 2 secondary |
| 153 | 1 | u8 | security_flags: bit 0 multi-currency |
| 154 | 2 | bytes | reserved |
| 156 | 60 | u16 × 30 | text lengths, in the order below |
| 216 | variable | bytes | the 30 texts, then padding |

Texts and limits (bytes): issuer_name 0–255, description 0–255, security_type 0–8, structure 0–8, listing_status 0–8, voting 0–8, primary_exchange 0–16, exchange 0–16, operating_mic 0 or 4, segment_mic 0 or 4, segment_name 0–128, symbol 0–255, alt_symbol 0–255, local_code 0–255, isin 0 or 12, cusip 0 or 9, composite_figi 0 or 12, composite_ticker 0–32, figi 0 or 12, figi_ticker 0–32, fisn 0–35, lei 0 or 20, cfi 0 or 6, cic 0–8, gics 0–8, incorporation_country 0 or 2, listing_country 0 or 2, register_country 0 or 2, trading_currency 0–16, par_value_currency 0–16.

`security_type`, `structure`, `listing_status` and `voting` are short producer-defined codes, like currency in INSTRUMENT_DEF; systems exchanging them must agree on the code set. Identity is `(publisher, instrument)`; a later record replaces the earlier one. `shares_outstanding` is a whole count because large issuers exceed the × 10⁻⁹ quantity range.

### 8.22 CORPORATE_ACTION — type 22

One corporate-action event for one listing. Header: publisher ≠ 0, instrument ≠ 0 (the listing). `ts_event` is the event date. A reference record; `required` is the producer's choice. Record bytes: align8(184 + text).

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 48 | 8 | u64 | security_id (0 none) |
| 56 | 8 | u64 | issuer_id (0 none) |
| 64 | 8 | u64 | created_ns (null allowed) |
| 72 | 8 | u64 | effective_ns (null allowed) |
| 80 | 8 | u64 | ex_ns (null allowed) |
| 88 | 8 | u64 | record_ns (null allowed) |
| 96 | 8 | u64 | payment_ns (null allowed) |
| 104 | 8 | u64 | record_date_id (0 none) |
| 112 | 8 | u64 | outturn_security_id (0 none) |
| 120 | 8 | i64 | ratio_old (× 10⁻⁹; null allowed) |
| 128 | 8 | i64 | ratio_new (× 10⁻⁹; null allowed) |
| 136 | 4 | u32 | option_id (null allowed) |
| 140 | 4 | u32 | serial_id (null allowed) |
| 144 | 1 | u8 | action_flags: bit 0 default option |
| 145 | 3 | bytes | reserved |
| 148 | 30 | u16 × 15 | text lengths, in the order below |
| 178 | 6 | bytes | reserved |
| 184 | variable | bytes | the 15 texts, then padding |

Texts and limits (bytes): event 1–8, subtype 0–16, action 0–8, status 0–8, participation 0–8, payment_type 0–8, fraction 0–8, date_label 0–32, related_event 0–8, related_event_id 0–32, event_id 1–32, unique_id 1–48, rate_currency 0–16, outturn_isin 0 or 12, details 0–65535.

- `event`, `subtype`, `action`, `status`, `participation`, `payment_type` and `fraction` are short producer-defined codes.
- `details` is empty or one UTF-8 JSON object with sorted keys. It carries event-specific terms that have no fixed field (extra dates, rates, tender limits, further outturn identifiers). A reader MUST NOT need `details` to interpret the fixed fields.
- Identity is `(publisher, unique_id)`. A later record with the same `unique_id` replaces the earlier one.
- Listing facts (issuer name, symbols, ISIN and so on) are not repeated here. They are carried by a SECURITY_DEF for the same instrument.

## 9. Ordering, gaps, snapshots, and replay

Byte order is authoritative delivery order. Frame order and record order MUST be preserved. Timestamps can move backward. Channel sequences do not define an exchange-wide total order across channels. A merge tool MUST choose and document its ordering policy and assign new container/record identities.

A market-data consumer begins with unknown books and status. QUOTE initializes top-of-book state. BOOK_SNAPSHOT initializes aggregate state, and BOOK_DELTA (§8.15) then changes it one price level at a time. BEST_QUOTE and TRADE_QUOTE keep their own state and do not replace QUOTE state. MBO must begin with CLEAR or a completed snapshot for each book; ADD alone cannot prove initial completeness.

MBO snapshot transaction:

1. SNAPSHOT_BEGIN starts a private empty working book for that instrument. Nested begins are invalid.
2. Subsequent MBO records for that book MUST be ADD until SNAPSHOT_END. IDs must be unique in the working book. Other instruments and unrelated schema records may interleave.
3. SNAPSHOT_END commits the complete working book atomically and marks MBO state valid. Empty snapshots are allowed.
4. GAP for the channel, EOF, or END while a snapshot is open aborts it. A completed container with any open snapshot is semantically invalid. A GAP discards the working snapshot and marks the book invalid; later stray SNAPSHOT_END is invalid.

Snapshots may cross DATA frames. A reader MUST NOT expose the working snapshot as a complete book. A configured snapshot-size limit may stop decoding with a resource-limit error rather than silently publishing partial state.

After a GAP, MBO changes without CLEAR/SNAPSHOT_BEGIN cannot restore state; semantic consumers MUST report them as unavailable for reliable reconstruction. Producers MUST send CLEAR or a complete snapshot before resuming ordinary MBO changes. A recovery snapshot establishes state at its source snapshot point; it does not recover missing trade history. The producer is responsible for reconciling source updates around that point before outputting the normalized stream.

Framing loss and source loss are distinct. A missing NWT frame or normalized sequence is a damaged/incomplete transfer and MUST fail strict decoding. A well-formed GAP reports source loss within an otherwise intact transfer. No consumer may silently turn damaged bytes into a trusted GAP record.

For byte-identical transport retries, deduplication keys are `(stream_id, frame_seq)` or `(stream_id, publisher, channel, sequence)`. Reusing an identity with different bytes is an integrity/protocol error. Across independently generated containers, these keys do not identify the same market event; applications need source-specific identity to deduplicate.

## 10. Compression and integrity

### 10.1 CRC32C

All CRC fields use CRC-32C/Castagnoli: width 32, polynomial `0x1EDC6F41`, reflected implementation polynomial `0x82F63B78`, initial value `0xFFFFFFFF`, reflected input/output convention, final XOR `0xFFFFFFFF`. Store the result as a little-endian u32. The check value for ASCII `123456789` is `0xE3069283`; empty input yields zero. CRC is error detection, not authentication. [CRC32C reference, RFC 3720 Appendix B.4](https://www.rfc-editor.org/rfc/rfc3720.html#appendix-B.4).

Container and frame header CRCs cover the entire respective 64-byte header with only their own CRC field set to zero. Metadata CRC covers every metadata byte including TLV padding. Payload CRC covers exactly the raw payload, excluding outer frame padding. CRCs are mandatory even if zero happens to be the calculated value. There is no “CRC absent” convention.

### 10.2 Codec 1: Zstandard

The stored payload MUST contain exactly one ordinary Zstandard frame, conforming to RFC 8878, with no dictionary, no skippable frames, no concatenated frame, and no trailing bytes. A content size MUST be present and equal `raw_bytes`; the window size MUST be at most 16,777,216 bytes. Zstd's own content checksum is optional; NWT CRC remains mandatory. The decompressor MUST consume exactly `stored_bytes`. [Zstandard format, RFC 8878](https://www.rfc-editor.org/rfc/rfc8878.html).

The frame header descriptor (RFC 8878, section 3.1.1.1.1) is checked before the library is called. Bits 7–6 select the content-size field and bit 5 the single-segment flag. Bit 3 is reserved and MUST be zero. Bit 2, the content-checksum flag, is allowed; the optional Zstd checksum is not required, and when present it is checked by the library. Bits 1–0 flag a dictionary ID and MUST be zero. The content size MUST be present and equal `raw_bytes`. The window size (or the content size, for a single-segment frame) MUST NOT exceed 16,777,216 bytes. The stored payload MUST be exactly one frame: the size of the first frame found by the library equals `stored_bytes`, so a skippable frame before or after it, a second frame, and trailing bytes are all rejected. Codec 1 is allowed on DATA frames only.

A reader without a Zstd library reads raw frames normally. For a codec-1 frame it fails with an error that says the library is not available. The header check runs first, so a malformed Zstd header is rejected even without the library.

Compression level is an encoder choice and not a decoder requirement. Independent frames cannot depend on earlier dictionary or compression state. Readers MUST enforce output/window limits before and during decompression. A writer stores a frame with codec 1 only when the compressed payload is smaller than the raw payload; otherwise it uses codec 0. Both codecs may appear within one container. Compressed bytes differ between library versions, so two conforming writers need not produce the same bytes; compare decoded records, not compressed bytes.

No compression ratio or latency target is asserted by this specification. Extremely small batches may cost more to compress than they save.

## 11. Index, summaries, store profile and end-of-stream

### 11.1 INDEX payload

An INDEX payload consists of one or more 40-byte entries, without an entry-count prefix. Entry count is `raw_bytes / 40`; the size MUST be a positive multiple of 40. Each entry is:

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 0 | 8 | u64 | data_frame_seq |
| 8 | 8 | u64 | data_frame_offset, absolute from container byte 0 |
| 16 | 8 | u64 | min_event_ns |
| 24 | 8 | u64 | max_event_ns |
| 32 | 4 | u32 | raw_bytes |
| 36 | 4 | u32 | record_count |

If any INDEX frames exist, their concatenated entries MUST enumerate every DATA frame exactly once in ascending frame sequence order, with values identical to the referenced headers. There may be multiple INDEX frames to respect size limits. No entry may refer to metadata, an INDEX, END, or bytes outside the container. Empty containers MUST NOT contain INDEX frames.

The index accelerates selecting candidate frames; it is not a complete state checkpoint. Timestamp ranges may overlap or go backward. Binary search by timestamp is invalid unless a separate verified monotonicity condition is established, such as a manifest `ordering` of `ts_event` (§5.2) that a validator has checked. A general reader examines all index ranges and reads selected frames in original order. Null-timestamp policies require explicit handling; frame bounds alone cannot identify all null-bearing frames.

Seeking to a trade or quote still requires the applicable earlier instrument definitions. MBO requires an earlier complete snapshot or CLEAR plus all subsequent updates. A consumer seeking without that context MUST label results as raw/partial and MUST NOT claim a reconstructed valid book. This version provides no definition or book-checkpoint index. FRAME_SUMMARY (§11.3) adds per-frame type and instrument ranges, but it does not carry state.

### 11.2 END payload

END has a 32-byte uncompressed payload and therefore a total size of exactly 96 bytes:

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 0 | 8 | u64 | first_index_offset, or 0 when absent |
| 8 | 8 | u64 | total_data_frames |
| 16 | 8 | u64 | total_records in DATA frames |
| 24 | 4 | u32 | completion_status: 0 normal; 1 producer-aborted |
| 28 | 4 | u32 | reserved |

Counts include optional unknown records and MUST match the container. `first_index_offset`, if nonzero, MUST identify the first INDEX frame, and all subsequent frames before END MUST be INDEX frames. END frame sequence equals the number of preceding DATA and INDEX frames.

A seekable reader MAY read the last 96 bytes to discover the index. It MUST validate END and all referenced bounds; this shortcut alone does not validate the file contents or completeness of the index. A strict full validator compares counts, sequences, entries, and payloads against a sequential scan.

Normal END means the producer intentionally completed this container; it does not certify a source without GAPs. Aborted END preserves a structurally complete prefix and explicitly reports unsuccessful completion. No bytes, including another container, may follow END in a single NWT object. Concatenation requires an external bundle format or separate objects.

EOF without END is incomplete, even if it occurs exactly on a frame boundary. Readers may expose a verified prefix only with an explicit incomplete result. An active live connection naturally has no END yet and remains in-progress. A clean transport close alone does not replace END.

### 11.3 FRAME_SUMMARY records

INDEX gives each frame's time range. FRAME_SUMMARY (type 20, §8.20) adds the frame's offset, stored size, codec, the set of record types it holds and its range of instrument IDs. It is carried as ordinary optional records, so a reader that does not know type 20 skips it and the container stays valid for a 1.0 reader.

- A summary record has publisher 0, channel 0, instrument 0 and both timestamps null. Its `sequence` continues the sequence of the system scope (publisher 0, channel 0).
- If a container has FRAME_SUMMARY records, they fill one or more trailing DATA frames, called summary frames, that contain nothing else. Summary frames are DATA frames: INDEX entries and the END counts include them.
- Together the summary records describe every non-summary DATA frame exactly once, in ascending frame order, with values equal to the real frames.
- A reader finds them from END to INDEX to the last DATA frame, then walks backwards while the first record of a frame is type 20.
- A validator checks every value against a full scan. A summary that disagrees with the file is an error.

A reader can use the summaries to skip a frame without reading it: when the frame's `type_mask` lacks the wanted type, or when the wanted instrument ID lies outside `[min_instrument_id, max_instrument_id]`, or when the INDEX time range does not overlap the query.

### 11.4 Store profile

There is no separate store format. A **store file** is a normal container written with these choices:

| Choice | Setting | Reason |
|---|---|---|
| Frame size | 1 MiB raw by default, up to the 16 MiB limit | Fewer headers, better compression |
| Codec | Zstd, with codec 0 for a frame that does not shrink | File size and read speed |
| INDEX | Always written | Seek by time |
| FRAME_SUMMARY | Always written | Skip frames by type and instrument without reading them |
| `ordering` | Declared in the manifest when it is true | Makes binary search by time valid |

Records are never reordered. Byte order is the delivery order, and definitions, snapshots and trade lifecycles depend on it. A tool that re-frames or recompresses a file keeps the record order and gives the new file a new stream ID. It declares an `ordering` only when the input already has it.

To answer a query from a store file, a reader:

1. reads the last 96 bytes (END) and validates it;
2. reads the INDEX frames that END points to;
3. reads the summary frames, found as described in §11.3;
4. chooses frames by time range, type mask and instrument range;
5. reads only the chosen frames, in their original order.

The reader needs one primitive, “read N bytes at offset X”. The same code therefore works on a local file, on object storage with range requests, and on any other source with that primitive. Results of a seek are partial in the sense of §11.1: earlier definitions and book state may be missing, and the reader MUST label them so.

## 12. Transport and recovery

### 12.1 Reliable byte streams

For TCP, TLS, or a reliable QUIC stream, send one container header, metadata, then frames. Message boundaries are not provided by the underlying byte stream: a read may contain one byte, part of a header, multiple records, or many frames. The decoder MUST support arbitrary fragmentation and coalescing.

Connection establishment, credentials, requested datasets/schemas, and codec capability agreement occur in the hosting service's control plane before NWT bytes begin. this version does not define a socket handshake or subscription message. An API MUST document its authentication, request syntax, quotas, retry policy, and allowed codecs separately. A producer MUST NOT send an unsupported codec after agreeing to a restricted capability set.

For an HTTP response, use the NWT object as the body and the private media type above when appropriate. Native NWT frame compression SHOULD be used without an additional HTTP compression wrapper when byte offsets/range access matter. Object storage is the same byte representation.

### 12.2 Backpressure and heartbeat

Producers SHOULD bound queues and flush on either a configured batch-size or latency threshold. A heartbeat is an ordinary SYSTEM record in a DATA frame; it consumes a record sequence and a frame sequence. Its interval and timeout are service policies, not inferred from NWT.

A producer that loses source data due to overflow MUST report GAP before resuming affected records, or terminate abnormally. It MUST NOT hide dropped events behind contiguous output sequence numbers. If backpressure blocks transmission, a heartbeat may also be delayed; heartbeat silence alone does not diagnose the cause.

### 12.3 Resume and byte ranges

Exact resume is allowed only against an immutable container with the same stream ID and verified header/metadata. A client records the byte offset and frame sequence after the last fully verified frame. The service may resume at that frame boundary and preserve original bytes and sequences. This resumed suffix is a transport continuation, not a standalone NWT object, and requires the client's previously validated context.

A standalone export starting at a later logical time MUST be a new container with a new stream ID, a new manifest, sequences starting at their initial values, and required definitions/snapshots/lifecycle context. An API providing semantic resume MUST define its source cursor and gap policy separately; NWT 1.1 does not standardize that cursor.

Retransmission does not deliver exactly-once application side effects by itself. Applications must durably coordinate processed positions with their own state/transactions.

### 12.4 Damaged archives

Strict readers stop at corruption. A separate salvage mode MAY scan forward for frame magic, validate candidate headers, bounds, decompression, checksums, and record structure, and recover later raw records. Magic matches alone are insufficient. Salvage output MUST use a new container ID, describe omitted regions, and restore semantic prerequisites or remain explicitly partial. A CRC-valid frame cannot reconstruct state lost before it.

## 13. Schema evolution and registries

Container major version changes permit incompatible envelope changes. Readers MUST reject unknown major versions. Minor versions may add TLV allocations or record schemas while preserving the 64-byte headers and all existing meanings. Minor 1 adds types 10–22 and nothing else. A 1.0 reader MAY read a minor 1 container only when every envelope field retains a supported value and every required TLV and schema is understood; it skips optional records it does not know. A container that declares BOOK_DELTA as required is therefore refused by a 1.0 reader, which is the intended effect. A strict implementation MAY instead reject unknown minor versions with a clear unsupported-version error.

Existing `(record_type, schema_version)` layouts and meanings are immutable. New fields require a new schema version; changed meanings require a new version or new type. Schema versions are complete contracts, not promises of prefix compatibility. Readers MUST NOT guess that an unknown version has the old layout. Enum extensions likewise require a schema revision where they affect meaning.

Record type allocation: 0 invalid, 1–32767 standard, 32768–65534 private, 65535 invalid. Types 1–22 are assigned here, as in the table of §8. Private types are scoped by their exact manifest URI; applications exchanging them MUST agree on both the URI and layout. A container cannot bind the same `(type,version)` to multiple schemas. Registry governance must assign any future public IDs before release; this draft establishes no external standards authority.

Unknown optional record types/versions are skipped by `record_bytes` after envelope and manifest validation. Unknown required schemas stop semantic decoding before DATA is consumed. All skipped records still contribute to sequence checking, frame counts, and timestamp bounds. A lossless relay preserves their bytes. Optional schemas MUST NOT redefine existing units, mutate standard books, or otherwise be prerequisites for standard interpretation; such dependencies require `required = true`.

## 14. Decoder and encoder requirements

### 14.1 Incremental decoder state machine

```text
READ_HEADER -> validate header CRC/version/limits
READ_METADATA -> validate metadata CRC/TLVs/manifest
READ_FRAME_HEADER -> validate header CRC/kind/order/limits
READ_PAYLOAD -> obtain exactly stored_bytes plus outer padding
DECOMPRESS -> codec-specific bounded decode
VALIDATE_PAYLOAD -> CRC, records/index/end, semantic prerequisites
COMMIT_FRAME -> expose validated records, advance expected sequences
repeat READ_FRAME_HEADER until END
DONE -> reject trailing bytes
```

Temporary lack of bytes returns NEED_MORE, not corruption. End-of-input while expecting more bytes returns TRUNCATED. No record from a frame may be presented as integrity-verified before that frame's CRC and structural validation succeed. A semantic consumer SHOULD validate mutations against temporary state and commit only after the complete frame passes semantic checks. Open multi-frame snapshots remain private until SNAPSHOT_END.

Record iteration pseudocode:

```text
offset = 0; parsed = 0
while offset < raw_bytes:
    require raw_bytes - offset >= 48
    n = read_u32_le(payload, offset)
    require 48 <= n <= 1048576 and n % 8 == 0
    require n <= raw_bytes - offset
    validate_common_header(payload[offset:offset+n])
    validate_declared_schema_or_skip_optional(...)
    offset += n; parsed += 1
require offset == raw_bytes and parsed == record_count
```

This is explanatory pseudocode, not a complete validator; CRCs, scopes, limits, reserved fields, timestamps, and state rules remain mandatory.

### 14.2 Error classification

Implementations SHOULD expose stable machine-readable categories: `BAD_MAGIC`, `UNSUPPORTED_VERSION`, `UNSUPPORTED_CODEC`, `UNSUPPORTED_REQUIRED_SCHEMA`, `INVALID_METADATA`, `BAD_HEADER_CRC`, `BAD_PAYLOAD_CRC`, `INVALID_LENGTH`, `NONZERO_RESERVED`, `INVALID_RECORD`, `SEQUENCE_ERROR`, `SEMANTIC_ERROR`, `DECOMPRESSION_ERROR`, `RESOURCE_LIMIT`, `TRUNCATED`, `ABORTED`, and `TRAILING_BYTES`.

Errors SHOULD include byte offset, frame sequence, record position, and schema when known. Logs MUST NOT treat untrusted text as format strings or commands. A reader may provide raw inspection despite unsupported semantics, but MUST mark that mode and its limitations explicitly.

### 14.3 Encoder obligations

Writers MUST validate schema constraints before emission, use checked integer arithmetic, zero all reserved bytes, compute exact counts and timestamp bounds, compute raw-payload CRCs before optional compression, and compute header CRCs last. Writers SHOULD prefer deterministic serialization for repeated conversion runs, though fresh stream IDs and creation times naturally differ.

An encoder cannot change the manifest after it has been sent. New publishers or schemas require a new container. It MUST emit definitions and state initialization before dependent data. A writer that cannot finish SHOULD emit an aborted END if possible; otherwise readers will classify the prefix as incomplete. Published files SHOULD be written to a temporary path, completed and flushed, then atomically renamed according to the host filesystem's guarantees.

## 15. Security and operational limits

NWT has no built-in encryption, digital signature, entitlement enforcement, or tamper-resistant authentication. Use authenticated encrypted transport and appropriate object access controls. If stored-object authenticity is required, sign or authenticate the complete immutable object externally. CRCs do not protect against intentional modification.

Hard format limits are 1 MiB metadata, 16 MiB stored/raw frame payload, 1 MiB record, 1024 aggregate book levels per side (for BOOK_SNAPSHOT, and for the book that BOOK_DELTA maintains), and the individual text/array limits specified above, including 65535 bytes for the `details` text of CORPORATE_ACTION. These are ceilings, not suggested allocation sizes. Readers MAY enforce lower documented local limits and return RESOURCE_LIMIT. They MUST NOT silently drop data to stay within a limit.

Total container length, number of frames, instruments, channels, live orders, and correction histories are not globally bounded by the format. Stateful consumers MUST apply configurable quotas, bounded buffering, disk-backed state, or explicit resource failures. Never allocate from an unchecked product or addition. Enforce decompressor window/output limits before materializing output. Do not dereference URI metadata or load executable schema plugins automatically.

CRC validation does not establish business-data correctness. Negative prices, crossed books, stale timestamps, and unusual but permitted values may be legitimate. Validation must distinguish malformed encoding from a source-quality alert.

## 16. Interoperability and conversion

Data in another format needs an explicit converter. Broad concepts such as instrument identity, event time, receive time, prices and message types can be mapped, but sizes, type IDs, flags, sequence meanings, metadata and framing MUST NOT be copied by assumption. The converter's author reads the source format's own definition for every field they map.

| Input concept | NWT treatment |
|---|---|
| Publisher/instrument identity | Allocate stable IDs; keep the mapping in converter metadata or reference data. Where the source has numeric IDs, keep their numbers |
| Event and receive timestamps | Convert clock semantics; map source nulls to NWT nulls |
| Fixed-point or decimal price | Parse with integer arithmetic and rescale with checked arithmetic and exactness checks |
| Integer/fractional size | Convert to quantity × 10^9 in an explicitly defined unit |
| Exchange-native sequence | Do not copy into the NWT output sequence; retain in a private schema or in `details` if needed |
| Feed action and flags | Map only when the meaning matches; otherwise reject, or count the loss in provenance |
| Order-level feed | Track each order and emit ADD, MODIFY or DELETE with the remaining size |
| Multi-level book update | Rebuild an aggregate snapshot, or emit BOOK_DELTA (§8.15) |
| Native instrument definition | Populate the available fields; keep other necessary fields in a private schema |
| Symbol directory or security master | Use LISTING, SYMBOL_MAP, SECURITY_DEF and VENUE_DEF; do not guess a field the source lacks |
| Late correction outside the export range | Include the original lifecycle context, or reject the standard TRADE conversion |

A converter MUST NOT claim lossless conversion unless every required source field and semantic distinction is retained. It fails, and does not guess, on an unknown source code. It fails, and does not truncate, on a text that exceeds a limit. It never reorders records. It parses and prints decimals with integer arithmetic; no floating-point value enters a conversion. When it rounds, it reports the loss to the caller and records the policy and the count in provenance. Provenance records the chosen policy; it cannot make a lossy conversion lossless.

Source codes that the converter keeps as text, for example status and action letters, stay text codes. A schema does not turn them into enums until the code set is defined. Facts that the source does not have stay “unknown”; they are not filled in from other fields.

CSV/JSON exports SHOULD render timestamps as integer decimal strings or unambiguous time strings, and prices/quantities as exact decimal strings. JavaScript numbers cannot represent all u64/i64 values exactly; implementations SHOULD use BigInt or a lossless integer library. A reverse converter MUST validate ranges and nulls, not round via floating-point intermediates. The kit's own text output formats are defined in `fixtures/v1.1/FORMAT-NOTES.md`.

## 17. Examples and binary test vectors

The accompanying fixture package provides one complete uncompressed market-data container, byte-level hex dumps, a values/offsets manifest, and a small executable vector generator/checker. It contains a definition followed by a trade, an index, and a normal END. The fixture is an interoperability aid for this draft, not a production SDK or comprehensive semantic validator.

Revision 1.1 adds two kinds of file. The synthetic conformance vectors (`fixtures/catalog-v1.1.json` and `fixtures/v1.1/`) cover every field of all 22 types, so the four codecs can be compared byte for byte. The real-data fixtures (`fixtures/real/`, `fixtures/real-market/`, `fixtures/real-reference/`) are converted from public and licensed source files and show what real records look like. The cookbook uses real records where one exists.

TRADE example values:

| Field | Value |
|---|---|
| publisher/channel/instrument | 1 / 0 / 1001 |
| sequence | 2, following an instrument definition at sequence 1 |
| ts_event | 1700000000000000000 |
| ts_recv | 1700000000000000100 |
| price | 123450000000 = 123.45 USD |
| quantity | 10000000000 = 10 shares |
| trade_id / original_sequence | 42 / 0 |
| action / aggressor | NEW / buyer |

The 48-byte common record header can be expressed in Python's explicit little-endian syntax as `struct.Struct('<IHBBIIQQQQ')`. This is a serialization description, not permission to use native structure layout without checking it. The full TRADE payload suffix is `'<qQQQBBHI'`. The fixture checker asserts the exact 48/40/88-byte sizes and CRC check value.

For language interoperability, a C/C++ implementation SHOULD read with explicit little-endian accessors or copy into validated aligned storage. A Rust implementation MUST account for unaligned input and byte order rather than casting arbitrary byte slices to references. A Python implementation can use `struct.unpack_from` after bounds validation.

## 18. Conformance test plan

Before describing an implementation as production-ready, run independent encoder/decoder round trips and the following cases. The accompanying checker covers a subset of envelope/vector checks; this matrix is a release requirement, not a claim that all tests already exist.

| Area | Required cases and expected result |
|---|---|
| Golden vectors | Decode fixture values; reproduce exact fixture bytes with its fixed ID/time |
| Fragmentation | Every split of header and short fixture, single-byte reads, many frames/read; identical events |
| Primitive values | Negative/zero prices, epoch/null times, maximum legal integers; exact values |
| CRC | Known check vector; altered header/metadata/raw payload rejected |
| Lengths | Too short/long, overflow, misalignment, count mismatch, trailing bytes rejected |
| Padding | Nonzero TLV, record, or frame padding rejected |
| Metadata | Duplicate keys/types, unknown required TLV/schema, undeclared publisher/type rejected |
| Evolution | Unknown optional record skipped and counted; unknown required version rejected |
| Compression | Raw/Zstd/mixed; dictionary, excess window, concatenation, extra bytes, wrong output size rejected |
| Index | Bad offset, missing/duplicate entry, mismatch, illegal ordering rejected |
| Completion | Normal/aborted END distinguished; missing/truncated END reported incomplete |
| Sequencing | Cross-frame continuity; duplicate/gap/wrap rejected; channel independence maintained |
| Trades | New/correct/cancel lifecycle; missing originals and updates after cancel rejected |
| Quotes/books | Empty/crossed quotes accepted; invalid absence encoding/rank duplicates rejected |
| MBO | Clear/add/modify/delete; multi-frame snapshot atomicity; nested/unfinished snapshot rejected |
| Source gaps | Each state invalidated; recovery restores only corresponding schema state |
| Definitions | Before-use rule, updates, immutable unit identity, private fields preserved |
| Resource limits | Declared oversized values rejected before allocation; bounded decompression/state |
| New types (10–22) | Every field, enum, flag mask and reserved field; text limits counted in bytes (a 255-byte limit accepts 127 two-byte characters plus one ASCII byte and rejects one more); exact fixed sizes; wrong text lengths rejected |
| Container minor | `minor` 1 with types 10–22 declared; `minor` 0 otherwise; a mismatch in either direction rejected, including a file that declares only types 1–9, 21 and 22 |
| Zstd header | Frame with content checksum accepted; dictionary, skippable frame, trailing bytes, wrong content size and oversized window rejected; missing library reported without affecting raw frames |
| Summaries and ordering | A FRAME_SUMMARY that disagrees with a full scan rejected; a false `ordering` claim rejected; a query answered from summaries equals a full scan with the same filter |
| Book deltas | Delta on an invalid book, delete of a missing level, growth past 1024 levels, and GAP invalidation |
| Reference and market extras | STATISTICS null rules, IMBALANCE side/quantity, overlapping SYMBOL_MAP intervals, OPTION_DEF against INSTRUMENT_DEF, replacement by identity for types 10–12, 21 and 22 |
| Text output | CSV and JSON escaping of a text with `,`, `"`, a line feed and a control byte, identical in every language |
| Fuzzing | Truncated/random/mutated inputs cannot crash, hang, read out of bounds, or allocate without bounds |

Interoperability sign-off SHOULD include two independently developed implementations, preferably in different languages, using both positive and deliberately malformed fixtures. Re-encoding with another compressor need not produce identical compressed bytes; decoded raw records and metadata semantics must agree. Byte-identical retries, however, must retain original compressed bytes.

## 19. Performance and implementation guidance

Uncompressed TRADE is 88 bytes; QUOTE is 96; BAR is 112; MBO is 88. A raw frame of 1000 trades is 88,064 bytes, excluding container metadata and index. Frame-header overhead is 64/88,000, approximately 0.073%. A single-trade frame is 152 bytes, approximately 72.7% envelope overhead relative to its 88-byte record. These are layout calculations, not benchmarks.

Batch sizes of 64 KiB–1 MiB raw are reasonable starting experiments for bulk transfer; live systems should tune a latency-triggered flush policy. Measure rather than assume the best compression level or batch size. Metadata JSON is parsed once per container; the hot record path uses fixed binary layouts.

Uncompressed buffers can support views without copying payload fields when ownership, lifetime, alignment, and endianness are safe. Compressed frames require decompression storage. CRC and validation still cost CPU. “Zero-copy” does not mean zero validation, zero memory use, or zero buffering.

Benchmark records/second, bytes/second, CPU time, peak memory, compression ratio, and end-to-end p50/p95/p99 latency. Report hardware, compiler/runtime, codec version/level, batch policy, schema mix, checksum policy, and whether semantic book reconstruction is enabled. Include incompressible and adversarially large inputs. A comparison with any other format must use equivalent data, fidelity, and processing work. This specification states no measured speed or size. Measurements made for the developer kit are reported in [VERIFICATION.md](VERIFICATION.md) with their hardware and settings.

## 20. Release acceptance and future work

This document is a complete proposed v1.1 wire contract for the stated scope, but production adoption still requires implementation and interoperability review. Freeze an immutable specification revision and fixture checksums before shipping a public SDK. Resolve any discovered ambiguity by publishing an explicit draft revision; never silently change already-released wire meanings.

Suggested implementation order: envelope and CRC; metadata and raw records; standard schema semantics; index/END; bounded Zstd; incremental streaming and resume integration; fuzzing and independent interoperability tests. Public APIs should expose raw record access alongside typed decoding and clearly distinguish a valid container from complete source-market history.

Future versions may define authenticated containers, dictionary compression, source-cursor replay, book-state checkpoints, cross-container corrections, datagram transport, alternative decimal scales, and dynamically extensible metadata. None of those features is implicitly supported by this draft.

## 21. References

The RFC references were consulted on 23 September 2026.

1. [RFC 8878 — Zstandard Compression](https://www.rfc-editor.org/rfc/rfc8878.html).
2. [RFC 3720 Appendix B.4 — CRC32C](https://www.rfc-editor.org/rfc/rfc3720.html#appendix-B.4).

Standards named by the schemas, listed by name only; this specification does not reproduce them and they were not consulted for this revision: ISO 10383 (market identifier codes), ISO 6166 (ISIN), ISO 17442 (LEI), ISO 10962 (CFI), ISO 3166 (country codes) and ISO 4217 (currency codes). FIGI and CUSIP identifiers are defined by their issuing bodies.

## Appendix A. Frozen example vector

The generated example is **920 bytes**, with three frames and two records. Its SHA-256 is:

```text
9283afa10b2686953e8c9708bd8fd04a3fe020e351ad39f6d5655b00b9f15029
```

Offsets are absolute from the beginning of `example.nwt`:

| Component | Offset |
|---|---:|
| header | 0 |
| metadata | 64 |
| data_frame | 432 |
| definition | 496 |
| trade | 632 |
| index_frame | 720 |
| end_frame | 824 |

The complete 88-byte TRADE record is shown below; offsets in this dump are record-relative.

```text
00000000  58 00 00 00 01 00 01 00 01 00 00 00 00 00 00 00
00000010  e9 03 00 00 00 00 00 00 00 00 2a 36 fe 9c 97 17
00000020  64 00 2a 36 fe 9c 97 17 02 00 00 00 00 00 00 00
00000030  80 82 31 be 1c 00 00 00 00 e4 0b 54 02 00 00 00
00000040  2a 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00000050  01 01 00 00 00 00 00 00
```

The supplied raw-envelope checker passed CRC check vectors, structure-size assertions, the complete example, and eight malformed-input checks (header, metadata, and payload corruption; missing/truncated END; trailing data; mismatched count; frame-sequence gap). Compression and full market-data semantics are not implemented by that checker.

## 22. Developer kit and clarified implementation boundaries

The developer kit supplies all 22 standard record schemas in Python, C# and C++, and in Rust. The Python, C# and C++ programs are built and compared by the kit's tests. The Rust program is written to the same contract but was not compiled or run in this release, because no Rust toolchain was available; treat it as unverified. Zstd (codec 1) is supported in all four languages through the system `libzstd`. Without that library, codec 1 fails with a clear error and raw files keep working.

The kit includes examples for every field, every defined enum, null and empty cases, UTF-8 strings, variable depth and source-gap recovery. The original two-record fixture in Appendix A remains under `fixtures/legacy/`; the draft.2 49-record fixture is `fixtures/all-records.nwt`; the 22-type conformance vector is `fixtures/v1.1/all-records.nwt`.

The normative requirements in this specification apply independently of what an example program implements. The bundled programs are intentionally not advertised as production-conformant NWT SDKs. See the implementation guide's capability matrix for what each language does and does not implement. The store features (`repack`, `query`, `validate`), the converters and the semantic state checks are in Python only.

Clarifications that apply to the whole 1.x line:

1. Feed type means a standard record schema; DATA, INDEX, and END are frame kinds, not exchange feed schemas.
2. Text lengths are UTF-8 octet lengths. Every definition/system text and every book-level field has an explicit worked example in the field reference.
3. Stored frame length excludes its outer padding. Record length includes its internal padding. Index offsets refer to frame headers, never record starts.
4. A decoder that only checks binary shape does not necessarily enforce trade/book business rules. Semantic conformance requires those rules and definition/state prerequisites too.
5. A snapshot being refreshed privately must not expose its partial working book. GAP invalidates committed and working state; a fresh snapshot or CLEAR is required for MBO recovery.
6. Deterministic fixture writers may use a fixed ID to reproduce the exact same object. Modified bytes require a new stream ID in ordinary applications, including any re-framed/recompressed output.
7. The fixture's dictionary-of-decimal-strings representation is an example API convention, not an alternative wire format or a change to the MANIFEST JSON number constraints.
8. The synthetic conformance vectors exist to compare implementations. They are not market data.

See [CHANGELOG.md](CHANGELOG.md) for the revision summary and [VERIFICATION.md](VERIFICATION.md) for actual test coverage.
