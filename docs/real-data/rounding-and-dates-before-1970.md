# Rounding and dates before 1970

NWT prices and ratios hold nine decimal places, and an NWT timestamp cannot hold a date before 1970. The `csv-secmaster` and `csv-corporate-actions` kinds store a value outside these limits as follows.

- A decimal with more than nine decimal places is rounded half to even at nine places. `0.30000000000000004` becomes 300000000.
- A date before 1970 is stored as null.
- The provenance counts the rounded values in `rounded_decimals` and the dates in `dates_before_1970`. A value is counted once for every source row that holds it.
- In a corporate-actions file, the source text is kept in the `details` of the row under `source_decimals` and `source_dates`, by source column name. This also holds when the value belongs to the listing columns and the `SECURITY_DEF` of the row is not written again.
- A `SECURITY_DEF` has no free text, so in a security-master file the provenance lists each such value under `not_exact`, with its line, column and source text.

The `corporate-actions-us.nwt` sample contains one value of each kind:

```json
{"source_decimals":{"par_value":"0.139682539682"}}
```

```json
{"source_dates":{"listing_date":"1929-02-14"}}
```
