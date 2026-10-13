# NWT — complete field reference

**Revision:** 1.1-draft.1. This companion explains every standard record field and every container field. The [specification](SPECIFICATION.md) remains the normative contract. All offsets are zero-based bytes; record payload offsets include the 48-byte common header. Offsets and widths in the type tables are generated from `schemas/records.json`, so they match that file exactly. Worked examples, with real data where a real source exists, are in the [feed cookbook](FEED-COOKBOOK.md).

## Three different kinds of type

The **container version** selects the outer format. The **frame kind** selects DATA, INDEX, or END. The **record type and schema version** select TRADE, QUOTE, and the other feed schemas. None is interchangeable with a venue's native message code.

## Constants and conversions

| Concept | Value / rule |
|---|---|
| Price/strike/multiplier scale | Exact integer × 10^-9 |
| Quantity/volume scale | Exact integer × 10^-9 in quantity_unit |
| Signed null | -9223372036854775808 |
| Unsigned 64-bit null | 18446744073709551615 |
| Count null | 4294967295, only where a schema permits it |
| Timestamp unit | POSIX nanoseconds, never milliseconds or microseconds |
| Byte order | Little-endian for every multi-byte integer |
| Padding | Zero bytes to the next multiple of 8 |
| Text | UTF-8, no NUL, lengths in bytes, in the order of the length fields |
| Boolean wire fields | None in the standard record layouts; metadata has JSON booleans |

For prices, `123.45 → 123450000000`; for size, `0.5 → 500000000`. Parse decimal text using decimal/integer arithmetic. A currency unit and a quantity unit are distinct. A quantity of 1.0 is encoded as 1,000,000,000 even when the venue reports integer lots. A few fields are plain whole numbers and are not scaled: counts, `round_lot`, `shares_outstanding`, IDs and `interval_ns`.

## How to read the type tables

Each table lists the fields after the 48-byte common header, in wire order. The offset is the sum of the widths before it, starting at 48. “Bytes / wire” gives the width and the integer type: `u` unsigned, `i` signed, `bytes[N]` for reserved blocks. A type with text has a second table that gives the order and limits of the texts; each text has a length field in the fixed portion. Enum and flag rules are in the “Meaning” column and summarised under each table.

<!-- BEGIN GENERATED: type tables (tools/build_html.py --write-field-reference) -->

## Common record header — every record

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 0 | `record_bytes` | 4 / u32 | Total bytes from record start through final padding, including the 48-byte common header. Derived by encoder; multiple of 8, maximum 1 MiB. |
| 4 | `record_type` | 2 / u16 | Standard schema identifier 1–22. Selects payload layout. It is not a source exchange message ID. |
| 6 | `schema_version` | 1 / u8 | Exactly 1 for every standard schema in this draft. A different version is a different wire contract. |
| 7 | `flags` | 1 / u8 | Bit 0 REPLAY; bit 1 SUSPECT. All other bits zero. Flags do not alter byte layout or waive validation. |
| 8 | `publisher_id` | 4 / u32 | Producer-assigned publisher namespace. Nonzero for types 1–8, 10–19 and 21–22. SYSTEM may use 0 with channel 0; FRAME_SUMMARY always does. |
| 12 | `channel_id` | 4 / u32 | Logical producer partition. Zero is valid. Sequence continuity is checked independently per publisher/channel. |
| 16 | `instrument_id` | 8 / u64 | Opaque instrument identity scoped by dataset and publisher. Nonzero for types 1–7, 11–19 and 21–22; zero for GAP, SYSTEM, VENUE_DEF and FRAME_SUMMARY. |
| 24 | `ts_event` | 8 / u64 | Source event time in POSIX nanoseconds; UINT64_MAX means unavailable. BAR requires interval end. It may move backward. |
| 32 | `ts_recv` | 8 / u64 | Producer capture time in POSIX nanoseconds; UINT64_MAX means unavailable. No assumption that it exceeds event time. |
| 40 | `sequence` | 8 / u64 | Normalized output position per container/publisher/channel. Starts at 1, increments by one, never wraps. Not the exchange sequence. |

## Type 1 — TRADE

Fixed portion: 88 bytes, including the 48-byte common header. Record bytes: 88. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `price` | 8 / i64 | Signed currency amount × 10^9. INT64_MIN is null. Negative and zero prices are allowed unless a specific action requires null. |
| 56 | `quantity` | 8 / u64 | Nonnegative quantity in definition units × 10^9. UINT64_MAX is null. Action-specific rules distinguish positive size, zero, and null. |
| 64 | `trade_id` | 8 / u64 | Nonzero trade identity within instrument/publisher/channel/container. Remains stable through correction and cancellation. |
| 72 | `original_sequence` | 8 / u64 | 0 for NEW. CANCEL/CORRECT reference the original NEW sequence in the same scope, not the previous correction. |
| 80 | `action` | 1 / u8 | 1 NEW, 2 CANCEL, 3 CORRECT. NEW introduces a trade; CORRECT replaces its values; CANCEL terminates it. |
| 81 | `aggressor` | 1 / u8 | 0 unknown, 1 buyer, 2 seller. This is aggressor direction, not resting-order book side. CANCEL requires 0. |
| 82 | `conditions` | 2 / u16 | Bit 0 off-book. All other bits zero. CANCEL requires zero. |
| 84 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

## Type 2 — QUOTE

Fixed portion: 96 bytes, including the 48-byte common header. Record bytes: 96. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `bid_price` | 8 / i64 | Signed bid price × 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero. |
| 56 | `ask_price` | 8 / i64 | Signed ask price × 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero. |
| 64 | `bid_quantity` | 8 / u64 | Bid size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 72 | `ask_quantity` | 8 / u64 | Ask size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 80 | `bid_order_count` | 4 / u32 | Integral bid order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0. |
| 84 | `ask_order_count` | 4 / u32 | Integral ask order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0. |
| 88 | `quote_flags` | 4 / u32 | Bit 0 indicative. All other bits zero. This is a complete replacement of both quote sides. |
| 92 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

## Type 3 — BAR

