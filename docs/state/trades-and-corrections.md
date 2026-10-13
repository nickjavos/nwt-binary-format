# Trades and corrections

A trade is identified by `trade_id` within its publisher, channel and instrument. Its lifecycle is `NEW`, then any number of `CORRECT`, then at most one `CANCEL`.

| Action | Fields | Effect |
|---|---|---|
| `NEW` | Non-null price, quantity above 0, `original_sequence` 0 | Starts the trade under a `trade_id` that is not in use. |
| `CORRECT` | Full replacement price, quantity, aggressor and conditions | Replaces the values of the trade. |
| `CANCEL` | Null price, null quantity, aggressor 0, conditions 0 | Ends the trade. A later `CORRECT` or `CANCEL` for it is an error. |

`CORRECT` and `CANCEL` carry the `trade_id` of the trade and, in `original_sequence`, the `sequence` of its `NEW` record. They never point at an earlier correction.

The first trade of the container that the reference codecs write with `write` goes through the whole lifecycle; the second has a negative price:

| `sequence` | Action | `trade_id` | `original_sequence` | Price and quantity |
|---|---|---|---|---|
| 2 | `NEW` | 42 | 0 | 123.45 and 10 |
| 3 | `CORRECT` | 42 | 2 | 123.46 and 12 |
| 4 | `CANCEL` | 42 | 2 | Null and null |
| 5 | `NEW` | 43 | 0 | −1.25 and 0.5 |

After sequence 4 the consumer holds trade 42 as canceled, with its history, and after sequence 5 trade 43 as active.

All records of a lifecycle are in the same container and the same channel. An export that contains a correction also contains the `NEW` record and the corrections before it, even when they lie outside the requested time range. The Specification defines these rules in [TRADE](../records/TRADE.md).
