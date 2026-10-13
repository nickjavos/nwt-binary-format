#pragma once
// Generated example inputs. Numeric field values are decimal strings.
inline constexpr const char* schema_json = R"NWTDATA({
  "format": "NWT",
  "revision": "1.1-draft.1",
  "header": [
    {
      "name": "record_bytes",
      "bytes": 4,
      "signed": false,
      "meaning": "Total bytes from record start through final padding, including the 48-byte common header. Derived by encoder; multiple of 8, maximum 1 MiB."
    },
    {
      "name": "record_type",
      "bytes": 2,
      "signed": false,
      "meaning": "Standard schema identifier 1\u201322. Selects payload layout. It is not a source exchange message ID."
    },
    {
      "name": "schema_version",
      "bytes": 1,
      "signed": false,
      "meaning": "Exactly 1 for every standard schema in this draft. A different version is a different wire contract."
    },
    {
      "name": "flags",
      "bytes": 1,
      "signed": false,
      "meaning": "Bit 0 REPLAY; bit 1 SUSPECT. All other bits zero. Flags do not alter byte layout or waive validation."
    },
    {
      "name": "publisher_id",
      "bytes": 4,
      "signed": false,
      "meaning": "Producer-assigned publisher namespace. Nonzero for types 1\u20138, 10\u201319 and 21\u201322. SYSTEM may use 0 with channel 0; FRAME_SUMMARY always does."
    },
    {
      "name": "channel_id",
      "bytes": 4,
      "signed": false,
      "meaning": "Logical producer partition. Zero is valid. Sequence continuity is checked independently per publisher/channel."
    },
    {
      "name": "instrument_id",
      "bytes": 8,
      "signed": false,
      "meaning": "Opaque instrument identity scoped by dataset and publisher. Nonzero for types 1\u20137, 11\u201319 and 21\u201322; zero for GAP, SYSTEM, VENUE_DEF and FRAME_SUMMARY."
    },
    {
      "name": "ts_event",
      "bytes": 8,
      "signed": false,
      "kind": "time",
      "meaning": "Source event time in POSIX nanoseconds; UINT64_MAX means unavailable. BAR requires interval end. It may move backward."
    },
    {
      "name": "ts_recv",
      "bytes": 8,
      "signed": false,
      "kind": "time",
      "meaning": "Producer capture time in POSIX nanoseconds; UINT64_MAX means unavailable. No assumption that it exceeds event time."
    },
    {
      "name": "sequence",
      "bytes": 8,
      "signed": false,
      "meaning": "Normalized output position per container/publisher/channel. Starts at 1, increments by one, never wraps. Not the exchange sequence."
    }
  ],
  "level": [
    {
      "name": "bid_price",
      "bytes": 8,
      "signed": true,
      "kind": "price",
      "meaning": "Signed bid price \u00d7 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero."
    },
    {
      "name": "ask_price",
      "bytes": 8,
      "signed": true,
      "kind": "price",
      "meaning": "Signed ask price \u00d7 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero."
    },
    {
      "name": "bid_quantity",
      "bytes": 8,
      "signed": false,
      "kind": "quantity",
      "meaning": "Bid size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
    },
    {
      "name": "ask_quantity",
      "bytes": 8,
      "signed": false,
      "kind": "quantity",
      "meaning": "Ask size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
    },
    {
      "name": "bid_count",
      "bytes": 4,
      "signed": false,
      "meaning": "Integral bid order count for this level. Same presence/null rules as bid_order_count."
    },
    {
      "name": "ask_count",
      "bytes": 4,
      "signed": false,
      "meaning": "Integral ask order count for this level. Same presence/null rules as ask_order_count."
    },
    {
      "name": "reserved",
      "bytes": 8,
      "signed": false,
      "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
    }
  ],
  "schemas": [
    {
      "type": 1,
      "name": "TRADE",
      "version": 1,
      "fixed_bytes": 88,
      "fields": [
        {
          "name": "price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed currency amount \u00d7 10^9. INT64_MIN is null. Negative and zero prices are allowed unless a specific action requires null."
        },
        {
          "name": "quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Nonnegative quantity in definition units \u00d7 10^9. UINT64_MAX is null. Action-specific rules distinguish positive size, zero, and null."
        },
        {
          "name": "trade_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Nonzero trade identity within instrument/publisher/channel/container. Remains stable through correction and cancellation."
        },
        {
          "name": "original_sequence",
          "bytes": 8,
          "signed": false,
          "meaning": "0 for NEW. CANCEL/CORRECT reference the original NEW sequence in the same scope, not the previous correction."
        },
        {
          "name": "action",
          "bytes": 1,
          "signed": false,
          "meaning": "1 NEW, 2 CANCEL, 3 CORRECT. NEW introduces a trade; CORRECT replaces its values; CANCEL terminates it."
        },
        {
          "name": "aggressor",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unknown, 1 buyer, 2 seller. This is aggressor direction, not resting-order book side. CANCEL requires 0."
        },
        {
          "name": "conditions",
          "bytes": 2,
          "signed": false,
          "meaning": "Bit 0 off-book. All other bits zero. CANCEL requires zero."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false
    },
    {
      "type": 2,
      "name": "QUOTE",
      "version": 1,
      "fixed_bytes": 96,
      "fields": [
        {
          "name": "bid_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed bid price \u00d7 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero."
        },
        {
          "name": "ask_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed ask price \u00d7 10^9. INT64_MIN means this side/level is absent; then its size and count must both be zero."
        },
        {
          "name": "bid_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Bid size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
        },
        {
          "name": "ask_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Ask size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
        },
        {
          "name": "bid_order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral bid order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0."
        },
        {
          "name": "ask_order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral ask order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0."
        },
        {
          "name": "quote_flags",
          "bytes": 4,
          "signed": false,
          "meaning": "Bit 0 indicative. All other bits zero. This is a complete replacement of both quote sides."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false
    },
    {
      "type": 3,
      "name": "BAR",
      "version": 1,
      "fixed_bytes": 112,
      "fields": [
        {
          "name": "interval_start_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Inclusive start of a completed bar, POSIX ns, non-null and strictly less than interval_end_ns."
        },
        {
          "name": "interval_end_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Exclusive end of a completed bar, POSIX ns, non-null. Equal to common ts_event."
        },
        {
          "name": "open",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "First trade price \u00d7 10^9 under the aggregation policy. Null only for empty bars."
        },
        {
          "name": "high",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Maximum trade price \u00d7 10^9. Must be at least open and close; null only for empty bars."
        },
        {
          "name": "low",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Minimum trade price \u00d7 10^9. Must be at most open and close; null only for empty bars."
        },
        {
          "name": "close",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Last trade price \u00d7 10^9 under the aggregation policy. Null only for empty bars."
        },
        {
          "name": "volume",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Traded quantity \u00d7 10^9, not currency turnover. Positive/non-null for nonempty bars; zero for empty bars."
        },
        {
          "name": "trade_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Positive integral count for nonempty bars; zero for empty bars. UINT32_MAX is not valid for this schema."
        },
        {
          "name": "bar_flags",
          "bytes": 4,
          "signed": false,
          "meaning": "Bit 0 empty. Empty bars have four null prices, zero volume, and zero count. All other bits zero."
        }
      ],
      "texts": [],
      "has_levels": false
    },
    {
      "type": 4,
      "name": "MBO",
      "version": 1,
      "fixed_bytes": 88,
      "fields": [
        {
          "name": "order_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Nonzero live-order key in the book scope. 0 only for CLEAR, SNAPSHOT_BEGIN, SNAPSHOT_END. IDs may be reused after deletion."
        },
        {
          "name": "price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed currency amount \u00d7 10^9. INT64_MIN is null. Negative and zero prices are allowed unless a specific action requires null."
        },
        {
          "name": "quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Nonnegative quantity in definition units \u00d7 10^9. UINT64_MAX is null. Action-specific rules distinguish positive size, zero, and null."
        },
        {
          "name": "priority",
          "bytes": 8,
          "signed": false,
          "meaning": "Ascending queue rank/key. UINT64_MAX means unknown. Lower known values have earlier priority at one side/price."
        },
        {
          "name": "action",
          "bytes": 1,
          "signed": false,
          "meaning": "1 ADD, 2 MODIFY, 3 DELETE, 4 CLEAR, 5 SNAPSHOT_BEGIN, 6 SNAPSHOT_END. MODIFY sets absolute remaining size, never a delta."
        },
        {
          "name": "side",
          "bytes": 1,
          "signed": false,
          "meaning": "0 none/control, 1 bid, 2 ask. ADD/MODIFY require bid/ask; DELETE and snapshot/control actions require 0."
        },
        {
          "name": "mbo_flags",
          "bytes": 2,
          "signed": false,
          "meaning": "Zero in v1.0. No implied execution, partial-fill, or snapshot bits."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false
    },
    {
      "type": 5,
      "name": "BOOK_SNAPSHOT",
      "version": 1,
      "fixed_bytes": 56,
      "fields": [
        {
          "name": "levels",
          "bytes": 2,
          "signed": false,
          "meaning": "Number of 48-byte paired bid/ask elements, 0\u20131024. Encoder derives it from the level array. Unequal depths use absent-side suffixes."
        },
        {
          "name": "book_flags",
          "bytes": 2,
          "signed": false,
          "meaning": "Bit 0 depth-limited: deeper prices may exist. All other bits zero. Zero levels is a valid empty observed book."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": true
    },
    {
      "type": 6,
      "name": "INSTRUMENT_DEF",
      "version": 1,
      "fixed_bytes": 112,
      "fields": [
        {
          "name": "price_increment",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Minimum fixed price step \u00d7 10^9; positive or INT64_MIN (unknown/variable schedule). Does not change wire scale."
        },
        {
          "name": "quantity_increment",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Quantity step in definition units \u00d7 10^9; positive or UINT64_MAX (unknown). Does not change wire scale."
        },
        {
          "name": "contract_multiplier",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed fixed-point multiplier \u00d7 10^9; positive or INT64_MIN (unknown). No universal cash-value formula is implied."
        },
        {
          "name": "expiration_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Expiration instant in POSIX ns; UINT64_MAX if unavailable/not applicable."
        },
        {
          "name": "underlying_instrument_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Same-publisher instrument ID; 0 when absent. Underlying definition need not be included in the container."
        },
        {
          "name": "strike",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Strike price \u00d7 10^9; INT64_MIN if unavailable/not applicable. Not enough information to infer option right/style."
        },
        {
          "name": "asset_class",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unspecified, 1 equity, 2 future, 3 option, 4 FX, 5 crypto, 6 index, 7 fixed income."
        },
        {
          "name": "reserved",
          "bytes": 7,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of symbol, 1\u2013255. Computed, not character count."
        },
        {
          "name": "venue_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of venue, 0\u2013255. Empty is allowed."
        },
        {
          "name": "currency_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of currency code, 1\u201316."
        },
        {
          "name": "quantity_unit_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of quantity-unit code, 1\u201332."
        }
      ],
      "texts": [
        "symbol",
        "venue",
        "currency",
        "quantity_unit"
      ],
      "has_levels": false,
      "text_limits": {
        "symbol": [
          1,
          255
        ],
        "venue": [
          0,
          255
        ],
        "currency": [
          1,
          16
        ],
        "quantity_unit": [
          1,
          32
        ]
      }
    },
    {
      "type": 7,
      "name": "STATUS",
      "version": 1,
      "fixed_bytes": 64,
      "fields": [
        {
          "name": "status",
          "bytes": 2,
          "signed": false,
          "meaning": "0 unknown, 1 pre-open, 2 open, 3 halted, 4 closed, 5 auction. Replacement administrative state; does not clear books."
        },
        {
          "name": "reason",
          "bytes": 2,
          "signed": false,
          "meaning": "0 unspecified, 1 scheduled, 2 volatility, 3 regulatory, 4 technical."
        },
        {
          "name": "status_flags",
          "bytes": 4,
          "signed": false,
          "meaning": "Zero in v1.0."
        },
        {
          "name": "reserved",
          "bytes": 8,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false
    },
    {
      "type": 8,
      "name": "GAP",
      "version": 1,
      "fixed_bytes": 80,
      "fields": [
        {
          "name": "first_missing_source_sequence",
          "bytes": 8,
          "signed": false,
          "meaning": "Inclusive first missing source-native sequence, or UINT64_MAX when unknown. Both endpoints must be null together."
        },
        {
          "name": "last_missing_source_sequence",
          "bytes": 8,
          "signed": false,
          "meaning": "Inclusive last missing source-native sequence, or UINT64_MAX when unknown. If known, first \u2264 last."
        },
        {
          "name": "reason",
          "bytes": 4,
          "signed": false,
          "meaning": "1 source packet loss, 2 source reset, 3 producer overflow, 4 unknown discontinuity."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "recovery_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Nonzero identifier unique among GAP records in this container. Diagnostic correlation only; not a snapshot ID."
        }
      ],
      "texts": [],
      "has_levels": false
    },
    {
      "type": 9,
      "name": "SYSTEM",
      "version": 1,
      "fixed_bytes": 64,
      "fields": [
        {
          "name": "code",
          "bytes": 2,
          "signed": false,
          "meaning": "1 heartbeat, 2 info, 3 warning, 4 error. SYSTEM error does not replace END."
        },
        {
          "name": "text_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of text, 0\u20134096. Heartbeat requires 0."
        },
        {
          "name": "severity",
          "bytes": 1,
          "signed": false,
          "meaning": "0 info for heartbeat/info, 1 for warning, 2 for error. Must agree with code."
        },
        {
          "name": "reserved",
          "bytes": 3,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "related_recovery_id",
          "bytes": 8,
          "signed": false,
          "meaning": "0 or a previously emitted GAP recovery ID. Heartbeat requires 0."
        }
      ],
      "texts": [
        "text"
      ],
      "has_levels": false,
      "text_limits": {
        "text": [
          0,
          4096
        ]
      }
    },
    {
      "type": 10,
      "name": "VENUE_DEF",
      "version": 1,
      "fixed_bytes": 96,
      "fields": [
        {
          "name": "created_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Date the venue record was created, midnight UTC of the source date in POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "updated_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Date of the last change to the venue record, midnight UTC in POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "expiry_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Date the venue code expires, midnight UTC in POSIX ns; UINT64_MAX when the venue has no expiry."
        },
        {
          "name": "kind",
          "bytes": 1,
          "signed": false,
          "meaning": "1 operating venue, 2 market segment. An operating venue requires mic equal to operating_mic."
        },
        {
          "name": "status",
          "bytes": 1,
          "signed": false,
          "meaning": "1 active, 2 updated, 3 expired."
        },
        {
          "name": "mic_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of mic, exactly 4. Computed, not character count."
        },
        {
          "name": "operating_mic_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of operating_mic, exactly 4. Computed, not character count."
        },
        {
          "name": "country_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of country, exactly 2. Computed, not character count."
        },
        {
          "name": "category_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of category, 0 or 4. Computed, not character count."
        },
        {
          "name": "acronym_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of acronym, 0\u201364. Computed, not character count."
        },
        {
          "name": "city_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of city, 0\u2013128. Computed, not character count."
        },
        {
          "name": "name_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of name, 1\u2013255. Computed, not character count."
        },
        {
          "name": "legal_entity_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of legal_entity, 0\u2013255. Computed, not character count."
        },
        {
          "name": "lei_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of lei, 0 or 20. Computed, not character count."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [
        "mic",
        "operating_mic",
        "country",
        "category",
        "acronym",
        "city",
        "name",
        "legal_entity",
        "lei"
      ],
      "has_levels": false,
      "enums": {
        "kind": [
          1,
          2
        ],
        "status": [
          1,
          2,
          3
        ]
      },
      "text_limits": {
        "mic": [
          4,
          4
        ],
        "operating_mic": [
          4,
          4
        ],
        "country": [
          2,
          2
        ],
        "acronym": [
          0,
          64
        ],
        "city": [
          0,
          128
        ],
        "name": [
          1,
          255
        ],
        "legal_entity": [
          0,
          255
        ]
      },
      "text_exact": {
        "category": [
          0,
          4
        ],
        "lei": [
          0,
          20
        ]
      }
    },
    {
      "type": 11,
      "name": "OPTION_DEF",
      "version": 1,
      "fixed_bytes": 96,
      "fields": [
        {
          "name": "underlying_instrument_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Same-publisher instrument ID of the underlying; 0 when it has no ID in this namespace, which requires a non-empty underlying_symbol."
        },
        {
          "name": "expiration_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Expiration instant in POSIX ns. Non-null. Equals the INSTRUMENT_DEF expiration when one exists."
        },
        {
          "name": "strike",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Strike price \u00d7 10^9. Non-null. Equals the INSTRUMENT_DEF strike when one exists."
        },
        {
          "name": "contract_multiplier",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed fixed-point multiplier \u00d7 10^9; positive or INT64_MIN (unknown)."
        },
        {
          "name": "right",
          "bytes": 1,
          "signed": false,
          "meaning": "1 call, 2 put."
        },
        {
          "name": "exercise_style",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unknown, 1 American, 2 European. Never inferred from the symbol."
        },
        {
          "name": "settlement",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unknown, 1 physical, 2 cash. Never inferred from the symbol."
        },
        {
          "name": "closing_type",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unknown, 1 normal hours, 2 late hours."
        },
        {
          "name": "option_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 pending; bit 1 adjusted (non-standard deliverable). All other bits zero."
        },
        {
          "name": "reserved",
          "bytes": 3,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "root_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of root, 1\u201316. Computed, not character count."
        },
        {
          "name": "underlying_symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of underlying_symbol, 0\u2013255. Computed, not character count."
        },
        {
          "name": "osi_symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of osi_symbol, 0 or 21. Computed, not character count."
        },
        {
          "name": "currency_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of currency, 0\u201316. Computed, not character count."
        }
      ],
      "texts": [
        "root",
        "underlying_symbol",
        "osi_symbol",
        "currency"
      ],
      "has_levels": false,
      "enums": {
        "right": [
          1,
          2
        ],
        "exercise_style": [
          0,
          1,
          2
        ],
        "settlement": [
          0,
          1,
          2
        ],
        "closing_type": [
          0,
          1,
          2
        ]
      },
      "masks": {
        "option_flags": 3
      },
      "text_limits": {
        "root": [
          1,
          16
        ],
        "underlying_symbol": [
          0,
          255
        ],
        "currency": [
          0,
          16
        ]
      },
      "text_exact": {
        "osi_symbol": [
          0,
          21
        ]
      }
    },
    {
      "type": 12,
      "name": "LISTING",
      "version": 1,
      "fixed_bytes": 72,
      "fields": [
        {
          "name": "round_lot",
          "bytes": 4,
          "signed": false,
          "meaning": "Round-lot size as an integral count of units; UINT32_MAX if unavailable. Not scaled by 10^9."
        },
        {
          "name": "listing_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 ETF; bit 1 test issue; bit 2 NextShares. All other bits zero."
        },
        {
          "name": "market_tier",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unspecified, 1 global select, 2 global, 3 capital."
        },
        {
          "name": "financial_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 reported; bit 1 deficient; bit 2 delinquent; bit 3 bankrupt. Bits 1\u20133 require bit 0. Value 1 is normal; 0 means the source reports no financial status."
        },
        {
          "name": "reserved",
          "bytes": 1,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of symbol, 1\u2013255. Computed, not character count."
        },
        {
          "name": "name_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of name, 0\u2013512. Computed, not character count."
        },
        {
          "name": "listing_mic_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of listing_mic, 0 or 4. Computed, not character count."
        },
        {
          "name": "cqs_symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of cqs_symbol, 0\u2013255. Computed, not character count."
        },
        {
          "name": "alt_symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of alt_symbol, 0\u2013255. Computed, not character count."
        },
        {
          "name": "reserved",
          "bytes": 6,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [
        "symbol",
        "name",
        "listing_mic",
        "cqs_symbol",
        "alt_symbol"
      ],
      "has_levels": false,
      "enums": {
        "market_tier": [
          0,
          1,
          2,
          3
        ]
      },
      "masks": {
        "listing_flags": 7,
        "financial_flags": 15
      },
      "text_limits": {
        "symbol": [
          1,
          255
        ],
        "name": [
          0,
          512
        ],
        "cqs_symbol": [
          0,
          255
        ],
        "alt_symbol": [
          0,
          255
        ]
      },
      "text_exact": {
        "listing_mic": [
          0,
          4
        ]
      }
    },
    {
      "type": 13,
      "name": "STATISTICS",
      "version": 1,
      "fixed_bytes": 80,
      "fields": [
        {
          "name": "ts_ref",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Start of the session or date the value refers to, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Value \u00d7 10^9 for price statistics (types 1\u20136). Non-null for SET of a price type; INT64_MIN otherwise."
        },
        {
          "name": "quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Value \u00d7 10^9 for quantity statistics (types 7\u20138). Non-null for SET of a quantity type; UINT64_MAX otherwise."
        },
        {
          "name": "stat_type",
          "bytes": 2,
          "signed": false,
          "meaning": "1 open, 2 high, 3 low, 4 close, 5 settlement, 6 VWAP (price types); 7 volume, 8 open interest (quantity types)."
        },
        {
          "name": "action",
          "bytes": 1,
          "signed": false,
          "meaning": "1 SET, 2 DELETE. SET replaces the value for (instrument, stat_type, ts_ref); DELETE withdraws it and requires both values null."
        },
        {
          "name": "stat_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 preliminary. All other bits zero. DELETE requires zero."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false,
      "enums": {
        "stat_type": [
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          8
        ],
        "action": [
          1,
          2
        ]
      },
      "masks": {
        "stat_flags": 1
      }
    },
    {
      "type": 14,
      "name": "OPTION_ANALYTICS",
      "version": 1,
      "fixed_bytes": 120,
      "fields": [
        {
          "name": "implied_volatility",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Annualised implied volatility \u00d7 10^9 (1.0 = 100%). INT64_MIN is null; otherwise not negative."
        },
        {
          "name": "delta",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Delta \u00d7 10^9. INT64_MIN is null; otherwise within \u22121 to +1."
        },
        {
          "name": "gamma",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Gamma \u00d7 10^9, per 1.00 move in the underlying. INT64_MIN is null; otherwise not negative."
        },
        {
          "name": "theta",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Theta \u00d7 10^9, currency per calendar day. INT64_MIN is null."
        },
        {
          "name": "vega",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Vega \u00d7 10^9, currency per 0.01 change in volatility. INT64_MIN is null."
        },
        {
          "name": "rho",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Rho \u00d7 10^9, currency per 0.01 change in rate. INT64_MIN is null."
        },
        {
          "name": "underlying_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Underlying price \u00d7 10^9 used for the calculation. INT64_MIN is null."
        },
        {
          "name": "theoretical_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Model price of the option \u00d7 10^9. INT64_MIN is null."
        },
        {
          "name": "price_basis",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unspecified, 1 mid, 2 last, 3 bid, 4 ask, 5 settlement."
        },
        {
          "name": "model",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unspecified, 1 Black-Scholes-Merton, 2 Black-76, 3 binomial, 4 other."
        },
        {
          "name": "reserved",
          "bytes": 6,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false,
      "enums": {
        "price_basis": [
          0,
          1,
          2,
          3,
          4,
          5
        ],
        "model": [
          0,
          1,
          2,
          3,
          4
        ]
      }
    },
    {
      "type": 15,
      "name": "BOOK_DELTA",
      "version": 1,
      "fixed_bytes": 72,
      "fields": [
        {
          "name": "price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Level price \u00d7 10^9. Non-null for SET and DELETE; INT64_MIN for CLEAR. Levels are keyed by price, not rank."
        },
        {
          "name": "quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "New aggregate size at this price \u00d7 10^9. SET: 1 through UINT64_MAX\u22121. DELETE and CLEAR: 0."
        },
        {
          "name": "order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral order count at the level; UINT32_MAX if unknown. DELETE and CLEAR require UINT32_MAX."
        },
        {
          "name": "action",
          "bytes": 1,
          "signed": false,
          "meaning": "1 SET, 2 DELETE, 3 CLEAR. SET adds or replaces a level; CLEAR empties one side or the whole book."
        },
        {
          "name": "side",
          "bytes": 1,
          "signed": false,
          "meaning": "1 bid, 2 ask, 0 both. 0 is valid only for CLEAR."
        },
        {
          "name": "delta_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 LAST_IN_EVENT: the last delta of one source event. All other bits zero."
        },
        {
          "name": "reserved",
          "bytes": 1,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false,
      "enums": {
        "action": [
          1,
          2,
          3
        ],
        "side": [
          0,
          1,
          2
        ]
      },
      "masks": {
        "delta_flags": 1
      }
    },
    {
      "type": 16,
      "name": "IMBALANCE",
      "version": 1,
      "fixed_bytes": 104,
      "fields": [
        {
          "name": "auction_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Scheduled auction time in POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "reference_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Reference price \u00d7 10^9 for the imbalance. Non-null."
        },
        {
          "name": "near_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Indicative price \u00d7 10^9 from auction and continuous interest; INT64_MIN if unavailable."
        },
        {
          "name": "far_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Indicative price \u00d7 10^9 from auction interest only; INT64_MIN if unavailable."
        },
        {
          "name": "paired_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Quantity \u00d7 10^9 matched at the reference price; UINT64_MAX if unavailable."
        },
        {
          "name": "imbalance_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Unmatched quantity \u00d7 10^9. Non-null; zero exactly when imbalance_side is 0."
        },
        {
          "name": "imbalance_side",
          "bytes": 1,
          "signed": false,
          "meaning": "0 none, 1 buy, 2 sell."
        },
        {
          "name": "auction_type",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unspecified, 1 opening, 2 closing, 3 reopening, 4 IPO, 5 intraday."
        },
        {
          "name": "reserved",
          "bytes": 6,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false,
      "enums": {
        "imbalance_side": [
          0,
          1,
          2
        ],
        "auction_type": [
          0,
          1,
          2,
          3,
          4,
          5
        ]
      }
    },
    {
      "type": 17,
      "name": "SYMBOL_MAP",
      "version": 1,
      "fixed_bytes": 72,
      "fields": [
        {
          "name": "valid_from_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Inclusive start of the mapping interval in POSIX ns. Non-null."
        },
        {
          "name": "valid_to_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Exclusive end of the mapping interval in POSIX ns; UINT64_MAX means open-ended. Otherwise greater than valid_from_ns."
        },
        {
          "name": "symbology",
          "bytes": 1,
          "signed": false,
          "meaning": "1 native, 2 OSI, 3 ISIN, 4 FIGI, 5 root, 6 continuous. Root is one-to-many; the others name one instrument at any time."
        },
        {
          "name": "reserved",
          "bytes": 1,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of symbol, 1\u2013255. Computed, not character count."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [
        "symbol"
      ],
      "has_levels": false,
      "enums": {
        "symbology": [
          1,
          2,
          3,
          4,
          5,
          6
        ]
      },
      "text_limits": {
        "symbol": [
          1,
          255
        ]
      }
    },
    {
      "type": 18,
      "name": "TRADE_QUOTE",
      "version": 1,
      "fixed_bytes": 120,
      "fields": [
        {
          "name": "price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Trade price \u00d7 10^9. Non-null."
        },
        {
          "name": "quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Trade size \u00d7 10^9. Positive and non-null."
        },
        {
          "name": "trade_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Trade identity within instrument/publisher/channel/container; 0 when unknown."
        },
        {
          "name": "bid_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed bid price \u00d7 10^9. INT64_MIN means the bid side is absent; then its size and count must both be zero."
        },
        {
          "name": "ask_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed ask price \u00d7 10^9. INT64_MIN means the ask side is absent; then its size and count must both be zero."
        },
        {
          "name": "bid_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Bid size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
        },
        {
          "name": "ask_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Ask size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
        },
        {
          "name": "bid_order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral bid order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0."
        },
        {
          "name": "ask_order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral ask order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0."
        },
        {
          "name": "aggressor",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unknown, 1 buyer, 2 seller. Aggressor direction, not resting-order book side."
        },
        {
          "name": "reserved",
          "bytes": 1,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "conditions",
          "bytes": 2,
          "signed": false,
          "meaning": "Bit 0 off-book. All other bits zero."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false,
      "enums": {
        "aggressor": [
          0,
          1,
          2
        ]
      },
      "masks": {
        "conditions": 1
      }
    },
    {
      "type": 19,
      "name": "BEST_QUOTE",
      "version": 1,
      "fixed_bytes": 112,
      "fields": [
        {
          "name": "bid_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed bid price \u00d7 10^9. INT64_MIN means the bid side is absent; then its size and count must both be zero."
        },
        {
          "name": "ask_price",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Signed ask price \u00d7 10^9. INT64_MIN means the ask side is absent; then its size and count must both be zero."
        },
        {
          "name": "bid_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Bid size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
        },
        {
          "name": "ask_quantity",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Ask size \u00d7 10^9. Present side requires 1 through UINT64_MAX\u22121; absent side requires 0."
        },
        {
          "name": "bid_order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral bid order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0."
        },
        {
          "name": "ask_order_count",
          "bytes": 4,
          "signed": false,
          "meaning": "Integral ask order count. Present side: positive or UINT32_MAX (unknown). Absent side: 0."
        },
        {
          "name": "quote_flags",
          "bytes": 4,
          "signed": false,
          "meaning": "Bit 0 indicative. All other bits zero."
        },
        {
          "name": "bid_publisher_id",
          "bytes": 4,
          "signed": false,
          "meaning": "Declared publisher that set the bid; 0 when the side is absent or the venue is unknown."
        },
        {
          "name": "ask_publisher_id",
          "bytes": 4,
          "signed": false,
          "meaning": "Declared publisher that set the ask; 0 when the side is absent or the venue is unknown."
        },
        {
          "name": "reserved",
          "bytes": 4,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "interval_ns",
          "bytes": 8,
          "signed": false,
          "meaning": "0 for an event-driven quote; otherwise the sampling interval in ns, with ts_event at the interval end. A duration, not a timestamp."
        }
      ],
      "texts": [],
      "has_levels": false,
      "masks": {
        "quote_flags": 1
      }
    },
    {
      "type": 20,
      "name": "FRAME_SUMMARY",
      "version": 1,
      "fixed_bytes": 104,
      "fields": [
        {
          "name": "data_frame_seq",
          "bytes": 8,
          "signed": false,
          "meaning": "frame_seq of the DATA frame this record describes."
        },
        {
          "name": "data_frame_offset",
          "bytes": 8,
          "signed": false,
          "meaning": "Byte offset of that frame header, absolute from container byte 0."
        },
        {
          "name": "stored_bytes",
          "bytes": 4,
          "signed": false,
          "meaning": "stored_bytes of that frame, so its payload can be fetched in one read."
        },
        {
          "name": "codec",
          "bytes": 1,
          "signed": false,
          "meaning": "Codec of that frame: 0 raw, 1 Zstd."
        },
        {
          "name": "summary_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0: the frame has a record with null ts_event. Bit 1: non-null ts_event is non-decreasing within the frame. All other bits zero."
        },
        {
          "name": "reserved",
          "bytes": 2,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "type_mask",
          "bytes": 8,
          "signed": false,
          "meaning": "Bit n (1\u201363) set when standard record type n is present in the frame; bit 0 set when any other type is present."
        },
        {
          "name": "min_instrument_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Smallest non-zero instrument ID in the frame; 0 when none."
        },
        {
          "name": "max_instrument_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Largest non-zero instrument ID in the frame; 0 when none."
        },
        {
          "name": "reserved",
          "bytes": 8,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [],
      "has_levels": false,
      "enums": {
        "codec": [
          0,
          1
        ]
      },
      "masks": {
        "summary_flags": 3
      }
    },
    {
      "type": 21,
      "name": "SECURITY_DEF",
      "version": 1,
      "fixed_bytes": 216,
      "fields": [
        {
          "name": "listing_group_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier that groups the listings of one security; 0 when none."
        },
        {
          "name": "security_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier of the security; 0 when none."
        },
        {
          "name": "issuer_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier of the issuer; 0 when none."
        },
        {
          "name": "listing_created_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "When the listing record was created at the source, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "listing_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Listing date, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "delisting_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Delisting date, POSIX ns; UINT64_MAX when the listing is not delisted or the date is unavailable."
        },
        {
          "name": "shares_outstanding",
          "bytes": 8,
          "signed": false,
          "meaning": "Shares outstanding as a whole count, not scaled by 10^9 (large issuers exceed the scaled range); UINT64_MAX if unavailable."
        },
        {
          "name": "shares_outstanding_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Date the shares-outstanding figure refers to, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "lot_size",
          "bytes": 8,
          "signed": false,
          "kind": "quantity",
          "meaning": "Trading lot size \u00d7 10^9; UINT64_MAX if unavailable."
        },
        {
          "name": "par_value",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Par value \u00d7 10^9 in par_value_currency; INT64_MIN if unavailable."
        },
        {
          "name": "votes_per_share",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Votes per share \u00d7 10^9; INT64_MIN if unavailable."
        },
        {
          "name": "cik",
          "bytes": 8,
          "signed": false,
          "meaning": "Regulatory central index key of the issuer; 0 when none."
        },
        {
          "name": "sic",
          "bytes": 4,
          "signed": false,
          "meaning": "Standard industrial classification code; 0 when none."
        },
        {
          "name": "naics",
          "bytes": 4,
          "signed": false,
          "meaning": "North American industry classification code; 0 when none."
        },
        {
          "name": "listing_source",
          "bytes": 1,
          "signed": false,
          "meaning": "0 unknown, 1 main, 2 secondary."
        },
        {
          "name": "security_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 multi-currency. All other bits zero."
        },
        {
          "name": "reserved",
          "bytes": 2,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "issuer_name_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of issuer_name, 0\u2013255. Computed, not character count."
        },
        {
          "name": "description_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of description, 0\u2013255. Computed, not character count."
        },
        {
          "name": "security_type_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of security_type, 0\u20138. Computed, not character count."
        },
        {
          "name": "structure_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of structure, 0\u20138. Computed, not character count."
        },
        {
          "name": "listing_status_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of listing_status, 0\u20138. Computed, not character count."
        },
        {
          "name": "voting_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of voting, 0\u20138. Computed, not character count."
        },
        {
          "name": "primary_exchange_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of primary_exchange, 0\u201316. Computed, not character count."
        },
        {
          "name": "exchange_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of exchange, 0\u201316. Computed, not character count."
        },
        {
          "name": "operating_mic_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of operating_mic, 0 or 4. Computed, not character count."
        },
        {
          "name": "segment_mic_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of segment_mic, 0 or 4. Computed, not character count."
        },
        {
          "name": "segment_name_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of segment_name, 0\u2013128. Computed, not character count."
        },
        {
          "name": "symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of symbol, 0\u2013255. Computed, not character count."
        },
        {
          "name": "alt_symbol_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of alt_symbol, 0\u2013255. Computed, not character count."
        },
        {
          "name": "local_code_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of local_code, 0\u2013255. Computed, not character count."
        },
        {
          "name": "isin_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of isin, 0 or 12. Computed, not character count."
        },
        {
          "name": "cusip_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of cusip, 0 or 9. Computed, not character count."
        },
        {
          "name": "composite_figi_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of composite_figi, 0 or 12. Computed, not character count."
        },
        {
          "name": "composite_ticker_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of composite_ticker, 0\u201332. Computed, not character count."
        },
        {
          "name": "figi_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of figi, 0 or 12. Computed, not character count."
        },
        {
          "name": "figi_ticker_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of figi_ticker, 0\u201332. Computed, not character count."
        },
        {
          "name": "fisn_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of fisn, 0\u201335. Computed, not character count."
        },
        {
          "name": "lei_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of lei, 0 or 20. Computed, not character count."
        },
        {
          "name": "cfi_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of cfi, 0 or 6. Computed, not character count."
        },
        {
          "name": "cic_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of cic, 0\u20138. Computed, not character count."
        },
        {
          "name": "gics_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of gics, 0\u20138. Computed, not character count."
        },
        {
          "name": "incorporation_country_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of incorporation_country, 0 or 2. Computed, not character count."
        },
        {
          "name": "listing_country_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of listing_country, 0 or 2. Computed, not character count."
        },
        {
          "name": "register_country_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of register_country, 0 or 2. Computed, not character count."
        },
        {
          "name": "trading_currency_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of trading_currency, 0\u201316. Computed, not character count."
        },
        {
          "name": "par_value_currency_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of par_value_currency, 0\u201316. Computed, not character count."
        }
      ],
      "texts": [
        "issuer_name",
        "description",
        "security_type",
        "structure",
        "listing_status",
        "voting",
        "primary_exchange",
        "exchange",
        "operating_mic",
        "segment_mic",
        "segment_name",
        "symbol",
        "alt_symbol",
        "local_code",
        "isin",
        "cusip",
        "composite_figi",
        "composite_ticker",
        "figi",
        "figi_ticker",
        "fisn",
        "lei",
        "cfi",
        "cic",
        "gics",
        "incorporation_country",
        "listing_country",
        "register_country",
        "trading_currency",
        "par_value_currency"
      ],
      "has_levels": false,
      "enums": {
        "listing_source": [
          0,
          1,
          2
        ]
      },
      "masks": {
        "security_flags": 1
      },
      "text_limits": {
        "issuer_name": [
          0,
          255
        ],
        "description": [
          0,
          255
        ],
        "security_type": [
          0,
          8
        ],
        "structure": [
          0,
          8
        ],
        "listing_status": [
          0,
          8
        ],
        "voting": [
          0,
          8
        ],
        "primary_exchange": [
          0,
          16
        ],
        "exchange": [
          0,
          16
        ],
        "segment_name": [
          0,
          128
        ],
        "symbol": [
          0,
          255
        ],
        "alt_symbol": [
          0,
          255
        ],
        "local_code": [
          0,
          255
        ],
        "composite_ticker": [
          0,
          32
        ],
        "figi_ticker": [
          0,
          32
        ],
        "fisn": [
          0,
          35
        ],
        "cic": [
          0,
          8
        ],
        "gics": [
          0,
          8
        ],
        "trading_currency": [
          0,
          16
        ],
        "par_value_currency": [
          0,
          16
        ]
      },
      "text_exact": {
        "operating_mic": [
          0,
          4
        ],
        "segment_mic": [
          0,
          4
        ],
        "isin": [
          0,
          12
        ],
        "cusip": [
          0,
          9
        ],
        "composite_figi": [
          0,
          12
        ],
        "figi": [
          0,
          12
        ],
        "lei": [
          0,
          20
        ],
        "cfi": [
          0,
          6
        ],
        "incorporation_country": [
          0,
          2
        ],
        "listing_country": [
          0,
          2
        ],
        "register_country": [
          0,
          2
        ]
      }
    },
    {
      "type": 22,
      "name": "CORPORATE_ACTION",
      "version": 1,
      "fixed_bytes": 184,
      "fields": [
        {
          "name": "security_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier of the security; 0 when none."
        },
        {
          "name": "issuer_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier of the issuer; 0 when none."
        },
        {
          "name": "created_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "When the event record was created at the source, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "effective_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Effective date, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "ex_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Ex-date, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "record_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Record date, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "payment_ns",
          "bytes": 8,
          "signed": false,
          "kind": "time",
          "meaning": "Payment date, POSIX ns; UINT64_MAX if unavailable."
        },
        {
          "name": "record_date_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier of the record-date entry; 0 when none."
        },
        {
          "name": "outturn_security_id",
          "bytes": 8,
          "signed": false,
          "meaning": "Producer identifier of the resulting security; 0 when none."
        },
        {
          "name": "ratio_old",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "Old side of the ratio \u00d7 10^9 (for a 4-for-1 split: 1); INT64_MIN if unavailable."
        },
        {
          "name": "ratio_new",
          "bytes": 8,
          "signed": true,
          "kind": "price",
          "meaning": "New side of the ratio \u00d7 10^9 (for a 4-for-1 split: 4); INT64_MIN if unavailable."
        },
        {
          "name": "option_id",
          "bytes": 4,
          "signed": false,
          "meaning": "Option number within the event; UINT32_MAX if unavailable."
        },
        {
          "name": "serial_id",
          "bytes": 4,
          "signed": false,
          "meaning": "Serial number within the option; UINT32_MAX if unavailable."
        },
        {
          "name": "action_flags",
          "bytes": 1,
          "signed": false,
          "meaning": "Bit 0 default option. All other bits zero."
        },
        {
          "name": "reserved",
          "bytes": 3,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        },
        {
          "name": "event_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of event, 1\u20138. Computed, not character count."
        },
        {
          "name": "subtype_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of subtype, 0\u201316. Computed, not character count."
        },
        {
          "name": "action_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of action, 0\u20138. Computed, not character count."
        },
        {
          "name": "status_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of status, 0\u20138. Computed, not character count."
        },
        {
          "name": "participation_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of participation, 0\u20138. Computed, not character count."
        },
        {
          "name": "payment_type_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of payment_type, 0\u20138. Computed, not character count."
        },
        {
          "name": "fraction_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of fraction, 0\u20138. Computed, not character count."
        },
        {
          "name": "date_label_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of date_label, 0\u201332. Computed, not character count."
        },
        {
          "name": "related_event_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of related_event, 0\u20138. Computed, not character count."
        },
        {
          "name": "related_event_id_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of related_event_id, 0\u201332. Computed, not character count."
        },
        {
          "name": "event_id_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of event_id, 1\u201332. Computed, not character count."
        },
        {
          "name": "unique_id_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of unique_id, 1\u201348. Computed, not character count."
        },
        {
          "name": "rate_currency_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of rate_currency, 0\u201316. Computed, not character count."
        },
        {
          "name": "outturn_isin_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of outturn_isin, 0 or 12. Computed, not character count."
        },
        {
          "name": "details_bytes",
          "bytes": 2,
          "signed": false,
          "meaning": "UTF-8 byte length of details, 0\u201365535. Computed, not character count."
        },
        {
          "name": "reserved",
          "bytes": 6,
          "signed": false,
          "meaning": "All bytes MUST be zero. This includes the unusual 3- and 7-byte reserved blocks. Never use as application storage."
        }
      ],
      "texts": [
        "event",
        "subtype",
        "action",
        "status",
        "participation",
        "payment_type",
        "fraction",
        "date_label",
        "related_event",
        "related_event_id",
        "event_id",
        "unique_id",
        "rate_currency",
        "outturn_isin",
        "details"
      ],
      "has_levels": false,
      "masks": {
        "action_flags": 1
      },
      "text_limits": {
        "event": [
          1,
          8
        ],
        "subtype": [
          0,
          16
        ],
        "action": [
          0,
          8
        ],
        "status": [
          0,
          8
        ],
        "participation": [
          0,
          8
        ],
        "payment_type": [
          0,
          8
        ],
        "fraction": [
          0,
          8
        ],
        "date_label": [
          0,
          32
        ],
        "related_event": [
          0,
          8
        ],
        "related_event_id": [
          0,
          32
        ],
        "event_id": [
          1,
          32
        ],
        "unique_id": [
          1,
          48
        ],
        "rate_currency": [
          0,
          16
        ],
        "details": [
          0,
          65535
        ]
      },
      "text_exact": {
        "outturn_isin": [
          0,
          12
        ]
      }
    }
  ]
})NWTDATA";
inline constexpr const char* catalog_json = R"NWTDATA([
  {
    "label": "definition-1",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000000000",
      "ts_recv": "1700000000000000100",
      "sequence": "1",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "1",
      "reserved": "0",
      "symbol_bytes": "3",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "5"
    },
    "texts": {
      "symbol": "EXM",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "share"
    },
    "levels": []
  },
  {
    "label": "trade-new",
    "type": 1,
    "fields": {
      "record_bytes": "88",
      "record_type": "1",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000001000",
      "ts_recv": "1700000000000001100",
      "sequence": "2",
      "price": "123450000000",
      "quantity": "10000000000",
      "trade_id": "42",
      "original_sequence": "0",
      "action": "1",
      "aggressor": "1",
      "conditions": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "trade-correct",
    "type": 1,
    "fields": {
      "record_bytes": "88",
      "record_type": "1",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000002000",
      "ts_recv": "1700000000000002100",
      "sequence": "3",
      "price": "123460000000",
      "quantity": "12000000000",
      "trade_id": "42",
      "original_sequence": "2",
      "action": "3",
      "aggressor": "2",
      "conditions": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "trade-cancel",
    "type": 1,
    "fields": {
      "record_bytes": "88",
      "record_type": "1",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000003000",
      "ts_recv": "1700000000000003100",
      "sequence": "4",
      "price": "-9223372036854775808",
      "quantity": "18446744073709551615",
      "trade_id": "42",
      "original_sequence": "2",
      "action": "2",
      "aggressor": "0",
      "conditions": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "trade-negative-price",
    "type": 1,
    "fields": {
      "record_bytes": "88",
      "record_type": "1",
      "schema_version": "1",
      "flags": "3",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000004000",
      "ts_recv": "1700000000000004100",
      "sequence": "5",
      "price": "-1250000000",
      "quantity": "500000000",
      "trade_id": "43",
      "original_sequence": "0",
      "action": "1",
      "aggressor": "0",
      "conditions": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "quote-two-sided",
    "type": 2,
    "fields": {
      "record_bytes": "96",
      "record_type": "2",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000005000",
      "ts_recv": "1700000000000005100",
      "sequence": "6",
      "bid_price": "123000000000",
      "ask_price": "124000000000",
      "bid_quantity": "10000000000",
      "ask_quantity": "11000000000",
      "bid_order_count": "2",
      "ask_order_count": "3",
      "quote_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "quote-one-sided",
    "type": 2,
    "fields": {
      "record_bytes": "96",
      "record_type": "2",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000006000",
      "ts_recv": "1700000000000006100",
      "sequence": "7",
      "bid_price": "123000000000",
      "ask_price": "-9223372036854775808",
      "bid_quantity": "10000000000",
      "ask_quantity": "0",
      "bid_order_count": "4294967295",
      "ask_order_count": "0",
      "quote_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "quote-empty",
    "type": 2,
    "fields": {
      "record_bytes": "96",
      "record_type": "2",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000007000",
      "ts_recv": "1700000000000007100",
      "sequence": "8",
      "bid_price": "-9223372036854775808",
      "ask_price": "-9223372036854775808",
      "bid_quantity": "0",
      "ask_quantity": "0",
      "bid_order_count": "0",
      "ask_order_count": "0",
      "quote_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "quote-crossed",
    "type": 2,
    "fields": {
      "record_bytes": "96",
      "record_type": "2",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000008000",
      "ts_recv": "1700000000000008100",
      "sequence": "9",
      "bid_price": "125000000000",
      "ask_price": "124000000000",
      "bid_quantity": "10000000000",
      "ask_quantity": "11000000000",
      "bid_order_count": "2",
      "ask_order_count": "3",
      "quote_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "bar-complete",
    "type": 3,
    "fields": {
      "record_bytes": "112",
      "record_type": "3",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000000000",
      "ts_recv": "1700000000000009100",
      "sequence": "10",
      "interval_start_ns": "1699999940000000000",
      "interval_end_ns": "1700000000000000000",
      "open": "123000000000",
      "high": "125000000000",
      "low": "122000000000",
      "close": "124000000000",
      "volume": "42000000000",
      "trade_count": "4",
      "bar_flags": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "bar-empty",
    "type": 3,
    "fields": {
      "record_bytes": "112",
      "record_type": "3",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000060000000000",
      "ts_recv": "1700000000000010100",
      "sequence": "11",
      "interval_start_ns": "1700000000000000000",
      "interval_end_ns": "1700000060000000000",
      "open": "-9223372036854775808",
      "high": "-9223372036854775808",
      "low": "-9223372036854775808",
      "close": "-9223372036854775808",
      "volume": "0",
      "trade_count": "0",
      "bar_flags": "1"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-clear",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000011000",
      "ts_recv": "1700000000000011100",
      "sequence": "12",
      "order_id": "0",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "4",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-add",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000012000",
      "ts_recv": "1700000000000012100",
      "sequence": "13",
      "order_id": "101",
      "price": "123000000000",
      "quantity": "10000000000",
      "priority": "100",
      "action": "1",
      "side": "1",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-modify",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000013000",
      "ts_recv": "1700000000000013100",
      "sequence": "14",
      "order_id": "101",
      "price": "123500000000",
      "quantity": "8000000000",
      "priority": "101",
      "action": "2",
      "side": "1",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-delete",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000014000",
      "ts_recv": "1700000000000014100",
      "sequence": "15",
      "order_id": "101",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "3",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-snapshot-begin",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000015000",
      "ts_recv": "1700000000000015100",
      "sequence": "16",
      "order_id": "0",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "5",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-snapshot-bid",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000016000",
      "ts_recv": "1700000000000016100",
      "sequence": "17",
      "order_id": "201",
      "price": "123000000000",
      "quantity": "8000000000",
      "priority": "1",
      "action": "1",
      "side": "1",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-snapshot-ask",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000017000",
      "ts_recv": "1700000000000017100",
      "sequence": "18",
      "order_id": "202",
      "price": "124000000000",
      "quantity": "9000000000",
      "priority": "18446744073709551615",
      "action": "1",
      "side": "2",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-snapshot-end",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000018000",
      "ts_recv": "1700000000000018100",
      "sequence": "19",
      "order_id": "0",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "6",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "book-two-levels",
    "type": 5,
    "fields": {
      "record_bytes": "152",
      "record_type": "5",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000019000",
      "ts_recv": "1700000000000019100",
      "sequence": "20",
      "levels": "2",
      "book_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": [
      {
        "bid_price": "123000000000",
        "ask_price": "124000000000",
        "bid_quantity": "10000000000",
        "ask_quantity": "11000000000",
        "bid_count": "1",
        "ask_count": "1",
        "reserved": "0"
      },
      {
        "bid_price": "122000000000",
        "ask_price": "-9223372036854775808",
        "bid_quantity": "12000000000",
        "ask_quantity": "0",
        "bid_count": "2",
        "ask_count": "0",
        "reserved": "0"
      }
    ]
  },
  {
    "label": "book-empty",
    "type": 5,
    "fields": {
      "record_bytes": "56",
      "record_type": "5",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000020000",
      "ts_recv": "1700000000000020100",
      "sequence": "21",
      "levels": "0",
      "book_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "book-depth-limited",
    "type": 5,
    "fields": {
      "record_bytes": "104",
      "record_type": "5",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000021000",
      "ts_recv": "1700000000000021100",
      "sequence": "22",
      "levels": "1",
      "book_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": [
      {
        "bid_price": "123000000000",
        "ask_price": "124000000000",
        "bid_quantity": "1000000000",
        "ask_quantity": "1000000000",
        "bid_count": "1",
        "ask_count": "1",
        "reserved": "0"
      }
    ]
  },
  {
    "label": "status-0",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000022000",
      "ts_recv": "1700000000000022100",
      "sequence": "23",
      "status": "0",
      "reason": "0",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-1",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000023000",
      "ts_recv": "1700000000000023100",
      "sequence": "24",
      "status": "1",
      "reason": "1",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-2",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000024000",
      "ts_recv": "1700000000000024100",
      "sequence": "25",
      "status": "2",
      "reason": "2",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-3",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000025000",
      "ts_recv": "1700000000000025100",
      "sequence": "26",
      "status": "3",
      "reason": "3",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-4",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000026000",
      "ts_recv": "1700000000000026100",
      "sequence": "27",
      "status": "4",
      "reason": "4",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-5",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000027000",
      "ts_recv": "1700000000000027100",
      "sequence": "28",
      "status": "5",
      "reason": "0",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "gap-1",
    "type": 8,
    "fields": {
      "record_bytes": "80",
      "record_type": "8",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000028000",
      "ts_recv": "1700000000000028100",
      "sequence": "29",
      "first_missing_source_sequence": "100",
      "last_missing_source_sequence": "105",
      "reason": "1",
      "reserved": "0",
      "recovery_id": "1"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "gap-2",
    "type": 8,
    "fields": {
      "record_bytes": "80",
      "record_type": "8",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000029000",
      "ts_recv": "1700000000000029100",
      "sequence": "30",
      "first_missing_source_sequence": "18446744073709551615",
      "last_missing_source_sequence": "18446744073709551615",
      "reason": "2",
      "reserved": "0",
      "recovery_id": "2"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "gap-3",
    "type": 8,
    "fields": {
      "record_bytes": "80",
      "record_type": "8",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000030000",
      "ts_recv": "1700000000000030100",
      "sequence": "31",
      "first_missing_source_sequence": "18446744073709551615",
      "last_missing_source_sequence": "18446744073709551615",
      "reason": "3",
      "reserved": "0",
      "recovery_id": "3"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "gap-4",
    "type": 8,
    "fields": {
      "record_bytes": "80",
      "record_type": "8",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000031000",
      "ts_recv": "1700000000000031100",
      "sequence": "32",
      "first_missing_source_sequence": "18446744073709551615",
      "last_missing_source_sequence": "18446744073709551615",
      "reason": "4",
      "reserved": "0",
      "recovery_id": "4"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "quote-recovery",
    "type": 2,
    "fields": {
      "record_bytes": "96",
      "record_type": "2",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000032000",
      "ts_recv": "1700000000000032100",
      "sequence": "33",
      "bid_price": "123000000000",
      "ask_price": "124000000000",
      "bid_quantity": "10000000000",
      "ask_quantity": "11000000000",
      "bid_order_count": "2",
      "ask_order_count": "3",
      "quote_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "book-recovery",
    "type": 5,
    "fields": {
      "record_bytes": "104",
      "record_type": "5",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000033000",
      "ts_recv": "1700000000000033100",
      "sequence": "34",
      "levels": "1",
      "book_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": [
      {
        "bid_price": "123000000000",
        "ask_price": "124000000000",
        "bid_quantity": "1000000000",
        "ask_quantity": "1000000000",
        "bid_count": "1",
        "ask_count": "1",
        "reserved": "0"
      }
    ]
  },
  {
    "label": "mbo-recovery-begin",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000034000",
      "ts_recv": "1700000000000034100",
      "sequence": "35",
      "order_id": "0",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "5",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-recovery-add",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000035000",
      "ts_recv": "1700000000000035100",
      "sequence": "36",
      "order_id": "301",
      "price": "123000000000",
      "quantity": "1000000000",
      "priority": "1",
      "action": "1",
      "side": "1",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-recovery-end",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000036000",
      "ts_recv": "1700000000000036100",
      "sequence": "37",
      "order_id": "0",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "6",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-recovery",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "1001",
      "ts_event": "1700000000000037000",
      "ts_recv": "1700000000000037100",
      "sequence": "38",
      "status": "2",
      "reason": "4",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "system-1",
    "type": 9,
    "fields": {
      "record_bytes": "64",
      "record_type": "9",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000038000",
      "ts_recv": "1700000000000038100",
      "sequence": "39",
      "code": "1",
      "text_bytes": "0",
      "severity": "0",
      "reserved": "0",
      "related_recovery_id": "0"
    },
    "texts": {
      "text": ""
    },
    "levels": []
  },
  {
    "label": "system-2",
    "type": 9,
    "fields": {
      "record_bytes": "104",
      "record_type": "9",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000039000",
      "ts_recv": "1700000000000039100",
      "sequence": "40",
      "code": "2",
      "text_bytes": "36",
      "severity": "0",
      "reserved": "0",
      "related_recovery_id": "4"
    },
    "texts": {
      "text": "Recovery received — café / 東京"
    },
    "levels": []
  },
  {
    "label": "system-3",
    "type": 9,
    "fields": {
      "record_bytes": "104",
      "record_type": "9",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000040000",
      "ts_recv": "1700000000000040100",
      "sequence": "41",
      "code": "3",
      "text_bytes": "36",
      "severity": "1",
      "reserved": "0",
      "related_recovery_id": "4"
    },
    "texts": {
      "text": "Recovery received — café / 東京"
    },
    "levels": []
  },
  {
    "label": "system-4",
    "type": 9,
    "fields": {
      "record_bytes": "104",
      "record_type": "9",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1700000000000041000",
      "ts_recv": "1700000000000041100",
      "sequence": "42",
      "code": "4",
      "text_bytes": "36",
      "severity": "2",
      "reserved": "0",
      "related_recovery_id": "4"
    },
    "texts": {
      "text": "Recovery received — café / 東京"
    },
    "levels": []
  },
  {
    "label": "definition-0",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2000",
      "ts_event": "1700000000000042000",
      "ts_recv": "1700000000000042100",
      "sequence": "43",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "0",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-0",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  },
  {
    "label": "definition-2",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1700000000000043000",
      "ts_recv": "1700000000000043100",
      "sequence": "44",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "1700086400000000000",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "2",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-2",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  },
  {
    "label": "definition-3",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2003",
      "ts_event": "1700000000000044000",
      "ts_recv": "1700000000000044100",
      "sequence": "45",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "1700086400000000000",
      "underlying_instrument_id": "1001",
      "strike": "125000000000",
      "asset_class": "3",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-3",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  },
  {
    "label": "definition-4",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2004",
      "ts_event": "1700000000000045000",
      "ts_recv": "1700000000000045100",
      "sequence": "46",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "4",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-4",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  },
  {
    "label": "definition-5",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2005",
      "ts_event": "1700000000000046000",
      "ts_recv": "1700000000000046100",
      "sequence": "47",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "5",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-5",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  },
  {
    "label": "definition-6",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2006",
      "ts_event": "1700000000000047000",
      "ts_recv": "1700000000000047100",
      "sequence": "48",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "6",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-6",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  },
  {
    "label": "definition-7",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2007",
      "ts_event": "1700000000000048000",
      "ts_recv": "1700000000000048100",
      "sequence": "49",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "7",
      "reserved": "0",
      "symbol_bytes": "5",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "4"
    },
    "texts": {
      "symbol": "EXM-7",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "unit"
    },
    "levels": []
  }
])NWTDATA";
inline constexpr const char* manifest_json = R"NWTDATA({"dataset":"EXAMPLE.ALL","producer":"nwt-developer-kit/1.0-draft.2","profile":"market-data","clock":"posix-ns","publishers":[{"id":1,"name":"Example Feed","venue":"EXAMPLE"}],"schemas":[{"type":1,"version":1,"required":true,"name":"TRADE","spec_uri":"urn:nwt:spec:1.0"},{"type":2,"version":1,"required":true,"name":"QUOTE","spec_uri":"urn:nwt:spec:1.0"},{"type":3,"version":1,"required":true,"name":"BAR","spec_uri":"urn:nwt:spec:1.0"},{"type":4,"version":1,"required":true,"name":"MBO","spec_uri":"urn:nwt:spec:1.0"},{"type":5,"version":1,"required":true,"name":"BOOK_SNAPSHOT","spec_uri":"urn:nwt:spec:1.0"},{"type":6,"version":1,"required":true,"name":"INSTRUMENT_DEF","spec_uri":"urn:nwt:spec:1.0"},{"type":7,"version":1,"required":true,"name":"STATUS","spec_uri":"urn:nwt:spec:1.0"},{"type":8,"version":1,"required":true,"name":"GAP","spec_uri":"urn:nwt:spec:1.0"},{"type":9,"version":1,"required":true,"name":"SYSTEM","spec_uri":"urn:nwt:spec:1.0"}]})NWTDATA";
inline constexpr const char* catalog_v11_json = R"NWTDATA([
  {
    "label": "def-equity",
    "type": 6,
    "fields": {
      "record_bytes": "136",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000000000000000",
      "ts_recv": "1760000000000000100",
      "sequence": "1",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "1000000000",
      "expiration_ns": "18446744073709551615",
      "underlying_instrument_id": "0",
      "strike": "-9223372036854775808",
      "asset_class": "1",
      "reserved": "0",
      "symbol_bytes": "4",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "5"
    },
    "texts": {
      "symbol": "NWTX",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "share"
    },
    "levels": []
  },
  {
    "label": "def-option",
    "type": 6,
    "fields": {
      "record_bytes": "152",
      "record_type": "6",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000000000001000",
      "ts_recv": "1760000000000001100",
      "sequence": "2",
      "price_increment": "10000000",
      "quantity_increment": "1000000000",
      "contract_multiplier": "100000000000",
      "expiration_ns": "1766178000000000000",
      "underlying_instrument_id": "2001",
      "strike": "150000000000",
      "asset_class": "3",
      "reserved": "0",
      "symbol_bytes": "21",
      "venue_bytes": "7",
      "currency_bytes": "3",
      "quantity_unit_bytes": "8"
    },
    "texts": {
      "symbol": "NWTX  251219C00150000",
      "venue": "EXAMPLE",
      "currency": "USD",
      "quantity_unit": "contract"
    },
    "levels": []
  },
  {
    "label": "venue-operating",
    "type": 10,
    "fields": {
      "record_bytes": "192",
      "record_type": "10",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1760000000000002000",
      "ts_recv": "1760000000000002100",
      "sequence": "3",
      "created_ns": "1433116800000000000",
      "updated_ns": "1711324800000000000",
      "expiry_ns": "18446744073709551615",
      "kind": "1",
      "status": "1",
      "mic_bytes": "4",
      "operating_mic_bytes": "4",
      "country_bytes": "2",
      "category_bytes": "4",
      "acronym_bytes": "4",
      "city_bytes": "8",
      "name_bytes": "20",
      "legal_entity_bytes": "24",
      "lei_bytes": "20",
      "reserved": "0"
    },
    "texts": {
      "mic": "XNWT",
      "operating_mic": "XNWT",
      "country": "US",
      "category": "RMKT",
      "acronym": "NWTX",
      "city": "NEW YORK",
      "name": "NWT EXAMPLE EXCHANGE",
      "legal_entity": "NWT EXAMPLE EXCHANGE LLC",
      "lei": "EXAMPLE00LEI00000001"
    },
    "levels": []
  },
  {
    "label": "venue-segment-unicode",
    "type": 10,
    "fields": {
      "record_bytes": "392",
      "record_type": "10",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1760000000000003000",
      "ts_recv": "1760000000000003100",
      "sequence": "4",
      "created_ns": "1572825600000000000",
      "updated_ns": "1613347200000000000",
      "expiry_ns": "18446744073709551615",
      "kind": "2",
      "status": "2",
      "mic_bytes": "4",
      "operating_mic_bytes": "4",
      "country_bytes": "2",
      "category_bytes": "0",
      "acronym_bytes": "0",
      "city_bytes": "0",
      "name_bytes": "255",
      "legal_entity_bytes": "24",
      "lei_bytes": "0",
      "reserved": "0"
    },
    "texts": {
      "mic": "NWTS",
      "operating_mic": "XNWT",
      "country": "US",
      "category": "",
      "acronym": "",
      "city": "",
      "name": "éééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééX",
      "legal_entity": "Unicode Segment Operator",
      "lei": ""
    },
    "levels": []
  },
  {
    "label": "venue-expired",
    "type": 10,
    "fields": {
      "record_bytes": "144",
      "record_type": "10",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1760000000000004000",
      "ts_recv": "1760000000000004100",
      "sequence": "5",
      "created_ns": "18446744073709551615",
      "updated_ns": "1703980800000000000",
      "expiry_ns": "1703980800000000000",
      "kind": "1",
      "status": "3",
      "mic_bytes": "4",
      "operating_mic_bytes": "4",
      "country_bytes": "2",
      "category_bytes": "4",
      "acronym_bytes": "4",
      "city_bytes": "6",
      "name_bytes": "18",
      "legal_entity_bytes": "0",
      "lei_bytes": "0",
      "reserved": "0"
    },
    "texts": {
      "mic": "XOLD",
      "operating_mic": "XOLD",
      "country": "GB",
      "category": "MLTF",
      "acronym": "OLDX",
      "city": "LONDON",
      "name": "OLD EXAMPLE MARKET",
      "legal_entity": "",
      "lei": ""
    },
    "levels": []
  },
  {
    "label": "listing-normal",
    "type": 12,
    "fields": {
      "record_bytes": "120",
      "record_type": "12",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "18446744073709551615",
      "ts_recv": "1760000000000005100",
      "sequence": "6",
      "round_lot": "100",
      "listing_flags": "0",
      "market_tier": "1",
      "financial_flags": "1",
      "reserved": "0",
      "symbol_bytes": "4",
      "name_bytes": "32",
      "listing_mic_bytes": "4",
      "cqs_symbol_bytes": "4",
      "alt_symbol_bytes": "4"
    },
    "texts": {
      "symbol": "NWTX",
      "name": "NWT Example Corp. - Common Stock",
      "listing_mic": "XNWT",
      "cqs_symbol": "NWTX",
      "alt_symbol": "NWTX"
    },
    "levels": []
  },
  {
    "label": "listing-etf-deficient",
    "type": 12,
    "fields": {
      "record_bytes": "112",
      "record_type": "12",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2003",
      "ts_event": "18446744073709551615",
      "ts_recv": "1760000000000006100",
      "sequence": "7",
      "round_lot": "100",
      "listing_flags": "1",
      "market_tier": "2",
      "financial_flags": "3",
      "reserved": "0",
      "symbol_bytes": "4",
      "name_bytes": "21",
      "listing_mic_bytes": "4",
      "cqs_symbol_bytes": "0",
      "alt_symbol_bytes": "5"
    },
    "texts": {
      "symbol": "NWTE",
      "name": "NWT Example Index ETF",
      "listing_mic": "XNWT",
      "cqs_symbol": "",
      "alt_symbol": "NWT.E"
    },
    "levels": []
  },
  {
    "label": "listing-minimal",
    "type": 12,
    "fields": {
      "record_bytes": "80",
      "record_type": "12",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2005",
      "ts_event": "18446744073709551615",
      "ts_recv": "18446744073709551615",
      "sequence": "8",
      "round_lot": "4294967295",
      "listing_flags": "0",
      "market_tier": "0",
      "financial_flags": "0",
      "reserved": "0",
      "symbol_bytes": "3",
      "name_bytes": "0",
      "listing_mic_bytes": "0",
      "cqs_symbol_bytes": "0",
      "alt_symbol_bytes": "0"
    },
    "texts": {
      "symbol": "MIN",
      "name": "",
      "listing_mic": "",
      "cqs_symbol": "",
      "alt_symbol": ""
    },
    "levels": []
  },
  {
    "label": "listing-awkward-text",
    "type": 12,
    "fields": {
      "record_bytes": "128",
      "record_type": "12",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2006",
      "ts_event": "18446744073709551615",
      "ts_recv": "1760000000000008100",
      "sequence": "9",
      "round_lot": "10",
      "listing_flags": "2",
      "market_tier": "0",
      "financial_flags": "0",
      "reserved": "0",
      "symbol_bytes": "4",
      "name_bytes": "40",
      "listing_mic_bytes": "0",
      "cqs_symbol_bytes": "5",
      "alt_symbol_bytes": "0"
    },
    "texts": {
      "symbol": "AWKW",
      "name": "Awkward, \"Quoted\" \\ Name\nLine two\u0001 café",
      "listing_mic": "",
      "cqs_symbol": "AWK.W",
      "alt_symbol": ""
    },
    "levels": []
  },
  {
    "label": "option-def-call",
    "type": 11,
    "fields": {
      "record_bytes": "128",
      "record_type": "11",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000000000009000",
      "ts_recv": "1760000000000009100",
      "sequence": "10",
      "underlying_instrument_id": "2001",
      "expiration_ns": "1766178000000000000",
      "strike": "150000000000",
      "contract_multiplier": "100000000000",
      "right": "1",
      "exercise_style": "1",
      "settlement": "1",
      "closing_type": "1",
      "option_flags": "0",
      "reserved": "0",
      "root_bytes": "4",
      "underlying_symbol_bytes": "4",
      "osi_symbol_bytes": "21",
      "currency_bytes": "3"
    },
    "texts": {
      "root": "NWTX",
      "underlying_symbol": "NWTX",
      "osi_symbol": "NWTX  251219C00150000",
      "currency": "USD"
    },
    "levels": []
  },
  {
    "label": "option-def-unknowns",
    "type": 11,
    "fields": {
      "record_bytes": "104",
      "record_type": "11",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2004",
      "ts_event": "1760000000000010000",
      "ts_recv": "1760000000000010100",
      "sequence": "11",
      "underlying_instrument_id": "0",
      "expiration_ns": "1768597200000000000",
      "strike": "12500000000",
      "contract_multiplier": "-9223372036854775808",
      "right": "2",
      "exercise_style": "0",
      "settlement": "0",
      "closing_type": "0",
      "option_flags": "3",
      "reserved": "0",
      "root_bytes": "4",
      "underlying_symbol_bytes": "4",
      "osi_symbol_bytes": "0",
      "currency_bytes": "0"
    },
    "texts": {
      "root": "ZZZQ",
      "underlying_symbol": "ZZZQ",
      "osi_symbol": "",
      "currency": ""
    },
    "levels": []
  },
  {
    "label": "symbol-map-native",
    "type": 17,
    "fields": {
      "record_bytes": "80",
      "record_type": "17",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000000000011000",
      "ts_recv": "1760000000000011100",
      "sequence": "12",
      "valid_from_ns": "1577923200000000000",
      "valid_to_ns": "18446744073709551615",
      "symbology": "1",
      "reserved": "0",
      "symbol_bytes": "4"
    },
    "texts": {
      "symbol": "NWTX"
    },
    "levels": []
  },
  {
    "label": "symbol-map-closed-isin",
    "type": 17,
    "fields": {
      "record_bytes": "88",
      "record_type": "17",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000000000012000",
      "ts_recv": "1760000000000012100",
      "sequence": "13",
      "valid_from_ns": "1577923200000000000",
      "valid_to_ns": "1735689600000000000",
      "symbology": "3",
      "reserved": "0",
      "symbol_bytes": "12"
    },
    "texts": {
      "symbol": "US0000NWTX07"
    },
    "levels": []
  },
  {
    "label": "symbol-map-root",
    "type": 17,
    "fields": {
      "record_bytes": "80",
      "record_type": "17",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000000000013000",
      "ts_recv": "1760000000000013100",
      "sequence": "14",
      "valid_from_ns": "1758499200000000000",
      "valid_to_ns": "1766178000000000000",
      "symbology": "5",
      "reserved": "0",
      "symbol_bytes": "4"
    },
    "texts": {
      "symbol": "NWTX"
    },
    "levels": []
  },
  {
    "label": "trade-new",
    "type": 1,
    "fields": {
      "record_bytes": "88",
      "record_type": "1",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000001000000000",
      "ts_recv": "1760000001000000100",
      "sequence": "15",
      "price": "149250000000",
      "quantity": "100000000000",
      "trade_id": "1",
      "original_sequence": "0",
      "action": "1",
      "aggressor": "1",
      "conditions": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "quote-two-sided",
    "type": 2,
    "fields": {
      "record_bytes": "96",
      "record_type": "2",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000001000001000",
      "ts_recv": "1760000001000001100",
      "sequence": "16",
      "bid_price": "149240000000",
      "ask_price": "149260000000",
      "bid_quantity": "300000000000",
      "ask_quantity": "200000000000",
      "bid_order_count": "2",
      "ask_order_count": "1",
      "quote_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "bar-complete",
    "type": 3,
    "fields": {
      "record_bytes": "112",
      "record_type": "3",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000000000",
      "ts_recv": "1760000060000000100",
      "sequence": "17",
      "interval_start_ns": "1760000000000000000",
      "interval_end_ns": "1760000060000000000",
      "open": "149250000000",
      "high": "149250000000",
      "low": "149250000000",
      "close": "149250000000",
      "volume": "100000000000",
      "trade_count": "1",
      "bar_flags": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "status-open",
    "type": 7,
    "fields": {
      "record_bytes": "64",
      "record_type": "7",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000001000",
      "ts_recv": "1760000060000001100",
      "sequence": "18",
      "status": "2",
      "reason": "1",
      "status_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "book-snapshot",
    "type": 5,
    "fields": {
      "record_bytes": "152",
      "record_type": "5",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000002000",
      "ts_recv": "1760000060000002100",
      "sequence": "19",
      "levels": "2",
      "book_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": [
      {
        "bid_price": "149240000000",
        "ask_price": "149260000000",
        "bid_quantity": "300000000000",
        "ask_quantity": "200000000000",
        "bid_count": "2",
        "ask_count": "1",
        "reserved": "0"
      },
      {
        "bid_price": "149230000000",
        "ask_price": "149270000000",
        "bid_quantity": "500000000000",
        "ask_quantity": "400000000000",
        "bid_count": "3",
        "ask_count": "2",
        "reserved": "0"
      }
    ]
  },
  {
    "label": "delta-set-bid",
    "type": 15,
    "fields": {
      "record_bytes": "72",
      "record_type": "15",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000003000",
      "ts_recv": "1760000060000003100",
      "sequence": "20",
      "price": "149250000000",
      "quantity": "100000000000",
      "order_count": "1",
      "action": "1",
      "side": "1",
      "delta_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "delta-set-ask-last",
    "type": 15,
    "fields": {
      "record_bytes": "72",
      "record_type": "15",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000003000",
      "ts_recv": "1760000060000003100",
      "sequence": "21",
      "price": "149260000000",
      "quantity": "250000000000",
      "order_count": "4294967295",
      "action": "1",
      "side": "2",
      "delta_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "delta-delete",
    "type": 15,
    "fields": {
      "record_bytes": "72",
      "record_type": "15",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000004000",
      "ts_recv": "1760000060000004100",
      "sequence": "22",
      "price": "149230000000",
      "quantity": "0",
      "order_count": "4294967295",
      "action": "2",
      "side": "1",
      "delta_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "delta-clear-side",
    "type": 15,
    "fields": {
      "record_bytes": "72",
      "record_type": "15",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000005000",
      "ts_recv": "1760000060000005100",
      "sequence": "23",
      "price": "-9223372036854775808",
      "quantity": "0",
      "order_count": "4294967295",
      "action": "3",
      "side": "2",
      "delta_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "delta-clear-all",
    "type": 15,
    "fields": {
      "record_bytes": "72",
      "record_type": "15",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000006000",
      "ts_recv": "1760000060000006100",
      "sequence": "24",
      "price": "-9223372036854775808",
      "quantity": "0",
      "order_count": "4294967295",
      "action": "3",
      "side": "0",
      "delta_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-clear",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000007000",
      "ts_recv": "1760000060000007100",
      "sequence": "25",
      "order_id": "0",
      "price": "-9223372036854775808",
      "quantity": "0",
      "priority": "18446744073709551615",
      "action": "4",
      "side": "0",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "mbo-add",
    "type": 4,
    "fields": {
      "record_bytes": "88",
      "record_type": "4",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000008000",
      "ts_recv": "1760000060000008100",
      "sequence": "26",
      "order_id": "9001",
      "price": "149240000000",
      "quantity": "100000000000",
      "priority": "1",
      "action": "1",
      "side": "1",
      "mbo_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "stat-open",
    "type": 13,
    "fields": {
      "record_bytes": "80",
      "record_type": "13",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000009000",
      "ts_recv": "1760000060000009100",
      "sequence": "27",
      "ts_ref": "1759968000000000000",
      "price": "149100000000",
      "quantity": "18446744073709551615",
      "stat_type": "1",
      "action": "1",
      "stat_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "stat-settlement-preliminary",
    "type": 13,
    "fields": {
      "record_bytes": "80",
      "record_type": "13",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000010000",
      "ts_recv": "1760000060000010100",
      "sequence": "28",
      "ts_ref": "1759968000000000000",
      "price": "149300000000",
      "quantity": "18446744073709551615",
      "stat_type": "5",
      "action": "1",
      "stat_flags": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "stat-volume",
    "type": 13,
    "fields": {
      "record_bytes": "80",
      "record_type": "13",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000011000",
      "ts_recv": "1760000060000011100",
      "sequence": "29",
      "ts_ref": "1759968000000000000",
      "price": "-9223372036854775808",
      "quantity": "1234500000000000",
      "stat_type": "7",
      "action": "1",
      "stat_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "stat-open-interest",
    "type": 13,
    "fields": {
      "record_bytes": "80",
      "record_type": "13",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000060000012000",
      "ts_recv": "1760000060000012100",
      "sequence": "30",
      "ts_ref": "1759968000000000000",
      "price": "-9223372036854775808",
      "quantity": "4321000000000",
      "stat_type": "8",
      "action": "1",
      "stat_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "stat-delete",
    "type": 13,
    "fields": {
      "record_bytes": "80",
      "record_type": "13",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000013000",
      "ts_recv": "1760000060000013100",
      "sequence": "31",
      "ts_ref": "1759968000000000000",
      "price": "-9223372036854775808",
      "quantity": "18446744073709551615",
      "stat_type": "5",
      "action": "2",
      "stat_flags": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "analytics-full",
    "type": 14,
    "fields": {
      "record_bytes": "120",
      "record_type": "14",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000060000014000",
      "ts_recv": "1760000060000014100",
      "sequence": "32",
      "implied_volatility": "253400000",
      "delta": "551200000",
      "gamma": "31200000",
      "theta": "-45600000",
      "vega": "198700000",
      "rho": "84300000",
      "underlying_price": "149250000000",
      "theoretical_price": "5430000000",
      "price_basis": "1",
      "model": "1",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "analytics-iv-only",
    "type": 14,
    "fields": {
      "record_bytes": "120",
      "record_type": "14",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000060000015000",
      "ts_recv": "1760000060000015100",
      "sequence": "33",
      "implied_volatility": "260000000",
      "delta": "-9223372036854775808",
      "gamma": "-9223372036854775808",
      "theta": "-9223372036854775808",
      "vega": "-9223372036854775808",
      "rho": "-9223372036854775808",
      "underlying_price": "-9223372036854775808",
      "theoretical_price": "-9223372036854775808",
      "price_basis": "0",
      "model": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "analytics-put-negative",
    "type": 14,
    "fields": {
      "record_bytes": "120",
      "record_type": "14",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2002",
      "ts_event": "1760000060000016000",
      "ts_recv": "1760000060000016100",
      "sequence": "34",
      "implied_volatility": "247100000",
      "delta": "-448800000",
      "gamma": "29800000",
      "theta": "-31200000",
      "vega": "187500000",
      "rho": "-62100000",
      "underlying_price": "149250000000",
      "theoretical_price": "4870000000",
      "price_basis": "5",
      "model": "3",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "imbalance-buy",
    "type": 16,
    "fields": {
      "record_bytes": "104",
      "record_type": "16",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000017000",
      "ts_recv": "1760000060000017100",
      "sequence": "35",
      "auction_ns": "1760040000000000000",
      "reference_price": "149250000000",
      "near_price": "149300000000",
      "far_price": "149350000000",
      "paired_quantity": "50000000000000",
      "imbalance_quantity": "12000000000000",
      "imbalance_side": "1",
      "auction_type": "2",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "imbalance-none",
    "type": 16,
    "fields": {
      "record_bytes": "104",
      "record_type": "16",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000018000",
      "ts_recv": "1760000060000018100",
      "sequence": "36",
      "auction_ns": "18446744073709551615",
      "reference_price": "149250000000",
      "near_price": "-9223372036854775808",
      "far_price": "-9223372036854775808",
      "paired_quantity": "18446744073709551615",
      "imbalance_quantity": "0",
      "imbalance_side": "0",
      "auction_type": "0",
      "reserved": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "trade-quote",
    "type": 18,
    "fields": {
      "record_bytes": "120",
      "record_type": "18",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000019000",
      "ts_recv": "1760000060000019100",
      "sequence": "37",
      "price": "149260000000",
      "quantity": "50000000000",
      "trade_id": "2",
      "bid_price": "149240000000",
      "ask_price": "149260000000",
      "bid_quantity": "300000000000",
      "ask_quantity": "200000000000",
      "bid_order_count": "2",
      "ask_order_count": "1",
      "aggressor": "1",
      "reserved": "0",
      "conditions": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "trade-quote-one-sided",
    "type": 18,
    "fields": {
      "record_bytes": "120",
      "record_type": "18",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000020000",
      "ts_recv": "1760000060000020100",
      "sequence": "38",
      "price": "149200000000",
      "quantity": "25000000000",
      "trade_id": "0",
      "bid_price": "-9223372036854775808",
      "ask_price": "149260000000",
      "bid_quantity": "0",
      "ask_quantity": "200000000000",
      "bid_order_count": "0",
      "ask_order_count": "4294967295",
      "aggressor": "2",
      "reserved": "0",
      "conditions": "1"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "best-quote-event",
    "type": 19,
    "fields": {
      "record_bytes": "112",
      "record_type": "19",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000060000021000",
      "ts_recv": "1760000060000021100",
      "sequence": "39",
      "bid_price": "149240000000",
      "ask_price": "149260000000",
      "bid_quantity": "300000000000",
      "ask_quantity": "200000000000",
      "bid_order_count": "2",
      "ask_order_count": "1",
      "quote_flags": "0",
      "bid_publisher_id": "1",
      "ask_publisher_id": "2",
      "reserved": "0",
      "interval_ns": "0"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "best-quote-sampled",
    "type": 19,
    "fields": {
      "record_bytes": "112",
      "record_type": "19",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "2001",
      "ts_event": "1760000061000000000",
      "ts_recv": "1760000061000000100",
      "sequence": "40",
      "bid_price": "149230000000",
      "ask_price": "-9223372036854775808",
      "bid_quantity": "500000000000",
      "ask_quantity": "0",
      "bid_order_count": "3",
      "ask_order_count": "0",
      "quote_flags": "1",
      "bid_publisher_id": "2",
      "ask_publisher_id": "0",
      "reserved": "0",
      "interval_ns": "1000000000"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "gap",
    "type": 8,
    "fields": {
      "record_bytes": "80",
      "record_type": "8",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1760000061000001000",
      "ts_recv": "1760000061000001100",
      "sequence": "41",
      "first_missing_source_sequence": "500",
      "last_missing_source_sequence": "509",
      "reason": "1",
      "reserved": "0",
      "recovery_id": "1"
    },
    "texts": {},
    "levels": []
  },
  {
    "label": "system-heartbeat",
    "type": 9,
    "fields": {
      "record_bytes": "64",
      "record_type": "9",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "0",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "1760000061000002000",
      "ts_recv": "1760000061000002100",
      "sequence": "1",
      "code": "1",
      "text_bytes": "0",
      "severity": "0",
      "reserved": "0",
      "related_recovery_id": "0"
    },
    "texts": {
      "text": ""
    },
    "levels": []
  },
  {
    "label": "security-def-full",
    "type": 21,
    "fields": {
      "record_bytes": "440",
      "record_type": "21",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "3001",
      "ts_event": "1760054400000000000",
      "ts_recv": "1760000061000003100",
      "sequence": "42",
      "listing_group_id": "500123",
      "security_id": "400456",
      "issuer_id": "300789",
      "listing_created_ns": "1572825600000000000",
      "listing_ns": "1572912000000000000",
      "delisting_ns": "18446744073709551615",
      "shares_outstanding": "15204137000",
      "shares_outstanding_ns": "1759190400000000000",
      "lot_size": "100000000000",
      "par_value": "10000",
      "votes_per_share": "1000000000",
      "cik": "1999999",
      "sic": "7372",
      "naics": "511210",
      "listing_source": "1",
      "security_flags": "1",
      "reserved": "0",
      "issuer_name_bytes": "16",
      "description_bytes": "15",
      "security_type_bytes": "3",
      "structure_bytes": "3",
      "listing_status_bytes": "1",
      "voting_bytes": "1",
      "primary_exchange_bytes": "5",
      "exchange_bytes": "5",
      "operating_mic_bytes": "4",
      "segment_mic_bytes": "4",
      "segment_name_bytes": "24",
      "symbol_bytes": "4",
      "alt_symbol_bytes": "5",
      "local_code_bytes": "4",
      "isin_bytes": "12",
      "cusip_bytes": "9",
      "composite_figi_bytes": "12",
      "composite_ticker_bytes": "7",
      "figi_bytes": "12",
      "figi_ticker_bytes": "7",
      "fisn_bytes": "14",
      "lei_bytes": "20",
      "cfi_bytes": "6",
      "cic_bytes": "4",
      "gics_bytes": "8",
      "incorporation_country_bytes": "2",
      "listing_country_bytes": "2",
      "register_country_bytes": "2",
      "trading_currency_bytes": "3",
      "par_value_currency_bytes": "3"
    },
    "texts": {
      "issuer_name": "NWT Example Corp",
      "description": "Ordinary Shares",
      "security_type": "EQS",
      "structure": "ORD",
      "listing_status": "L",
      "voting": "V",
      "primary_exchange": "USNWT",
      "exchange": "USNWT",
      "operating_mic": "XNWT",
      "segment_mic": "NWTS",
      "segment_name": "NWT EXAMPLE MAIN SEGMENT",
      "symbol": "NWTX",
      "alt_symbol": "NWT.X",
      "local_code": "NWTX",
      "isin": "US0000NWTX07",
      "cusip": "0000NWTX0",
      "composite_figi": "NWTG00000001",
      "composite_ticker": "NWTX US",
      "figi": "NWTG00000002",
      "figi_ticker": "NWTX UQ",
      "fisn": "NWT EXAMPLE/SH",
      "lei": "EXAMPLE00LEI00000001",
      "cfi": "ESVUFR",
      "cic": "US31",
      "gics": "45103010",
      "incorporation_country": "US",
      "listing_country": "US",
      "register_country": "US",
      "trading_currency": "USD",
      "par_value_currency": "USD"
    },
    "levels": []
  },
  {
    "label": "security-def-minimal",
    "type": 21,
    "fields": {
      "record_bytes": "216",
      "record_type": "21",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "3002",
      "ts_event": "1760054400000000000",
      "ts_recv": "1760000061000004100",
      "sequence": "43",
      "listing_group_id": "0",
      "security_id": "0",
      "issuer_id": "0",
      "listing_created_ns": "18446744073709551615",
      "listing_ns": "18446744073709551615",
      "delisting_ns": "18446744073709551615",
      "shares_outstanding": "18446744073709551615",
      "shares_outstanding_ns": "18446744073709551615",
      "lot_size": "18446744073709551615",
      "par_value": "-9223372036854775808",
      "votes_per_share": "-9223372036854775808",
      "cik": "0",
      "sic": "0",
      "naics": "0",
      "listing_source": "0",
      "security_flags": "0",
      "reserved": "0",
      "issuer_name_bytes": "0",
      "description_bytes": "0",
      "security_type_bytes": "0",
      "structure_bytes": "0",
      "listing_status_bytes": "0",
      "voting_bytes": "0",
      "primary_exchange_bytes": "0",
      "exchange_bytes": "0",
      "operating_mic_bytes": "0",
      "segment_mic_bytes": "0",
      "segment_name_bytes": "0",
      "symbol_bytes": "0",
      "alt_symbol_bytes": "0",
      "local_code_bytes": "0",
      "isin_bytes": "0",
      "cusip_bytes": "0",
      "composite_figi_bytes": "0",
      "composite_ticker_bytes": "0",
      "figi_bytes": "0",
      "figi_ticker_bytes": "0",
      "fisn_bytes": "0",
      "lei_bytes": "0",
      "cfi_bytes": "0",
      "cic_bytes": "0",
      "gics_bytes": "0",
      "incorporation_country_bytes": "0",
      "listing_country_bytes": "0",
      "register_country_bytes": "0",
      "trading_currency_bytes": "0",
      "par_value_currency_bytes": "0"
    },
    "texts": {
      "issuer_name": "",
      "description": "",
      "security_type": "",
      "structure": "",
      "listing_status": "",
      "voting": "",
      "primary_exchange": "",
      "exchange": "",
      "operating_mic": "",
      "segment_mic": "",
      "segment_name": "",
      "symbol": "",
      "alt_symbol": "",
      "local_code": "",
      "isin": "",
      "cusip": "",
      "composite_figi": "",
      "composite_ticker": "",
      "figi": "",
      "figi_ticker": "",
      "fisn": "",
      "lei": "",
      "cfi": "",
      "cic": "",
      "gics": "",
      "incorporation_country": "",
      "listing_country": "",
      "register_country": "",
      "trading_currency": "",
      "par_value_currency": ""
    },
    "levels": []
  },
  {
    "label": "corporate-action-dividend",
    "type": 22,
    "fields": {
      "record_bytes": "288",
      "record_type": "22",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "3001",
      "ts_event": "1763078400000000000",
      "ts_recv": "1760000061000005100",
      "sequence": "44",
      "security_id": "400456",
      "issuer_id": "300789",
      "created_ns": "1760966415000000000",
      "effective_ns": "18446744073709551615",
      "ex_ns": "1763078400000000000",
      "record_ns": "1763078400000000000",
      "payment_ns": "1764288000000000000",
      "record_date_id": "7001234",
      "outturn_security_id": "0",
      "ratio_old": "-9223372036854775808",
      "ratio_new": "-9223372036854775808",
      "option_id": "1",
      "serial_id": "1",
      "action_flags": "1",
      "reserved": "0",
      "event_bytes": "3",
      "subtype_bytes": "4",
      "action_bytes": "1",
      "status_bytes": "1",
      "participation_bytes": "1",
      "payment_type_bytes": "1",
      "fraction_bytes": "0",
      "date_label_bytes": "7",
      "related_event_bytes": "0",
      "related_event_id_bytes": "0",
      "event_id_bytes": "7",
      "unique_id_bytes": "15",
      "rate_currency_bytes": "3",
      "outturn_isin_bytes": "0",
      "details_bytes": "56"
    },
    "texts": {
      "event": "DIV",
      "subtype": "CASH",
      "action": "I",
      "status": "A",
      "participation": "M",
      "payment_type": "C",
      "fraction": "",
      "date_label": "ex_date",
      "related_event": "",
      "related_event_id": "",
      "event_id": "9001234",
      "unique_id": "DIV-9001234-1-1",
      "rate_currency": "USD",
      "outturn_isin": "",
      "details": "{\"gross_rate\":\"0.24\",\"net_rate\":\"0.204\",\"tax_rate\":\"15\"}"
    },
    "levels": []
  },
  {
    "label": "corporate-action-split",
    "type": 22,
    "fields": {
      "record_bytes": "256",
      "record_type": "22",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "3001",
      "ts_event": "1764547200000000000",
      "ts_recv": "1760000061000006100",
      "sequence": "45",
      "security_id": "400456",
      "issuer_id": "300789",
      "created_ns": "1762128000000000000",
      "effective_ns": "1764547200000000000",
      "ex_ns": "1764547200000000000",
      "record_ns": "1764288000000000000",
      "payment_ns": "18446744073709551615",
      "record_date_id": "7001301",
      "outturn_security_id": "400457",
      "ratio_old": "1000000000",
      "ratio_new": "4000000000",
      "option_id": "1",
      "serial_id": "1",
      "action_flags": "1",
      "reserved": "0",
      "event_bytes": "5",
      "subtype_bytes": "0",
      "action_bytes": "1",
      "status_bytes": "1",
      "participation_bytes": "1",
      "payment_type_bytes": "1",
      "fraction_bytes": "1",
      "date_label_bytes": "14",
      "related_event_bytes": "3",
      "related_event_id_bytes": "7",
      "event_id_bytes": "7",
      "unique_id_bytes": "17",
      "rate_currency_bytes": "0",
      "outturn_isin_bytes": "12",
      "details_bytes": "0"
    },
    "texts": {
      "event": "SPLIT",
      "subtype": "",
      "action": "I",
      "status": "A",
      "participation": "M",
      "payment_type": "S",
      "fraction": "D",
      "date_label": "effective_date",
      "related_event": "DIV",
      "related_event_id": "9001234",
      "event_id": "9001301",
      "unique_id": "SPLIT-9001301-1-1",
      "rate_currency": "",
      "outturn_isin": "US0000NWTX15",
      "details": ""
    },
    "levels": []
  },
  {
    "label": "corporate-action-minimal",
    "type": 22,
    "fields": {
      "record_bytes": "208",
      "record_type": "22",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "1",
      "channel_id": "0",
      "instrument_id": "3002",
      "ts_event": "1764633600000000000",
      "ts_recv": "1760000061000007100",
      "sequence": "46",
      "security_id": "0",
      "issuer_id": "0",
      "created_ns": "18446744073709551615",
      "effective_ns": "18446744073709551615",
      "ex_ns": "18446744073709551615",
      "record_ns": "18446744073709551615",
      "payment_ns": "18446744073709551615",
      "record_date_id": "0",
      "outturn_security_id": "0",
      "ratio_old": "-9223372036854775808",
      "ratio_new": "-9223372036854775808",
      "option_id": "4294967295",
      "serial_id": "4294967295",
      "action_flags": "0",
      "reserved": "0",
      "event_bytes": "3",
      "subtype_bytes": "0",
      "action_bytes": "0",
      "status_bytes": "0",
      "participation_bytes": "0",
      "payment_type_bytes": "0",
      "fraction_bytes": "0",
      "date_label_bytes": "0",
      "related_event_bytes": "0",
      "related_event_id_bytes": "0",
      "event_id_bytes": "7",
      "unique_id_bytes": "11",
      "rate_currency_bytes": "0",
      "outturn_isin_bytes": "0",
      "details_bytes": "0"
    },
    "texts": {
      "event": "ANN",
      "subtype": "",
      "action": "",
      "status": "",
      "participation": "",
      "payment_type": "",
      "fraction": "",
      "date_label": "",
      "related_event": "",
      "related_event_id": "",
      "event_id": "9001400",
      "unique_id": "ANN-9001400",
      "rate_currency": "",
      "outturn_isin": "",
      "details": ""
    },
    "levels": []
  },
  {
    "label": "frame-summary",
    "type": 20,
    "standalone": true,
    "fields": {
      "record_bytes": "104",
      "record_type": "20",
      "schema_version": "1",
      "flags": "0",
      "publisher_id": "0",
      "channel_id": "0",
      "instrument_id": "0",
      "ts_event": "18446744073709551615",
      "ts_recv": "18446744073709551615",
      "sequence": "2",
      "data_frame_seq": "0",
      "data_frame_offset": "2280",
      "stored_bytes": "480",
      "codec": "0",
      "summary_flags": "2",
      "reserved": "0",
      "type_mask": "1088",
      "min_instrument_id": "2001",
      "max_instrument_id": "2002"
    },
    "texts": {},
    "levels": []
  }
])NWTDATA";
inline constexpr const char* manifest_v11_json = R"NWTDATA({"dataset":"EXAMPLE.V11","producer":"nwt-developer-kit/1.1-draft.1","profile":"market-data","clock":"posix-ns","publishers":[{"id":1,"name":"Example Feed","venue":"EXAMPLE"},{"id":2,"name":"Second Venue","venue":"EXAMPLE2"}],"schemas":[{"type":1,"version":1,"required":true,"name":"TRADE","spec_uri":"urn:nwt:spec:1.0"},{"type":2,"version":1,"required":true,"name":"QUOTE","spec_uri":"urn:nwt:spec:1.0"},{"type":3,"version":1,"required":true,"name":"BAR","spec_uri":"urn:nwt:spec:1.0"},{"type":4,"version":1,"required":true,"name":"MBO","spec_uri":"urn:nwt:spec:1.0"},{"type":5,"version":1,"required":true,"name":"BOOK_SNAPSHOT","spec_uri":"urn:nwt:spec:1.0"},{"type":6,"version":1,"required":true,"name":"INSTRUMENT_DEF","spec_uri":"urn:nwt:spec:1.0"},{"type":7,"version":1,"required":true,"name":"STATUS","spec_uri":"urn:nwt:spec:1.0"},{"type":8,"version":1,"required":true,"name":"GAP","spec_uri":"urn:nwt:spec:1.0"},{"type":9,"version":1,"required":true,"name":"SYSTEM","spec_uri":"urn:nwt:spec:1.0"},{"type":10,"version":1,"required":false,"name":"VENUE_DEF","spec_uri":"urn:nwt:spec:1.1"},{"type":11,"version":1,"required":false,"name":"OPTION_DEF","spec_uri":"urn:nwt:spec:1.1"},{"type":12,"version":1,"required":false,"name":"LISTING","spec_uri":"urn:nwt:spec:1.1"},{"type":13,"version":1,"required":false,"name":"STATISTICS","spec_uri":"urn:nwt:spec:1.1"},{"type":14,"version":1,"required":false,"name":"OPTION_ANALYTICS","spec_uri":"urn:nwt:spec:1.1"},{"type":15,"version":1,"required":true,"name":"BOOK_DELTA","spec_uri":"urn:nwt:spec:1.1"},{"type":16,"version":1,"required":false,"name":"IMBALANCE","spec_uri":"urn:nwt:spec:1.1"},{"type":17,"version":1,"required":false,"name":"SYMBOL_MAP","spec_uri":"urn:nwt:spec:1.1"},{"type":18,"version":1,"required":false,"name":"TRADE_QUOTE","spec_uri":"urn:nwt:spec:1.1"},{"type":19,"version":1,"required":false,"name":"BEST_QUOTE","spec_uri":"urn:nwt:spec:1.1"},{"type":20,"version":1,"required":false,"name":"FRAME_SUMMARY","spec_uri":"urn:nwt:spec:1.1"},{"type":21,"version":1,"required":false,"name":"SECURITY_DEF","spec_uri":"urn:nwt:spec:1.1"},{"type":22,"version":1,"required":false,"name":"CORPORATE_ACTION","spec_uri":"urn:nwt:spec:1.1"}]})NWTDATA";