Fixed portion: 112 bytes, including the 48-byte common header. Record bytes: 112. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `interval_start_ns` | 8 / u64 | Inclusive start of a completed bar, POSIX ns, non-null and strictly less than interval_end_ns. |
| 56 | `interval_end_ns` | 8 / u64 | Exclusive end of a completed bar, POSIX ns, non-null. Equal to common ts_event. |
| 64 | `open` | 8 / i64 | First trade price × 10^9 under the aggregation policy. Null only for empty bars. |
| 72 | `high` | 8 / i64 | Maximum trade price × 10^9. Must be at least open and close; null only for empty bars. |
| 80 | `low` | 8 / i64 | Minimum trade price × 10^9. Must be at most open and close; null only for empty bars. |
| 88 | `close` | 8 / i64 | Last trade price × 10^9 under the aggregation policy. Null only for empty bars. |
| 96 | `volume` | 8 / u64 | Traded quantity × 10^9, not currency turnover. Positive/non-null for nonempty bars; zero for empty bars. |
| 104 | `trade_count` | 4 / u32 | Positive integral count for nonempty bars; zero for empty bars. UINT32_MAX is not valid for this schema. |
| 108 | `bar_flags` | 4 / u32 | Bit 0 empty. Empty bars have four null prices, zero volume, and zero count. All other bits zero. |

## Type 4 — MBO

Fixed portion: 88 bytes, including the 48-byte common header. Record bytes: 88. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `order_id` | 8 / u64 | Nonzero live-order key in the book scope. 0 only for CLEAR, SNAPSHOT_BEGIN, SNAPSHOT_END. IDs may be reused after deletion. |
| 56 | `price` | 8 / i64 | Signed currency amount × 10^9. INT64_MIN is null. Negative and zero prices are allowed unless a specific action requires null. |
| 64 | `quantity` | 8 / u64 | Nonnegative quantity in definition units × 10^9. UINT64_MAX is null. Action-specific rules distinguish positive size, zero, and null. |
| 72 | `priority` | 8 / u64 | Ascending queue rank/key. UINT64_MAX means unknown. Lower known values have earlier priority at one side/price. |
| 80 | `action` | 1 / u8 | 1 ADD, 2 MODIFY, 3 DELETE, 4 CLEAR, 5 SNAPSHOT_BEGIN, 6 SNAPSHOT_END. MODIFY sets absolute remaining size, never a delta. |
| 81 | `side` | 1 / u8 | 0 none/control, 1 bid, 2 ask. ADD/MODIFY require bid/ask; DELETE and snapshot/control actions require 0. |
| 82 | `mbo_flags` | 2 / u16 | Zero in v1.0. No implied execution, partial-fill, or snapshot bits. |
| 84 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

## Type 5 — BOOK_SNAPSHOT

Fixed portion: 56 bytes, including the 48-byte common header. Record bytes: 56 + 48 × levels. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `levels` | 2 / u16 | Number of 48-byte paired bid/ask elements, 0–1024. Encoder derives it from the level array. Unequal depths use absent-side suffixes. |
| 50 | `book_flags` | 2 / u16 | Bit 0 depth-limited: deeper prices may exist. All other bits zero. Zero levels is a valid empty observed book. |
| 52 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Each level element has its own 48-byte layout. Offsets below are relative to that element; element `i` starts at record offset `56 + 48*i`.

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 0 | `bid_price` | 8 / i64 | Signed bid price × 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero. |
| 8 | `ask_price` | 8 / i64 | Signed ask price × 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero. |
| 16 | `bid_quantity` | 8 / u64 | Bid size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 24 | `ask_quantity` | 8 / u64 | Ask size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 32 | `bid_count` | 4 / u32 | Integral bid order count for this level. Same presence/null rules as bid_order_count. |
| 36 | `ask_count` | 4 / u32 | Integral ask order count for this level. Same presence/null rules as ask_order_count. |
| 40 | `reserved` | 8 / bytes[8] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

An element pairs the bid at rank i with the ask at rank i. Neither side is a delta. The last element must contain at least one present side.

## Type 6 — INSTRUMENT_DEF

