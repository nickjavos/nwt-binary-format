# Rules for every conversion

**Exact values**

- Decimals, dates and timestamps are parsed with integer arithmetic (`tools/nwt_parse.py`). No value passes through floating point. `6e-06` with nine decimal places is 6000, and `7370.0` as a whole number is 7370.
- Text is copied exactly: no trimming, no case change. A text longer or shorter than its field allows stops the conversion.
- A code that is not in the code table of its column stops the conversion.
- The four public kinds never round: a value that does not fit its field stops the conversion. The `csv-secmaster` and `csv-corporate-actions` kinds round a decimal with more than nine decimal places and keep its source text, as described under [Rounding and dates before 1970](rounding-and-dates-before-1970.md).
- A missing column, a repeated column name or a row with the wrong number of fields stops the conversion.

**Identifiers**

- The security-master and corporate-actions exports carry numeric identifiers behind a prefix. The number after `L-` becomes `instrument_id`; the numbers after `LG-`, `S-`, `I-` and `D-` fill their own fields. An identifier without its prefix stops the conversion.
- The symbol directories carry no numeric identifiers. Their `instrument_id` is derived from the symbol, as described in [Instrument identifiers](instrument-identifiers.md).
- `VENUE_DEF` records describe venues, not instruments: `instrument_id` is 0.

**Timestamps**

- Every time field is POSIX nanoseconds, UTC. A source date becomes midnight UTC of that date.
- The converter accepts a source timestamp only in UTC, written with `Z` or `+00:00`, with up to nine fractional digits. Any other offset stops the conversion.
- `ts_recv` is the record timestamp of the source row where the source has one (`ts_record`). Otherwise it is null.
- In the `csv-secmaster` and `csv-corporate-actions` kinds, a date before 1970 is stored as null and its source text is kept, as described under [Rounding and dates before 1970](rounding-and-dates-before-1970.md). In the other kinds a date before 1970 stops the conversion.

**Columns with no NWT field**

- In a corporate-actions export, every filled column with no NWT field is kept in the `details` text of the record, as described under [The details text](corporate-actions-security_def-and-corporate_action.md#the-details-text).
- In the other kinds, a column with no NWT field is skipped and listed in the provenance under `columns_not_carried`. Each kind names the columns it skips. Any other unknown column stops the conversion.

**Nulls**

- An empty number becomes the null value of its field.
- An empty identifier, `cik`, `sic` or `naics` becomes 0.
- An empty text becomes an empty text.

**Order and sequence**

- Records keep the order of the source rows.
- The manifest declares one publisher with ID 1. Every record is on publisher 1, channel 0, and `sequence` starts at 1.

**Output**

- On any failure the converter prints a message that starts with `NWT error:`, exits with status 1 and writes no output file. A failure in a row names the source line: `NWT error: line N: …`.
- The output is deterministic. The container `created_ns` is the constant 2026-10-13T00:00:00Z, and the stream ID is the first 16 bytes of the SHA-256 of the source file. The same source bytes and the same options give the same container bytes.
- Every container has a `PROVENANCE` element: a JSON object with `source_kind`, `source_format`, `source_rows`, `source_sha256`, the record counts under `records`, the rules applied as text under `conversion_policy` and `clock_policy`, and `license_reference`. Public kinds add `source_url`, and `retrieved` when the option is given. A kind that skips source columns lists them under `columns_not_carried`.
