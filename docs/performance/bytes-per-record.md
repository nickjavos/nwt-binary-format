# Bytes per record

The chart divides the size of each file by the number of records in it. An NWT record has binary fields of fixed width. A nanosecond timestamp takes 8 bytes, and the same value takes 19 digits as decimal text. JSON Lines also repeats every field name in every record. The records of `corporate-actions-us` carry long text fields, which NWT stores as UTF-8 without change, so the relative difference between CSV and NWT is the smallest there.

<!-- nwt-chart: bytes-per-record -->

| Sample | CSV | JSON Lines | NWT, raw frames |
|---|---|---|---|
| `equity-quotes` | 127 | 428 | 102 |
| `equity-orders` | 121 | 375 | 89.3 |
| `equity-bars` | 177 | 465 | 114 |
| `option-best-quotes` | 171 | 567 | 124 |
| `statistics` | 161 | 517 | 120 |
| `corporate-actions-us` | 578 | 1,800 | 487 |
