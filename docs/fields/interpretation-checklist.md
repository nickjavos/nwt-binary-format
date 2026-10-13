# Interpretation checklist

A correct decoder or encoder agrees with every point below.

## Sizes and lengths

- `record_bytes` counts the 48-byte header. `stored_bytes` and `raw_bytes` do not count the frame header.
- `stored_bytes` leaves out the frame padding. `metadata_bytes` includes the padding of every metadata element.
- A text length counts UTF-8 bytes, not characters. A limit of 255 bytes accepts 127 two-byte characters plus one ASCII byte and rejects one byte more.
- Every `reserved` field is zero. A record type can have more than one: `LISTING`, `SYMBOL_MAP`, `TRADE_QUOTE`, `FRAME_SUMMARY` and `CORPORATE_ACTION` do.
- Records are transferred inside a `.nwt` container. A conformance vector stored as a bare record in a `.bin` file has no manifest and no CRC.

## Nulls and numbers

- The meaning of `UINT64_MAX` depends on the field. It is the null of a time, a quantity or a priority, and it is a legal value of an order identifier or a trade identifier.
- The size and the order count of an absent quote side are zero, not null. A null ask price requires a zero ask size and a zero ask count.
- `shares_outstanding` of `SECURITY_DEF` is a whole number of shares, not a value scaled by 10⁹. `round_lot`, `order_count`, `option_id` and `serial_id` are plain counts too.
- `interval_ns` of `BEST_QUOTE` is a duration, not a timestamp.
- Every `STATISTICS` record has both `price` and `quantity`. Which of the two is null depends on `stat_type` and `action`.
- A null `ts_event` is valid where the record type allows it, for example in `LISTING`. A frame whose records all have a null `ts_event` has null bounds.
- `min_event_ns` is the smallest non-null event time of the frame. It is not necessarily the time of the first record.

## State and order

- Instrument definitions apply in byte order. Sorting the records by `ts_event` changes their interpretation.
- The quantity of an `MBO` `MODIFY` is the absolute remaining size. A `TRADE` does not reduce the order book.
- The state of `BEST_QUOTE` and `TRADE_QUOTE` is separate from the state of `QUOTE`. They do not replace it.
- Sequence checks, CRC checks and gap recovery continue when `REPLAY` or `SUSPECT` is set. The flags replace none of these.
- `details` of `CORPORATE_ACTION` passes through the codec as text. That it is one JSON object with sorted keys is a rule for producers and for the state rules, not for the codec.
