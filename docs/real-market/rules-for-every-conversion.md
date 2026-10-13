# Rules for every conversion

**Record header**

Every record takes its header fields from the source row.

| Source column | NWT field | Rule |
|---|---|---|
| `publisher_id` | `publisher_id` | Kept. 0 stops the conversion. |
| `instrument_id` | `instrument_id` | Kept. 0 stops the conversion. |
| `channel_id` | `channel_id` | Kept. 0 when the file has no such column. |
| `ts_event` | `ts_event` | UTC timestamp with up to nine fractional digits, stored as POSIX nanoseconds. |
| `ts_recv` | `ts_recv` | As `ts_event`. Null when the file has no such column. |

- `sequence` restarts at 1 for each pair of publisher and channel in each output file. The source sequence number is not carried.
- Every publisher ID that appears is declared in the manifest under the name `publisher-<id>` with an empty venue.

**Exact values**

- Prices, sizes and timestamps are parsed with integer arithmetic (`tools/nwt_parse.py`). No value passes through floating point.
- Nothing is rounded. A price or a size with more than nine decimal places stops the conversion, and the provenance states `values_rounded` as 0.
- The converter accepts a timestamp only in UTC, written with `Z` or `+00:00`. Any other offset stops the conversion.
- Text is copied exactly. A text longer or shorter than its field allows stops the conversion.
- An unknown code, a missing column, a repeated column name or a row with the wrong number of columns stops the conversion.

**Nulls**

- An empty price becomes the null price.
- An empty timestamp becomes the null timestamp.
- A book side with no price is an absent side: null price, quantity 0 and order count 0.

**Instrument definitions**

- A definition always precedes the first record of its instrument. It is written once for each pair of publisher and instrument, on the publisher and channel of that first record.
- With `--definitions`, the definition comes from the definitions export, by the mapping in [Instrument definitions](instrument-definitions-instrument_def-and-option_def.md). When the export has several rows for one instrument, the last row is used.
- Without `--definitions`, the converter writes a minimal `INSTRUMENT_DEF`: the `symbol` of the row, `asset_class` 0, null increments, expiration and strike, null `ts_event` and `ts_recv`, and the currency, quantity unit and venue given as options.

**Rows and columns**

- Records keep the order of the source rows.
- A source column that is not in a mapping table of this page is not carried. This includes the source `flags`, the source sequence number and the capture-delay column `ts_in_delta`.
- A row that has no NWT form is skipped and counted in the provenance under `rows_skipped`, by reason. A row that is converted by a stated rule, such as a fill row, is counted under `notes`.

**Output**

- On any failure the converter prints a message that starts with `NWT error:`, exits with status 1 and writes no output file. A failure in a row names the source file and line: `NWT error: <file> line N: …`.
- The output is deterministic. The container `created_ns` is the constant 2026-10-13T00:00:00Z. The stream ID is the first 16 bytes of the SHA-256 of the kind, the output role (`main` or `deltas`) and the SHA-256 of the source rows read. The same rows and the same options give the same container bytes.
- Every container has a `PROVENANCE` element, described under [Provenance](provenance.md).
