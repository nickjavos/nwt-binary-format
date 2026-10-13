# Provenance

Every container has a `PROVENANCE` element: a JSON object that records what was converted and by which rules. The converter prints the same object when it finishes. With `--emit-deltas`, the printed object also holds the provenance of the second file under `deltas`.

| Key | Content |
|---|---|
| `source_schema` | The kind of export: `definition`, `mbo`, `mbp-1`, `mbp-10`, `cmbp-1`, `ohlcv-1m` or `statistics` |
| `source_sha256`, `source_rows` | The SHA-256 and the number of the source rows read |
| `definitions_sha256` | The SHA-256 of the `--definitions` file, when one is given |
| `trades_sha256` | The SHA-256 of the `--trades` file, for `csv-ohlcv` |
| `output` | `main`, or `deltas` for the file written by `--emit-deltas` |
| `policy_options` | The options that decide what is written, as given on the command line |
| `conversion_policy` | The rules applied, as text |
| `records_written` | The number of records, by record type |
| `rows_skipped` | The number of rows left out, by reason |
| `notes` | The number of rows converted by a stated rule, by rule |
| `values_rounded` | Always 0 |

The object also holds `source_format`, `converter` and `license_reference`.
