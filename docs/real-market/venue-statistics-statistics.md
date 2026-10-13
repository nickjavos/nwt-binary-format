# Venue statistics: STATISTICS

The kind `csv-statistics` reads a statistics export. Every row that has a value becomes one `STATISTICS` record.

| Source `stat_type` | Source meaning | NWT `stat_type` |
|---:|---|---|
| 1 | Opening price | 1 (open) |
| 5 | Trading session high price | 2 (high) |
| 4 | Trading session low price | 3 (low) |
| 11 | Close price | 4 (close) |
| 3 | Settlement price | 5 (settlement) |
| 6 | Cleared volume | 7 (volume) |
| 9 | Open interest | 8 (open interest) |

Any other `stat_type` stops the conversion. The other columns map as follows:

| Source column | NWT field | Rule |
|---|---|---|
| `price` | `price` | The value of a price type (NWT types 1–5). The quantity is null. |
| `quantity` | `quantity` | The value of a quantity type (NWT types 7 and 8). The price is null. The export writes "no quantity" as 9223372036854775807, which becomes null. |
| `update_action` | `action` | 1 is SET, 2 is DELETE. A DELETE has a null price and a null quantity. |
| `ts_ref` | `ts_ref` | UTC timestamp. Empty becomes null. |
| `stat_flags` | `stat_flags` | See the rules below. |

- A row with `update_action` 1 and no value is skipped and counted.
- A row that carries a value in the column of the other kind stops the conversion.
- On a settlement price, source `stat_flags` 1 marks a final settlement. NWT marks the opposite case: bit 0 of `stat_flags` means preliminary. A settlement price with source flag 1 is written with `stat_flags` 0, and a settlement price with source flag 0 is written with `stat_flags` 1.
- Any other source flag value, or a flag on another type, stops the conversion.

A statistic from the `statistics.nwt` sample:

<!-- nwt-file: fixtures/real-market/statistics.jsonl lines=2-2 -->