Fixed portion: 112 bytes, including the 48-byte common header. Record bytes: align8(112 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `price_increment` | 8 / i64 | Minimum fixed price step × 10^9; positive or INT64_MIN (unknown/variable schedule). Does not change wire scale. |
| 56 | `quantity_increment` | 8 / u64 | Quantity step in definition units × 10^9; positive or UINT64_MAX (unknown). Does not change wire scale. |
| 64 | `contract_multiplier` | 8 / i64 | Signed fixed-point multiplier × 10^9; positive or INT64_MIN (unknown). No universal cash-value formula is implied. |
| 72 | `expiration_ns` | 8 / u64 | Expiration instant in POSIX ns; UINT64_MAX if unavailable/not applicable. |
| 80 | `underlying_instrument_id` | 8 / u64 | Same-publisher instrument ID; 0 when absent. Underlying definition need not be included in the container. |
| 88 | `strike` | 8 / i64 | Strike price × 10^9; INT64_MIN if unavailable/not applicable. Not enough information to infer option right/style. |
| 96 | `asset_class` | 1 / u8 | 0 unspecified, 1 equity, 2 future, 3 option, 4 FX, 5 crypto, 6 index, 7 fixed income. |
| 97 | `reserved` | 7 / bytes[7] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 104 | `symbol_bytes` | 2 / u16 | UTF-8 byte length of symbol, 1–255. Computed, not character count. |
| 106 | `venue_bytes` | 2 / u16 | UTF-8 byte length of venue, 0–255. Empty is allowed. |
| 108 | `currency_bytes` | 2 / u16 | UTF-8 byte length of currency code, 1–16. |
| 110 | `quantity_unit_bytes` | 2 / u16 | UTF-8 byte length of quantity-unit code, 1–32. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `symbol` | `symbol_bytes` | 1–255 |
| 2 | `venue` | `venue_bytes` | 0–255 |
| 3 | `currency` | `currency_bytes` | 1–16 |
| 4 | `quantity_unit` | `quantity_unit_bytes` | 1–32 |

## Type 7 — STATUS

Fixed portion: 64 bytes, including the 48-byte common header. Record bytes: 64. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `status` | 2 / u16 | 0 unknown, 1 pre-open, 2 open, 3 halted, 4 closed, 5 auction. Replacement administrative state; does not clear books. |
| 50 | `reason` | 2 / u16 | 0 unspecified, 1 scheduled, 2 volatility, 3 regulatory, 4 technical. |
| 52 | `status_flags` | 4 / u32 | Zero in v1.0. |
| 56 | `reserved` | 8 / bytes[8] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

## Type 8 — GAP

Fixed portion: 80 bytes, including the 48-byte common header. Record bytes: 80. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `first_missing_source_sequence` | 8 / u64 | Inclusive first missing source-native sequence, or UINT64_MAX when unknown. Both endpoints must be null together. |
| 56 | `last_missing_source_sequence` | 8 / u64 | Inclusive last missing source-native sequence, or UINT64_MAX when unknown. If known, first ≤ last. |
| 64 | `reason` | 4 / u32 | 1 source packet loss, 2 source reset, 3 producer overflow, 4 unknown discontinuity. |
| 68 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 72 | `recovery_id` | 8 / u64 | Nonzero identifier unique among GAP records in this container. Diagnostic correlation only; not a snapshot ID. |

## Type 9 — SYSTEM

Fixed portion: 64 bytes, including the 48-byte common header. Record bytes: align8(64 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `code` | 2 / u16 | 1 heartbeat, 2 info, 3 warning, 4 error. SYSTEM error does not replace END. |
| 50 | `text_bytes` | 2 / u16 | UTF-8 byte length of text, 0–4096. Heartbeat requires 0. |
| 52 | `severity` | 1 / u8 | 0 info for heartbeat/info, 1 for warning, 2 for error. Must agree with code. |
| 53 | `reserved` | 3 / bytes[3] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 56 | `related_recovery_id` | 8 / u64 | 0 or a previously emitted GAP recovery ID. Heartbeat requires 0. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `text` | `text_bytes` | 0–4096 |

## Type 10 — VENUE_DEF

Fixed portion: 96 bytes, including the 48-byte common header. Record bytes: align8(96 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `created_ns` | 8 / u64 | Date the venue record was created, midnight UTC of the source date in POSIX ns; UINT64_MAX if unavailable. |
| 56 | `updated_ns` | 8 / u64 | Date of the last change to the venue record, midnight UTC in POSIX ns; UINT64_MAX if unavailable. |
| 64 | `expiry_ns` | 8 / u64 | Date the venue code expires, midnight UTC in POSIX ns; UINT64_MAX when the venue has no expiry. |
| 72 | `kind` | 1 / u8 | 1 operating venue, 2 market segment. An operating venue requires mic equal to operating_mic. |
| 73 | `status` | 1 / u8 | 1 active, 2 updated, 3 expired. |
| 74 | `mic_bytes` | 2 / u16 | UTF-8 byte length of mic, exactly 4. Computed, not character count. |
| 76 | `operating_mic_bytes` | 2 / u16 | UTF-8 byte length of operating_mic, exactly 4. Computed, not character count. |
| 78 | `country_bytes` | 2 / u16 | UTF-8 byte length of country, exactly 2. Computed, not character count. |
| 80 | `category_bytes` | 2 / u16 | UTF-8 byte length of category, 0 or 4. Computed, not character count. |
| 82 | `acronym_bytes` | 2 / u16 | UTF-8 byte length of acronym, 0–64. Computed, not character count. |
| 84 | `city_bytes` | 2 / u16 | UTF-8 byte length of city, 0–128. Computed, not character count. |
| 86 | `name_bytes` | 2 / u16 | UTF-8 byte length of name, 1–255. Computed, not character count. |
| 88 | `legal_entity_bytes` | 2 / u16 | UTF-8 byte length of legal_entity, 0–255. Computed, not character count. |
| 90 | `lei_bytes` | 2 / u16 | UTF-8 byte length of lei, 0 or 20. Computed, not character count. |
| 92 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `mic` | `mic_bytes` | exactly 4 |
| 2 | `operating_mic` | `operating_mic_bytes` | exactly 4 |
| 3 | `country` | `country_bytes` | exactly 2 |
| 4 | `category` | `category_bytes` | 0 or 4 |
| 5 | `acronym` | `acronym_bytes` | 0–64 |
| 6 | `city` | `city_bytes` | 0–128 |
| 7 | `name` | `name_bytes` | 1–255 |
| 8 | `legal_entity` | `legal_entity_bytes` | 0–255 |
| 9 | `lei` | `lei_bytes` | 0 or 20 |

Allowed values: `kind` ∈ {1, 2}; `status` ∈ {1, 2, 3}.

## Type 11 — OPTION_DEF

Fixed portion: 96 bytes, including the 48-byte common header. Record bytes: align8(96 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `underlying_instrument_id` | 8 / u64 | Same-publisher instrument ID of the underlying; 0 when it has no ID in this namespace, which requires a non-empty underlying_symbol. |
| 56 | `expiration_ns` | 8 / u64 | Expiration instant in POSIX ns. Non-null. Equals the INSTRUMENT_DEF expiration when one exists. |
| 64 | `strike` | 8 / i64 | Strike price × 10^9. Non-null. Equals the INSTRUMENT_DEF strike when one exists. |
| 72 | `contract_multiplier` | 8 / i64 | Signed fixed-point multiplier × 10^9; positive or INT64_MIN (unknown). |
| 80 | `right` | 1 / u8 | 1 call, 2 put. |
| 81 | `exercise_style` | 1 / u8 | 0 unknown, 1 American, 2 European. Never inferred from the symbol. |
| 82 | `settlement` | 1 / u8 | 0 unknown, 1 physical, 2 cash. Never inferred from the symbol. |
| 83 | `closing_type` | 1 / u8 | 0 unknown, 1 normal hours, 2 late hours. |
| 84 | `option_flags` | 1 / u8 | Bit 0 pending; bit 1 adjusted (non-standard deliverable). All other bits zero. |
| 85 | `reserved` | 3 / bytes[3] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 88 | `root_bytes` | 2 / u16 | UTF-8 byte length of root, 1–16. Computed, not character count. |
| 90 | `underlying_symbol_bytes` | 2 / u16 | UTF-8 byte length of underlying_symbol, 0–255. Computed, not character count. |
| 92 | `osi_symbol_bytes` | 2 / u16 | UTF-8 byte length of osi_symbol, 0 or 21. Computed, not character count. |
| 94 | `currency_bytes` | 2 / u16 | UTF-8 byte length of currency, 0–16. Computed, not character count. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `root` | `root_bytes` | 1–16 |
| 2 | `underlying_symbol` | `underlying_symbol_bytes` | 0–255 |
| 3 | `osi_symbol` | `osi_symbol_bytes` | 0 or 21 |
| 4 | `currency` | `currency_bytes` | 0–16 |

Allowed values: `right` ∈ {1, 2}; `exercise_style` ∈ {0, 1, 2}; `settlement` ∈ {0, 1, 2}; `closing_type` ∈ {0, 1, 2}. Allowed flag bits: `option_flags` bits 0–1 (mask 3).

## Type 12 — LISTING

Fixed portion: 72 bytes, including the 48-byte common header. Record bytes: align8(72 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `round_lot` | 4 / u32 | Round-lot size as an integral count of units; UINT32_MAX if unavailable. Not scaled by 10^9. |
| 52 | `listing_flags` | 1 / u8 | Bit 0 ETF; bit 1 test issue; bit 2 NextShares. All other bits zero. |
| 53 | `market_tier` | 1 / u8 | 0 unspecified, 1 global select, 2 global, 3 capital. |
| 54 | `financial_flags` | 1 / u8 | Bit 0 reported; bit 1 deficient; bit 2 delinquent; bit 3 bankrupt. Bits 1–3 require bit 0. Value 1 is normal; 0 means the source reports no financial status. |
| 55 | `reserved` | 1 / bytes[1] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 56 | `symbol_bytes` | 2 / u16 | UTF-8 byte length of symbol, 1–255. Computed, not character count. |
| 58 | `name_bytes` | 2 / u16 | UTF-8 byte length of name, 0–512. Computed, not character count. |
| 60 | `listing_mic_bytes` | 2 / u16 | UTF-8 byte length of listing_mic, 0 or 4. Computed, not character count. |
| 62 | `cqs_symbol_bytes` | 2 / u16 | UTF-8 byte length of cqs_symbol, 0–255. Computed, not character count. |
| 64 | `alt_symbol_bytes` | 2 / u16 | UTF-8 byte length of alt_symbol, 0–255. Computed, not character count. |
| 66 | `reserved` | 6 / bytes[6] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `symbol` | `symbol_bytes` | 1–255 |
| 2 | `name` | `name_bytes` | 0–512 |
| 3 | `listing_mic` | `listing_mic_bytes` | 0 or 4 |
| 4 | `cqs_symbol` | `cqs_symbol_bytes` | 0–255 |
| 5 | `alt_symbol` | `alt_symbol_bytes` | 0–255 |

Allowed values: `market_tier` ∈ {0, 1, 2, 3}. Allowed flag bits: `listing_flags` bits 0–2 (mask 7); `financial_flags` bits 0–3 (mask 15).

## Type 13 — STATISTICS

Fixed portion: 80 bytes, including the 48-byte common header. Record bytes: 80. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `ts_ref` | 8 / u64 | Start of the session or date the value refers to, POSIX ns; UINT64_MAX if unavailable. |
| 56 | `price` | 8 / i64 | Value × 10^9 for price statistics (types 1–6). Non-null for SET of a price type; INT64_MIN otherwise. |
| 64 | `quantity` | 8 / u64 | Value × 10^9 for quantity statistics (types 7–8). Non-null for SET of a quantity type; UINT64_MAX otherwise. |
| 72 | `stat_type` | 2 / u16 | 1 open, 2 high, 3 low, 4 close, 5 settlement, 6 VWAP (price types); 7 volume, 8 open interest (quantity types). |
| 74 | `action` | 1 / u8 | 1 SET, 2 DELETE. SET replaces the value for (instrument, stat_type, ts_ref); DELETE withdraws it and requires both values null. |
| 75 | `stat_flags` | 1 / u8 | Bit 0 preliminary. All other bits zero. DELETE requires zero. |
| 76 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Allowed values: `stat_type` ∈ {1, 2, 3, 4, 5, 6, 7, 8}; `action` ∈ {1, 2}. Allowed flag bits: `stat_flags` bit 0 (mask 1).

## Type 14 — OPTION_ANALYTICS

Fixed portion: 120 bytes, including the 48-byte common header. Record bytes: 120. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `implied_volatility` | 8 / i64 | Annualised implied volatility × 10^9 (1.0 = 100%). INT64_MIN is null; otherwise not negative. |
| 56 | `delta` | 8 / i64 | Delta × 10^9. INT64_MIN is null; otherwise within −1 to +1. |
| 64 | `gamma` | 8 / i64 | Gamma × 10^9, per 1.00 move in the underlying. INT64_MIN is null; otherwise not negative. |
| 72 | `theta` | 8 / i64 | Theta × 10^9, currency per calendar day. INT64_MIN is null. |
| 80 | `vega` | 8 / i64 | Vega × 10^9, currency per 0.01 change in volatility. INT64_MIN is null. |
| 88 | `rho` | 8 / i64 | Rho × 10^9, currency per 0.01 change in rate. INT64_MIN is null. |
| 96 | `underlying_price` | 8 / i64 | Underlying price × 10^9 used for the calculation. INT64_MIN is null. |
| 104 | `theoretical_price` | 8 / i64 | Model price of the option × 10^9. INT64_MIN is null. |
| 112 | `price_basis` | 1 / u8 | 0 unspecified, 1 mid, 2 last, 3 bid, 4 ask, 5 settlement. |
| 113 | `model` | 1 / u8 | 0 unspecified, 1 Black-Scholes-Merton, 2 Black-76, 3 binomial, 4 other. |
| 114 | `reserved` | 6 / bytes[6] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Allowed values: `price_basis` ∈ {0, 1, 2, 3, 4, 5}; `model` ∈ {0, 1, 2, 3, 4}.

## Type 15 — BOOK_DELTA

Fixed portion: 72 bytes, including the 48-byte common header. Record bytes: 72. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `price` | 8 / i64 | Level price × 10^9. Non-null for SET and DELETE; INT64_MIN for CLEAR. Levels are keyed by price, not rank. |
| 56 | `quantity` | 8 / u64 | New aggregate size at this price × 10^9. SET: 1 through UINT64_MAX−1. DELETE and CLEAR: 0. |
| 64 | `order_count` | 4 / u32 | Integral order count at the level; UINT32_MAX if unknown. DELETE and CLEAR require UINT32_MAX. |
| 68 | `action` | 1 / u8 | 1 SET, 2 DELETE, 3 CLEAR. SET adds or replaces a level; CLEAR empties one side or the whole book. |
| 69 | `side` | 1 / u8 | 1 bid, 2 ask, 0 both. 0 is valid only for CLEAR. |
| 70 | `delta_flags` | 1 / u8 | Bit 0 LAST_IN_EVENT: the last delta of one source event. All other bits zero. |
| 71 | `reserved` | 1 / bytes[1] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Allowed values: `action` ∈ {1, 2, 3}; `side` ∈ {0, 1, 2}. Allowed flag bits: `delta_flags` bit 0 (mask 1).

## Type 16 — IMBALANCE

Fixed portion: 104 bytes, including the 48-byte common header. Record bytes: 104. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `auction_ns` | 8 / u64 | Scheduled auction time in POSIX ns; UINT64_MAX if unavailable. |
| 56 | `reference_price` | 8 / i64 | Reference price × 10^9 for the imbalance. Non-null. |
| 64 | `near_price` | 8 / i64 | Indicative price × 10^9 from auction and continuous interest; INT64_MIN if unavailable. |
| 72 | `far_price` | 8 / i64 | Indicative price × 10^9 from auction interest only; INT64_MIN if unavailable. |
| 80 | `paired_quantity` | 8 / u64 | Quantity × 10^9 matched at the reference price; UINT64_MAX if unavailable. |
| 88 | `imbalance_quantity` | 8 / u64 | Unmatched quantity × 10^9. Non-null; zero exactly when imbalance_side is 0. |
| 96 | `imbalance_side` | 1 / u8 | 0 none, 1 buy, 2 sell. |
| 97 | `auction_type` | 1 / u8 | 0 unspecified, 1 opening, 2 closing, 3 reopening, 4 IPO, 5 intraday. |
| 98 | `reserved` | 6 / bytes[6] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Allowed values: `imbalance_side` ∈ {0, 1, 2}; `auction_type` ∈ {0, 1, 2, 3, 4, 5}.

## Type 17 — SYMBOL_MAP

Fixed portion: 72 bytes, including the 48-byte common header. Record bytes: align8(72 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `valid_from_ns` | 8 / u64 | Inclusive start of the mapping interval in POSIX ns. Non-null. |
| 56 | `valid_to_ns` | 8 / u64 | Exclusive end of the mapping interval in POSIX ns; UINT64_MAX means open-ended. Otherwise greater than valid_from_ns. |
| 64 | `symbology` | 1 / u8 | 1 native, 2 OSI, 3 ISIN, 4 FIGI, 5 root, 6 continuous. Root is one-to-many; the others name one instrument at any time. |
| 65 | `reserved` | 1 / bytes[1] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 66 | `symbol_bytes` | 2 / u16 | UTF-8 byte length of symbol, 1–255. Computed, not character count. |
| 68 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `symbol` | `symbol_bytes` | 1–255 |

Allowed values: `symbology` ∈ {1, 2, 3, 4, 5, 6}.

## Type 18 — TRADE_QUOTE

Fixed portion: 120 bytes, including the 48-byte common header. Record bytes: 120. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `price` | 8 / i64 | Trade price × 10^9. Non-null. |
| 56 | `quantity` | 8 / u64 | Trade size × 10^9. Positive and non-null. |
| 64 | `trade_id` | 8 / u64 | Trade identity within instrument/publisher/channel/container; 0 when unknown. |
| 72 | `bid_price` | 8 / i64 | Signed bid price × 10^9. INT64_MIN means the bid side is absent; then its size and count must both be zero. |
| 80 | `ask_price` | 8 / i64 | Signed ask price × 10^9. INT64_MIN means the ask side is absent; then its size and count must both be zero. |
| 88 | `bid_quantity` | 8 / u64 | Bid size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 96 | `ask_quantity` | 8 / u64 | Ask size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 104 | `bid_order_count` | 4 / u32 | Integral bid order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0. |
| 108 | `ask_order_count` | 4 / u32 | Integral ask order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0. |
| 112 | `aggressor` | 1 / u8 | 0 unknown, 1 buyer, 2 seller. Aggressor direction, not resting-order book side. |
| 113 | `reserved` | 1 / bytes[1] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 114 | `conditions` | 2 / u16 | Bit 0 off-book. All other bits zero. |
| 116 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Allowed values: `aggressor` ∈ {0, 1, 2}. Allowed flag bits: `conditions` bit 0 (mask 1).

## Type 19 — BEST_QUOTE

Fixed portion: 112 bytes, including the 48-byte common header. Record bytes: 112. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `bid_price` | 8 / i64 | Signed bid price × 10^9. INT64_MIN means the bid side is absent; then its size and count must both be zero. |
| 56 | `ask_price` | 8 / i64 | Signed ask price × 10^9. INT64_MIN means the ask side is absent; then its size and count must both be zero. |
| 64 | `bid_quantity` | 8 / u64 | Bid size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 72 | `ask_quantity` | 8 / u64 | Ask size × 10^9. Present side requires 1 through UINT64_MAX−1; absent side requires 0. |
| 80 | `bid_order_count` | 4 / u32 | Integral bid order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0. |
| 84 | `ask_order_count` | 4 / u32 | Integral ask order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0. |
| 88 | `quote_flags` | 4 / u32 | Bit 0 indicative. All other bits zero. |
| 92 | `bid_publisher_id` | 4 / u32 | Declared publisher that set the bid; 0 when the side is absent or the venue is unknown. |
| 96 | `ask_publisher_id` | 4 / u32 | Declared publisher that set the ask; 0 when the side is absent or the venue is unknown. |
| 100 | `reserved` | 4 / bytes[4] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 104 | `interval_ns` | 8 / u64 | 0 for an event-driven quote; otherwise the sampling interval in ns, with ts_event at the interval end. A duration, not a timestamp. |

Allowed flag bits: `quote_flags` bit 0 (mask 1).

## Type 20 — FRAME_SUMMARY

Fixed portion: 104 bytes, including the 48-byte common header. Record bytes: 104. A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `data_frame_seq` | 8 / u64 | frame_seq of the DATA frame this record describes. |
| 56 | `data_frame_offset` | 8 / u64 | Byte offset of that frame header, absolute from container byte 0. |
| 64 | `stored_bytes` | 4 / u32 | stored_bytes of that frame, so its payload can be fetched in one read. |
| 68 | `codec` | 1 / u8 | Codec of that frame: 0 raw, 1 Zstd. |
| 69 | `summary_flags` | 1 / u8 | Bit 0: the frame has a record with null ts_event. Bit 1: non-null ts_event is non-decreasing within the frame. All other bits zero. |
| 70 | `reserved` | 2 / bytes[2] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 72 | `type_mask` | 8 / u64 | Bit n (1–63) set when standard record type n is present in the frame; bit 0 set when any other type is present. |
| 80 | `min_instrument_id` | 8 / u64 | Smallest non-zero instrument ID in the frame; 0 when none. |
| 88 | `max_instrument_id` | 8 / u64 | Largest non-zero instrument ID in the frame; 0 when none. |
| 96 | `reserved` | 8 / bytes[8] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Allowed values: `codec` ∈ {0, 1}. Allowed flag bits: `summary_flags` bits 0–1 (mask 3).

## Type 21 — SECURITY_DEF

Fixed portion: 216 bytes, including the 48-byte common header. Record bytes: align8(216 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `listing_group_id` | 8 / u64 | Producer identifier that groups the listings of one security; 0 when none. |
| 56 | `security_id` | 8 / u64 | Producer identifier of the security; 0 when none. |
| 64 | `issuer_id` | 8 / u64 | Producer identifier of the issuer; 0 when none. |
| 72 | `listing_created_ns` | 8 / u64 | When the listing record was created at the source, POSIX ns; UINT64_MAX if unavailable. |
| 80 | `listing_ns` | 8 / u64 | Listing date, POSIX ns; UINT64_MAX if unavailable. |
| 88 | `delisting_ns` | 8 / u64 | Delisting date, POSIX ns; UINT64_MAX when the listing is not delisted or the date is unavailable. |
| 96 | `shares_outstanding` | 8 / u64 | Shares outstanding as a whole count, not scaled by 10^9 (large issuers exceed the scaled range); UINT64_MAX if unavailable. |
| 104 | `shares_outstanding_ns` | 8 / u64 | Date the shares-outstanding figure refers to, POSIX ns; UINT64_MAX if unavailable. |
| 112 | `lot_size` | 8 / u64 | Trading lot size × 10^9; UINT64_MAX if unavailable. |
| 120 | `par_value` | 8 / i64 | Par value × 10^9 in par_value_currency; INT64_MIN if unavailable. |
| 128 | `votes_per_share` | 8 / i64 | Votes per share × 10^9; INT64_MIN if unavailable. |
| 136 | `cik` | 8 / u64 | Regulatory central index key of the issuer; 0 when none. |
| 144 | `sic` | 4 / u32 | Standard industrial classification code; 0 when none. |
| 148 | `naics` | 4 / u32 | North American industry classification code; 0 when none. |
| 152 | `listing_source` | 1 / u8 | 0 unknown, 1 main, 2 secondary. |
| 153 | `security_flags` | 1 / u8 | Bit 0 multi-currency. All other bits zero. |
| 154 | `reserved` | 2 / bytes[2] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 156 | `issuer_name_bytes` | 2 / u16 | UTF-8 byte length of issuer_name, 0–255. Computed, not character count. |
| 158 | `description_bytes` | 2 / u16 | UTF-8 byte length of description, 0–255. Computed, not character count. |
| 160 | `security_type_bytes` | 2 / u16 | UTF-8 byte length of security_type, 0–8. Computed, not character count. |
| 162 | `structure_bytes` | 2 / u16 | UTF-8 byte length of structure, 0–8. Computed, not character count. |
| 164 | `listing_status_bytes` | 2 / u16 | UTF-8 byte length of listing_status, 0–8. Computed, not character count. |
| 166 | `voting_bytes` | 2 / u16 | UTF-8 byte length of voting, 0–8. Computed, not character count. |
| 168 | `primary_exchange_bytes` | 2 / u16 | UTF-8 byte length of primary_exchange, 0–16. Computed, not character count. |
| 170 | `exchange_bytes` | 2 / u16 | UTF-8 byte length of exchange, 0–16. Computed, not character count. |
| 172 | `operating_mic_bytes` | 2 / u16 | UTF-8 byte length of operating_mic, 0 or 4. Computed, not character count. |
| 174 | `segment_mic_bytes` | 2 / u16 | UTF-8 byte length of segment_mic, 0 or 4. Computed, not character count. |
| 176 | `segment_name_bytes` | 2 / u16 | UTF-8 byte length of segment_name, 0–128. Computed, not character count. |
| 178 | `symbol_bytes` | 2 / u16 | UTF-8 byte length of symbol, 0–255. Computed, not character count. |
| 180 | `alt_symbol_bytes` | 2 / u16 | UTF-8 byte length of alt_symbol, 0–255. Computed, not character count. |
| 182 | `local_code_bytes` | 2 / u16 | UTF-8 byte length of local_code, 0–255. Computed, not character count. |
| 184 | `isin_bytes` | 2 / u16 | UTF-8 byte length of isin, 0 or 12. Computed, not character count. |
| 186 | `cusip_bytes` | 2 / u16 | UTF-8 byte length of cusip, 0 or 9. Computed, not character count. |
| 188 | `composite_figi_bytes` | 2 / u16 | UTF-8 byte length of composite_figi, 0 or 12. Computed, not character count. |
| 190 | `composite_ticker_bytes` | 2 / u16 | UTF-8 byte length of composite_ticker, 0–32. Computed, not character count. |
| 192 | `figi_bytes` | 2 / u16 | UTF-8 byte length of figi, 0 or 12. Computed, not character count. |
| 194 | `figi_ticker_bytes` | 2 / u16 | UTF-8 byte length of figi_ticker, 0–32. Computed, not character count. |
| 196 | `fisn_bytes` | 2 / u16 | UTF-8 byte length of fisn, 0–35. Computed, not character count. |
| 198 | `lei_bytes` | 2 / u16 | UTF-8 byte length of lei, 0 or 20. Computed, not character count. |
| 200 | `cfi_bytes` | 2 / u16 | UTF-8 byte length of cfi, 0 or 6. Computed, not character count. |
| 202 | `cic_bytes` | 2 / u16 | UTF-8 byte length of cic, 0–8. Computed, not character count. |
| 204 | `gics_bytes` | 2 / u16 | UTF-8 byte length of gics, 0–8. Computed, not character count. |
| 206 | `incorporation_country_bytes` | 2 / u16 | UTF-8 byte length of incorporation_country, 0 or 2. Computed, not character count. |
| 208 | `listing_country_bytes` | 2 / u16 | UTF-8 byte length of listing_country, 0 or 2. Computed, not character count. |
| 210 | `register_country_bytes` | 2 / u16 | UTF-8 byte length of register_country, 0 or 2. Computed, not character count. |
| 212 | `trading_currency_bytes` | 2 / u16 | UTF-8 byte length of trading_currency, 0–16. Computed, not character count. |
| 214 | `par_value_currency_bytes` | 2 / u16 | UTF-8 byte length of par_value_currency, 0–16. Computed, not character count. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `issuer_name` | `issuer_name_bytes` | 0–255 |
| 2 | `description` | `description_bytes` | 0–255 |
| 3 | `security_type` | `security_type_bytes` | 0–8 |
| 4 | `structure` | `structure_bytes` | 0–8 |
| 5 | `listing_status` | `listing_status_bytes` | 0–8 |
| 6 | `voting` | `voting_bytes` | 0–8 |
| 7 | `primary_exchange` | `primary_exchange_bytes` | 0–16 |
| 8 | `exchange` | `exchange_bytes` | 0–16 |
| 9 | `operating_mic` | `operating_mic_bytes` | 0 or 4 |
| 10 | `segment_mic` | `segment_mic_bytes` | 0 or 4 |
| 11 | `segment_name` | `segment_name_bytes` | 0–128 |
| 12 | `symbol` | `symbol_bytes` | 0–255 |
| 13 | `alt_symbol` | `alt_symbol_bytes` | 0–255 |
| 14 | `local_code` | `local_code_bytes` | 0–255 |
| 15 | `isin` | `isin_bytes` | 0 or 12 |
| 16 | `cusip` | `cusip_bytes` | 0 or 9 |
| 17 | `composite_figi` | `composite_figi_bytes` | 0 or 12 |
| 18 | `composite_ticker` | `composite_ticker_bytes` | 0–32 |
| 19 | `figi` | `figi_bytes` | 0 or 12 |
| 20 | `figi_ticker` | `figi_ticker_bytes` | 0–32 |
| 21 | `fisn` | `fisn_bytes` | 0–35 |
| 22 | `lei` | `lei_bytes` | 0 or 20 |
| 23 | `cfi` | `cfi_bytes` | 0 or 6 |
| 24 | `cic` | `cic_bytes` | 0–8 |
| 25 | `gics` | `gics_bytes` | 0–8 |
| 26 | `incorporation_country` | `incorporation_country_bytes` | 0 or 2 |
| 27 | `listing_country` | `listing_country_bytes` | 0 or 2 |
| 28 | `register_country` | `register_country_bytes` | 0 or 2 |
| 29 | `trading_currency` | `trading_currency_bytes` | 0–16 |
| 30 | `par_value_currency` | `par_value_currency_bytes` | 0–16 |

Allowed values: `listing_source` ∈ {0, 1, 2}. Allowed flag bits: `security_flags` bit 0 (mask 1).

## Type 22 — CORPORATE_ACTION

Fixed portion: 184 bytes, including the 48-byte common header. Record bytes: align8(184 + sum of text byte lengths). A worked example is in the [feed cookbook](FEED-COOKBOOK.md).

| Offset | Field | Bytes / wire | Meaning, units, nulls, validation |
|---:|---|---|---|
| 48 | `security_id` | 8 / u64 | Producer identifier of the security; 0 when none. |
| 56 | `issuer_id` | 8 / u64 | Producer identifier of the issuer; 0 when none. |
| 64 | `created_ns` | 8 / u64 | When the event record was created at the source, POSIX ns; UINT64_MAX if unavailable. |
| 72 | `effective_ns` | 8 / u64 | Effective date, POSIX ns; UINT64_MAX if unavailable. |
| 80 | `ex_ns` | 8 / u64 | Ex-date, POSIX ns; UINT64_MAX if unavailable. |
| 88 | `record_ns` | 8 / u64 | Record date, POSIX ns; UINT64_MAX if unavailable. |
| 96 | `payment_ns` | 8 / u64 | Payment date, POSIX ns; UINT64_MAX if unavailable. |
| 104 | `record_date_id` | 8 / u64 | Producer identifier of the record-date entry; 0 when none. |
| 112 | `outturn_security_id` | 8 / u64 | Producer identifier of the resulting security; 0 when none. |
| 120 | `ratio_old` | 8 / i64 | Old side of the ratio × 10^9 (for a 4-for-1 split: 1); INT64_MIN if unavailable. |
| 128 | `ratio_new` | 8 / i64 | New side of the ratio × 10^9 (for a 4-for-1 split: 4); INT64_MIN if unavailable. |
| 136 | `option_id` | 4 / u32 | Option number within the event; UINT32_MAX if unavailable. |
| 140 | `serial_id` | 4 / u32 | Serial number within the option; UINT32_MAX if unavailable. |
| 144 | `action_flags` | 1 / u8 | Bit 0 default option. All other bits zero. |
| 145 | `reserved` | 3 / bytes[3] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |
| 148 | `event_bytes` | 2 / u16 | UTF-8 byte length of event, 1–8. Computed, not character count. |
| 150 | `subtype_bytes` | 2 / u16 | UTF-8 byte length of subtype, 0–16. Computed, not character count. |
| 152 | `action_bytes` | 2 / u16 | UTF-8 byte length of action, 0–8. Computed, not character count. |
| 154 | `status_bytes` | 2 / u16 | UTF-8 byte length of status, 0–8. Computed, not character count. |
| 156 | `participation_bytes` | 2 / u16 | UTF-8 byte length of participation, 0–8. Computed, not character count. |
| 158 | `payment_type_bytes` | 2 / u16 | UTF-8 byte length of payment_type, 0–8. Computed, not character count. |
| 160 | `fraction_bytes` | 2 / u16 | UTF-8 byte length of fraction, 0–8. Computed, not character count. |
| 162 | `date_label_bytes` | 2 / u16 | UTF-8 byte length of date_label, 0–32. Computed, not character count. |
| 164 | `related_event_bytes` | 2 / u16 | UTF-8 byte length of related_event, 0–8. Computed, not character count. |
| 166 | `related_event_id_bytes` | 2 / u16 | UTF-8 byte length of related_event_id, 0–32. Computed, not character count. |
| 168 | `event_id_bytes` | 2 / u16 | UTF-8 byte length of event_id, 1–32. Computed, not character count. |
| 170 | `unique_id_bytes` | 2 / u16 | UTF-8 byte length of unique_id, 1–48. Computed, not character count. |
| 172 | `rate_currency_bytes` | 2 / u16 | UTF-8 byte length of rate_currency, 0–16. Computed, not character count. |
| 174 | `outturn_isin_bytes` | 2 / u16 | UTF-8 byte length of outturn_isin, 0 or 12. Computed, not character count. |
| 176 | `details_bytes` | 2 / u16 | UTF-8 byte length of details, 0–65535. Computed, not character count. |
| 178 | `reserved` | 6 / bytes[6] | All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage. |

Variable text follows the fixed portion, in this order, without terminators or separators, then zero padding to a multiple of 8:

| Order | Text | Length field | Limit (UTF-8 bytes) |
|---:|---|---|---|
| 1 | `event` | `event_bytes` | 1–8 |
| 2 | `subtype` | `subtype_bytes` | 0–16 |
| 3 | `action` | `action_bytes` | 0–8 |
| 4 | `status` | `status_bytes` | 0–8 |
| 5 | `participation` | `participation_bytes` | 0–8 |
| 6 | `payment_type` | `payment_type_bytes` | 0–8 |
| 7 | `fraction` | `fraction_bytes` | 0–8 |
| 8 | `date_label` | `date_label_bytes` | 0–32 |
| 9 | `related_event` | `related_event_bytes` | 0–8 |
| 10 | `related_event_id` | `related_event_id_bytes` | 0–32 |
| 11 | `event_id` | `event_id_bytes` | 1–32 |
| 12 | `unique_id` | `unique_id_bytes` | 1–48 |
| 13 | `rate_currency` | `rate_currency_bytes` | 0–16 |
| 14 | `outturn_isin` | `outturn_isin_bytes` | 0 or 12 |
| 15 | `details` | `details_bytes` | 0–65535 |

Allowed flag bits: `action_flags` bit 0 (mask 1).

<!-- END GENERATED -->

## Container, metadata, frame, index, and termination fields

The following tables reproduce the outer layouts so field coverage includes more than market payloads. Header CRCs zero only their own CRC field during calculation; the other checksum fields remain included. Examples for these fields are in `fixtures/container-fields.json`.

### Container header — 64 bytes

| Offset | Bytes | Type | Field | Meaning |
|---:|---:|---|---|---|
| 0 | 8 | bytes | magic | `4e 57 54 42 49 4e 0d 0a` (`NWTBIN\r\n`) |
| 8 | 2 | u16 | major | 1 |
| 10 | 2 | u16 | minor | 0, or 1 when the manifest declares any standard type 10–22 |
| 12 | 2 | u16 | header_bytes | 64 |
| 14 | 2 | u16 | flags | 0 |
| 16 | 4 | u32 | metadata_bytes | Total padded metadata size |
| 20 | 4 | u32 | metadata_crc32c | CRC of all metadata bytes including padding |
| 24 | 16 | bytes | stream_id | Opaque nonzero 128-bit identifier |
| 40 | 8 | u64 | created_ns | Creation time, or null |
| 48 | 8 | u64 | reserved | 0 |
| 56 | 4 | u32 | header_crc32c | CRC of 64 bytes with this field zero |
| 60 | 4 | u32 | reserved | 0 |

### Frame header — 64 bytes

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

### INDEX entry — 40 bytes

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 0 | 8 | u64 | data_frame_seq |
| 8 | 8 | u64 | data_frame_offset, absolute from container byte 0 |
| 16 | 8 | u64 | min_event_ns |
| 24 | 8 | u64 | max_event_ns |
| 32 | 4 | u32 | raw_bytes |
| 36 | 4 | u32 | record_count |

### END payload — 32 bytes

| Offset | Bytes | Type | Field |
|---:|---:|---|---|
| 0 | 8 | u64 | first_index_offset, or 0 when absent |
| 8 | 8 | u64 | total_data_frames |
| 16 | 8 | u64 | total_records in DATA frames |
| 24 | 4 | u32 | completion_status: 0 normal; 1 producer-aborted |
| 28 | 4 | u32 | reserved |

### Metadata TLV header — 8 bytes

| Offset | Field | Width | Meaning / constraint |
|---:|---|---:|---|
| 0 | type | u16 | 1 MANIFEST, 2 PROVENANCE, or a permitted private/unknown type |
| 2 | flags | u16 | Bit 0 REQUIRED; other bits zero |
| 4 | value_bytes | u32 | Length of value only; excludes this header and padding |
| 8 | value | bytes[value_bytes] | JSON for standard metadata types |
| 8+value_bytes | padding | 0–7 bytes | Zero bytes to align8(8+value_bytes) |

### MANIFEST JSON fields — required properties

| Property | Type | Meaning / constraints |
|---|---|---|
| dataset | string | Stable namespace; 1–255 UTF-8 bytes |
| producer | string | Producer/version; 1–255 bytes |
| profile | string | market-data or generic-events; this kit uses market-data |
| clock | string | posix-ns |
| publishers | array | At most 4096; unique nonzero u32 IDs |
| publishers[].id | integer | Namespace referenced by publisher_id |
| publishers[].name | string | 1–255 bytes |
| publishers[].venue | string | 0–255 bytes |
| schemas | array | 1–4096 unique (type,version) entries |
| schemas[].type | integer | Record type, 1–65534 |
| schemas[].version | integer | 1–255; 1 for this draft's standard schemas |
| schemas[].required | boolean | Unknown required schema blocks semantic decoding. BOOK_DELTA must be true; FRAME_SUMMARY must be false |
| schemas[].name | string | 1–255 bytes; standard schema name |
| schemas[].spec_uri | string | 1–2048 bytes; `urn:nwt:spec:1.0` for types 1–9, `urn:nwt:spec:1.1` for types 10–22 |

### MANIFEST JSON fields — optional property

| Property | Type | Meaning / constraints |
|---|---|---|
| ordering | string | `none` (default), `ts_event` or `instrument,ts_event`. A claim about byte order that a validator checks. See [specification §5.2](SPECIFICATION.md). |

Optional PROVENANCE string properties are `source_format`, `source_version`, `converter`, `conversion_policy`, `clock_policy`, and `license_reference`, each at most 4096 UTF-8 bytes. These are descriptive properties, not instructions or unit overrides. Any optional future properties must obey the JSON constraints in the specification. No source credentials belong in metadata.

## Common interpretation mistakes

- `record_bytes` counts the header; `stored_bytes` and `raw_bytes` do not count the frame header.
- `stored_bytes` excludes frame padding. `metadata_bytes` includes every TLV's padding.
- `min_event_ns` is the minimum of all non-null record event times in the frame, not necessarily the first record's timestamp.
- The same `UINT64_MAX` bit pattern can mean null time/quantity/priority, but an order or trade ID may legally have that value.
- A null ask price requires zero ask size/count, not null size/count.
- A MODIFY carries absolute remaining quantity. A TRADE does not implicitly reduce the MBO book.
- Instrument definitions apply in byte order. Sorting all records by ts_event changes interpretation.
- Replay/SUSPECT flags do not replace sequence checks, CRC checks, or gap recovery.
- A record-only `.bin` fixture has no outer CRC or manifest. Use a `.nwt` container for transfer.
- A text length counts UTF-8 bytes. A 255-byte limit accepts 127 two-byte characters plus one ASCII byte, and rejects one more byte.
- `shares_outstanding` (SECURITY_DEF) is a whole share count, not a value scaled by 10^9. `round_lot`, `order_count`, `option_id` and `serial_id` are plain counts too. `interval_ns` (BEST_QUOTE) is a duration, not a timestamp.
- A `reserved` field may occur more than once in one type (LISTING, SYMBOL_MAP, TRADE_QUOTE, FRAME_SUMMARY, CORPORATE_ACTION). Every one must be zero.
- A null `ts_event` is allowed on some reference records (for example LISTING in the synthetic catalog). A frame whose records all have a null `ts_event` has null frame bounds.
- STATISTICS `quantity` and `price` are both always present on the wire; which one is null depends on `stat_type` and `action`.
- BEST_QUOTE and TRADE_QUOTE keep their own state. They do not replace QUOTE state.
- `details` (CORPORATE_ACTION) is text to the codec. Whether it is one JSON object with sorted keys is a rule for producers and the state checker.
