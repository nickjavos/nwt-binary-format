# Reference data and statistics

Reference records describe venues, instruments, symbols and corporate events. The reference record types are `VENUE_DEF`, `OPTION_DEF`, `LISTING`, `SYMBOL_MAP`, `SECURITY_DEF` and `CORPORATE_ACTION`.

- A reference record needs no `INSTRUMENT_DEF` before it, and it does not replace one.
- A later record with the same key replaces the earlier one. The keys are in the table of [State a consumer keeps](state-a-consumer-keeps.md).
- `OPTION_DEF` and `INSTRUMENT_DEF` for the same instrument agree: the asset class of the definition is option, and expiration, strike and underlying instrument are equal. The check runs whichever record comes first.
- `SYMBOL_MAP` gives a half-open interval, from `valid_from_ns` up to but not including `valid_to_ns`, in which a symbol names an instrument. Two intervals of the same publisher, symbology and symbol do not overlap. Root symbols, symbology 5, are exempt: one root names many instruments at a time.
- The `details` text of a `CORPORATE_ACTION`, when it is not empty, is one JSON object with sorted keys and no duplicate key.
- A `GAP` does not invalidate reference data.

A statistic is a reference value of a session, not a trade. `ts_ref` names the session or the date it belongs to.

- `SET` gives the value. Price statistics (open, high, low, close, settlement, VWAP) carry a price and a null quantity. Quantity statistics (volume, open interest) carry a quantity and a null price.
- `DELETE` withdraws the value. Its price and its quantity are null.
- A consumer that keeps the latest `SET` per key and removes the key on `DELETE` holds the current statistics.
