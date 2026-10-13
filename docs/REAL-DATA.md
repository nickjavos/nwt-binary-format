# Reference data samples

The reference data samples are eight NWT files built from public exchange and registry files and from security-master and corporate-actions exports in CSV. They hold six record types: `VENUE_DEF`, `OPTION_DEF`, `LISTING`, `SYMBOL_MAP`, `SECURITY_DEF` and `CORPORATE_ACTION`. Use them to test a reader against real values, to see how each source column becomes an NWT field, and as a model for converting your own reference data with `tools/nwt_convert_reference.py`. Trades, quotes, books and bars are covered in [Market data samples](REAL-DATA-MARKET.md).

## Samples

Each sample is an `.nwt` file. Where a `.jsonl` file is listed, it is the JSON Lines view of the same sample: one JSON object per record, in file order.

| File | Record types | Contents |
|---|---|---|
| [venues.nwt](files/samples/venues.nwt)<br>[venues.jsonl](files/samples/venues.jsonl) | `VENUE_DEF` | 100 venues from the ISO 10383 market identifier code list: operating venues and market segments, active and expired |
| [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt)<br>[listings-nasdaq.jsonl](files/samples/listings-nasdaq.jsonl) | `LISTING`, `SYMBOL_MAP` | 100 securities from the Nasdaq-listed symbol directory, each as one `LISTING` followed by one `SYMBOL_MAP` |
| [listings-other.nwt](files/samples/listings-other.nwt)<br>[listings-other.jsonl](files/samples/listings-other.jsonl) | `LISTING`, `SYMBOL_MAP` | 100 securities from the symbol directory of the other US exchanges, each as one `LISTING` followed by one `SYMBOL_MAP` |
| [options.nwt](files/samples/options.nwt)<br>[options.jsonl](files/samples/options.jsonl) | `OPTION_DEF` | 100 option series from the option series directory |
| [secmaster-us.nwt](files/samples/secmaster-us.nwt)<br>[secmaster-us.jsonl](files/samples/secmaster-us.jsonl) | `SECURITY_DEF` | 28 US listings from a security-master export |
| [secmaster-global.nwt](files/samples/secmaster-global.nwt)<br>[secmaster-global.jsonl](files/samples/secmaster-global.jsonl) | `SECURITY_DEF` | 195 listings in 25 countries from a security-master export |
| [corporate-actions-us.nwt](files/samples/corporate-actions-us.nwt)<br>[corporate-actions-us.jsonl](files/samples/corporate-actions-us.jsonl) | `SECURITY_DEF`, `CORPORATE_ACTION` | 864 corporate-action events from a US export and the 777 `SECURITY_DEF` records that describe their listings |
| [corporate-actions-global.nwt](files/samples/corporate-actions-global.nwt)<br>[corporate-actions-global.jsonl](files/samples/corporate-actions-global.jsonl) | `SECURITY_DEF`, `CORPORATE_ACTION` | 500 corporate-action events from a global export and the 442 `SECURITY_DEF` records that describe their listings |

The first two records of `venues.jsonl` are shown below. Every integer is written as a decimal string, so 64-bit values survive any JSON parser. `18446744073709551615` is the null timestamp.

<!-- nwt-file: fixtures/real/venues.jsonl lines=1-2 -->

## Convert a file

The converter, `tools/nwt_convert_reference.py`, is a Python script that uses only the standard library. This procedure builds the `venues.nwt` sample from the saved rows of the ISO 10383 list.

1. Open a terminal in the kit root.
2. Run the converter with a kind, a source file and an output file:

   ```bash
   python3 tools/nwt_convert_reference.py mic fixtures/real/source/ISO10383_MIC.csv venues.nwt --retrieved 2026-10-13
   ```

   The converter writes `venues.nwt` and prints the provenance it stored in the file, as JSON. The record counts are under `records`:

   ```text
     "records": {
       "VENUE_DEF": 100
     },
     "retrieved": "2026-10-13",
   ```
3. Check the file with the `nwt` command:

   ```bash
   python3 tools/nwt.py inspect venues.nwt
   ```

   The last lines of the output confirm a complete file with 100 records:

   ```text
   end data_frames=1 records=100 status=normal
   records VENUE_DEF 100
   ```
4. Print the records as JSON Lines. Add `--pretty` for decimal prices and ISO 8601 timestamps.

   ```bash
   python3 examples/python/nwt_example.py to-json venues.nwt
   ```

The same converter runs through two other entry points, which take the same arguments:

```bash
python3 tools/nwt_convert.py mic fixtures/real/source/ISO10383_MIC.csv venues.nwt --retrieved 2026-10-13
```

```bash
python3 tools/nwt.py convert mic fixtures/real/source/ISO10383_MIC.csv venues.nwt --retrieved 2026-10-13
```

The other commands of `tools/nwt.py` are described in [The nwt command](TOOLS.md).

## Converter kinds

The first argument selects the source format.

| Kind | Source | Records written |
|---|---|---|
| `mic` | ISO 10383 market identifier code list, CSV | One `VENUE_DEF` per row |
| `nasdaqlisted` | Nasdaq-listed symbol directory, pipe-separated text | One `LISTING` and one `SYMBOL_MAP` per row |
| `otherlisted` | Symbol directory of the other US exchanges, pipe-separated text | One `LISTING` and one `SYMBOL_MAP` per row |
| `options` | Option series directory, pipe-separated text | One `OPTION_DEF` per row |
| `csv-secmaster` | Security-master export, CSV | One `SECURITY_DEF` per row |
| `csv-corporate-actions` | Corporate-actions export, CSV | One `CORPORATE_ACTION` per row, preceded by a `SECURITY_DEF` when the listing is new or its facts changed |

Two options follow the output file:

| Option | Meaning |
|---|---|
| `--dataset NAME` | The dataset name in the manifest. The defaults are `REAL.ISO10383.MIC`, `REAL.SYMDIR.NASDAQLISTED`, `REAL.SYMDIR.OTHERLISTED`, `REAL.SYMDIR.OPTIONS`, `REAL.SECMASTER` and `REAL.CORPACT`. |
| `--retrieved YYYY-MM-DD` | The date on which the source file was retrieved. It is stored in the provenance. |

The four public sources are published at these addresses:

| Kind | Published file |
|---|---|
| `mic` | `https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv` |
| `nasdaqlisted` | `https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt` |
| `otherlisted` | `https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt` |
| `options` | `https://www.nasdaqtrader.com/dynamic/SymDir/options.txt` |

To convert a whole public file, download it and pass it as the source file. A row with the wrong number of fields stops the conversion, so cut a partial download at the end of a line.

## Rules for every conversion

**Exact values**

- Decimals, dates and timestamps are parsed with integer arithmetic (`tools/nwt_parse.py`). No value passes through floating point. `6e-06` with nine decimal places is 6000, and `7370.0` as a whole number is 7370.
- Text is copied exactly: no trimming, no case change. A text longer or shorter than its field allows stops the conversion.
- A code that is not in the code table of its column stops the conversion.
- The four public kinds never round: a value that does not fit its field stops the conversion. The `csv-secmaster` and `csv-corporate-actions` kinds round a decimal with more than nine decimal places and keep its source text, as described under [Rounding and dates before 1970](#rounding-and-dates-before-1970).
- A missing column, a repeated column name or a row with the wrong number of fields stops the conversion.

**Identifiers**

- The security-master and corporate-actions exports carry numeric identifiers behind a prefix. The number after `L-` becomes `instrument_id`; the numbers after `LG-`, `S-`, `I-` and `D-` fill their own fields. An identifier without its prefix stops the conversion.
- The symbol directories carry no numeric identifiers. Their `instrument_id` is derived from the symbol, as described in [Instrument identifiers](#instrument-identifiers).
- `VENUE_DEF` records describe venues, not instruments: `instrument_id` is 0.

**Timestamps**

- Every time field is POSIX nanoseconds, UTC. A source date becomes midnight UTC of that date.
- The converter accepts a source timestamp only in UTC, written with `Z` or `+00:00`, with up to nine fractional digits. Any other offset stops the conversion.
- `ts_recv` is the record timestamp of the source row where the source has one (`ts_record`). Otherwise it is null.
- In the `csv-secmaster` and `csv-corporate-actions` kinds, a date before 1970 is stored as null and its source text is kept, as described under [Rounding and dates before 1970](#rounding-and-dates-before-1970). In the other kinds a date before 1970 stops the conversion.

**Columns with no NWT field**

- In a corporate-actions export, every filled column with no NWT field is kept in the `details` text of the record, as described under [The details text](#the-details-text).
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

## Instrument identifiers

The symbol directories and the option series directory identify an instrument by symbol only. The converter derives a stable 63-bit `instrument_id` from a namespace and a key with `instrument_id_for`:

<!-- nwt-file: tools/nwt_ids.py -->

| Kind | Namespace | Key |
|---|---|---|
| `nasdaqlisted` | `XNAS` | The value of `Symbol` |
| `otherlisted` | The `listing_mic` of the row | The value of `ACT Symbol` |
| `options` | `XNDQ` | Root symbol, expiration as `YYYY-MM-DD`, `C` or `P`, and the strike with nine decimals, joined by vertical bars |

The identifier of `AAAP` in the namespace `XNAS` is 2746828257060480391. An option series key looks like this, and its identifier in the namespace `XNDQ` is 6409513827953069741:

```text
A|2028-01-21|P|100.000000000
```

- The identifier is the first 63 bits of the SHA-256 of the namespace, a NUL byte and the key, so it also fits a signed 64-bit integer.
- The identifier of a symbol does not change when other rows are added to or removed from the source file.
- A key that appears twice in one file stops the conversion.
- Two different keys that give the same identifier stop the conversion, and the error names both keys.

## Symbol directories: LISTING and SYMBOL_MAP

The kinds `nasdaqlisted` and `otherlisted` read the two listed-securities files. Each row becomes one `LISTING` and then one `SYMBOL_MAP` for the same instrument.

A header row that differs from the published column list stops the conversion. The last row of a complete file holds the file creation time in the form `File Creation Time: mmddyyyyhh:mm`. The converter reads it as US Eastern time and converts it to UTC. A file that has data rows and no creation-time row stops the conversion.

| Source column | NWT field | Rule |
|---|---|---|
| `Symbol`, `ACT Symbol` | `symbol` | `Symbol` in `nasdaqlisted`, `ACT Symbol` in `otherlisted`. The same text is the `symbol` of the `SYMBOL_MAP` and the key of `instrument_id`. |
| `Security Name` | `name` | Copied exactly. |
| `Round Lot Size` | `round_lot` | Whole number. Empty becomes null. |
| `ETF` | `listing_flags` bit 0 | `Y` sets the bit, `N` clears it. Any other value stops the conversion. |
| `Test Issue` | `listing_flags` bit 1 | `Y` sets the bit, `N` clears it. |
| `NextShares` | `listing_flags` bit 2 | `nasdaqlisted` only. `Y` sets the bit, `N` clears it. The bit is 0 in `otherlisted`. |
| `Market Category` | `market_tier` | `nasdaqlisted` only, by the code table below. The field is 0 in `otherlisted`. |
| `Financial Status` | `financial_flags` | `nasdaqlisted` only, by the code table below. The field is 0 in `otherlisted`: the file reports no financial status. |
| `Exchange` | `listing_mic` | `otherlisted` only, by the code table below. The field is `XNAS` in `nasdaqlisted`. |
| `CQS Symbol` | `cqs_symbol` | `otherlisted` only. Empty in `nasdaqlisted`. |
| `NASDAQ Symbol` | `alt_symbol` | `otherlisted` only. Empty in `nasdaqlisted`. |
| `File Creation Time` | `ts_event`, `valid_from_ns` | The `ts_event` of both records and the `valid_from_ns` of the `SYMBOL_MAP`. |

The converter sets the remaining fields: `ts_recv` is null, and the `SYMBOL_MAP` has `symbology` 1 (native) and a null `valid_to_ns`, which means an open-ended mapping.

A `LISTING` and its `SYMBOL_MAP` from the Nasdaq-listed sample:

<!-- nwt-file: fixtures/real/listings-nasdaq.jsonl lines=1-2 -->

### Code letters

The letters and their meanings are those of the publisher's page "Symbol Look-Up/Directory Data Fields & Definitions", `https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs`. A letter that is not in a table stops the conversion.

`Market Category` sets `market_tier`:

| Letter | Meaning | `market_tier` |
|---|---|---:|
| `Q` | Nasdaq Global Select Market | 1 |
| `G` | Nasdaq Global Market | 2 |
| `S` | Nasdaq Capital Market | 3 |

`Financial Status` sets `financial_flags`. Bit 0 means that a status is reported, bit 1 deficient, bit 2 delinquent, bit 3 bankrupt:

| Letter | Meaning | `financial_flags` |
|---|---|---:|
| `N` | Normal: not deficient, delinquent or bankrupt | 1 |
| `D` | Deficient | 3 |
| `E` | Delinquent | 5 |
| `Q` | Bankrupt | 9 |
| `H` | Deficient and delinquent | 7 |
| `G` | Deficient and bankrupt | 11 |
| `J` | Delinquent and bankrupt | 13 |
| `K` | Deficient, delinquent and bankrupt | 15 |

`Exchange` sets `listing_mic`, which is also the namespace of `instrument_id`:

| Letter | Meaning | `listing_mic` |
|---|---|---|
| `A` | NYSE MKT | `XASE` |
| `N` | New York Stock Exchange | `XNYS` |
| `P` | NYSE Arca | `ARCX` |
| `Z` | BATS Global Markets | `BATS` |
| `V` | Investors' Exchange | `IEXG` |

## Option series: OPTION_DEF

The kind `options` reads the option series directory. Each row becomes one `OPTION_DEF`.

| Source column | NWT field | Rule |
|---|---|---|
| `Root Symbol` | `root` | Copied exactly. Also the first part of the `instrument_id` key. |
| `Underlying Symbol` | `underlying_symbol` | Copied exactly. |
| `Expiration Date` | `expiration_ns` | `mm/dd/yyyy`, stored as midnight UTC of that date. |
| `Explicit Strike Price` | `strike` | Exact decimal with up to nine decimal places. An empty strike, or one with more than nine decimal places, stops the conversion. |
| `Options Type` | `right` | `C` is 1 (call), `P` is 2 (put). |
| `Options Closing Type` | `closing_type` | `N` is 1 (normal hours), `L` is 2 (late hours). |
| `Pending` | `option_flags` bit 0 | `Y` sets the bit, `N` clears it. |
| `File Creation Time` | `ts_event` | Read as for the symbol directories. Null when the file has no creation-time row. |

The file has no column for the other `OPTION_DEF` fields, and the converter never infers them:

- `underlying_instrument_id` is 0, because the file names the underlying by symbol only.
- `exercise_style` and `settlement` are 0 (unknown).
- `contract_multiplier` is null.
- `option_flags` bit 1 (adjusted) is 0.
- `osi_symbol` and `currency` are empty.

`Underlying Issue Name` has no `OPTION_DEF` field. The converter skips it and lists it in the provenance under `columns_not_carried`.

The `options.nwt` sample is built from the first rows of the directory, which do not include the creation-time row, so its `ts_event` is null.

## Market identifier codes: VENUE_DEF

The kind `mic` reads the ISO 10383 list. Each row becomes one `VENUE_DEF`.

| Source column | NWT field | Rule |
|---|---|---|
| `MIC` | `mic` | Copied exactly. |
| `OPERATING MIC` | `operating_mic` | Copied exactly. In an `OPRT` row it equals `MIC`; any other value stops the conversion. |
| `OPRT/SGMT` | `kind` | `OPRT` is 1 (operating venue), `SGMT` is 2 (market segment). |
| `STATUS` | `status` | `ACTIVE` is 1, `UPDATED` is 2, `EXPIRED` is 3. |
| `CREATION DATE` | `created_ns` | `YYYYMMDD`, stored as midnight UTC. Empty becomes null. |
| `LAST UPDATE DATE` | `updated_ns` | `YYYYMMDD`, stored as midnight UTC. Empty becomes null. |
| `EXPIRY DATE` | `expiry_ns` | `YYYYMMDD`, stored as midnight UTC. Empty becomes null: the venue has no expiry. |
| `ISO COUNTRY CODE (ISO 3166)` | `country` | Copied exactly. |
| `MARKET CATEGORY CODE` | `category` | Copied exactly. |
| `ACRONYM` | `acronym` | Copied exactly. |
| `CITY` | `city` | Copied exactly. |
| `MARKET NAME-INSTITUTION DESCRIPTION` | `name` | Copied exactly. |
| `LEGAL ENTITY NAME` | `legal_entity` | Copied exactly. |
| `LEI` | `lei` | Copied exactly. |

- `instrument_id` is 0, and `ts_event` and `ts_recv` are null. The dates of the source are in `created_ns`, `updated_ns` and `expiry_ns`.
- `WEBSITE`, `LAST VALIDATION DATE` and `COMMENTS` have no `VENUE_DEF` field. The converter skips them and lists them in the provenance under `columns_not_carried`.
- Any other column stops the conversion.

## Security master: SECURITY_DEF

The kind `csv-secmaster` reads a security-master export. Each row becomes one `SECURITY_DEF`. The same mapping builds the `SECURITY_DEF` of a corporate-actions row from the listing columns that the row has.

| Source column | NWT field | Rule |
|---|---|---|
| `listing_id` | `instrument_id` | The number after `L-`. Empty or zero stops the conversion. |
| `ts_effective` | `ts_event` | UTC timestamp. In a corporate-actions row, `ts_event` is `event_date` instead. |
| `ts_record` | `ts_recv` | UTC timestamp. |
| `listing_group_id` | `listing_group_id` | The number after `LG-`. |
| `security_id` | `security_id` | The number after `S-`. |
| `issuer_id` | `issuer_id` | The number after `I-`. |
| `listing_created_date` | `listing_created_ns` | Date, midnight UTC. |
| `listing_date` | `listing_ns` | Date, midnight UTC. |
| `delisting_date` | `delisting_ns` | Date, midnight UTC. |
| `shares_outstanding` | `shares_outstanding` | Whole count, not scaled: `855630000.0` is 855630000. |
| `shares_outstanding_date` | `shares_outstanding_ns` | Date, midnight UTC. |
| `lot_size` | `lot_size` | Decimal scaled by 10⁹. |
| `par_value` | `par_value` | Decimal scaled by 10⁹. |
| `vote_per_sec` | `votes_per_share` | Decimal scaled by 10⁹. |
| `cik`, `sic`, `naics` | `cik`, `sic`, `naics` | Whole numbers: `7370.0` is 7370, and `7370.5` stops the conversion. Empty becomes 0. |
| `listing_source` | `listing_source` | `M` is 1 (main), `S` is 2 (secondary), empty is 0. |
| `multi_currency` | `security_flags` bit 0 | `True` sets the bit. `False` or empty clears it. |
| `issuer_name` | `issuer_name` | Copied exactly. |
| `security_description` | `description` | Copied exactly. |
| `security_type`, `structure`, `listing_status`, `voting` | The fields of the same names | The source codes, as text. |
| `primary_exchange`, `exchange`, `operating_mic`, `segment_mic` | The fields of the same names | Copied exactly. |
| `segment_mic_name` | `segment_name` | Copied exactly. |
| `symbol` | `symbol` | Copied exactly. |
| `nasdaq_symbol` | `alt_symbol` | Copied exactly. |
| `us_code` | `cusip` | Copied exactly. |
| `bbg_comp_id` | `composite_figi` | Copied exactly. |
| `bbg_comp_ticker` | `composite_ticker` | Copied exactly. |
| `local_code`, `isin`, `figi`, `figi_ticker`, `fisn`, `lei`, `cfi`, `cic`, `gics` | The fields of the same names | Copied exactly. |
| `incorporation_country`, `listing_country`, `register_country` | The fields of the same names | Copied exactly. |
| `trading_currency`, `par_value_currency` | The fields of the same names | Copied exactly. |

- Status, type, structure and voting codes are carried as the source codes, in text fields. A reader interprets them with the code set of the data source. `listing_source` is the one code that becomes a number.
- `ts_created` has no `SECURITY_DEF` field. The converter skips it and lists it in the provenance under `columns_not_carried`.
- Any other column stops the conversion.

The first record of the `secmaster-us.nwt` sample:

<!-- nwt-file: fixtures/real-reference/secmaster-us.jsonl lines=1-1 -->

## Corporate actions: SECURITY_DEF and CORPORATE_ACTION

The kind `csv-corporate-actions` reads a corporate-actions export. Every row carries the event and a copy of the facts of its listing. For each row, in order, the converter writes:

1. A `SECURITY_DEF`, when the listing has not appeared in the file yet or when any of its listing columns differs from the previous row of the same listing. Its `ts_event` is the event date of the row.
2. The `CORPORATE_ACTION`.

A corporate-actions export does not have these listing columns, so its `SECURITY_DEF` records leave the matching fields empty, zero or null: `listing_created_date`, `fisn`, `lei`, `sic`, `cik`, `gics`, `naics`, `cic`, `cfi`, `incorporation_country`, `structure`, `voting`, `vote_per_sec`, `shares_outstanding`, `shares_outstanding_date`.

| Source column | NWT field | Rule |
|---|---|---|
| `listing_id` | `instrument_id` | The number after `L-`. |
| `event_date` | `ts_event` | Date, midnight UTC. |
| `ts_record` | `ts_recv` | UTC timestamp. |
| `security_id`, `issuer_id` | `security_id`, `issuer_id` | The numbers after `S-` and `I-`. |
| `event_created_date` | `created_ns` | Date, midnight UTC. |
| `effective_date` | `effective_ns` | Date, midnight UTC. |
| `ex_date` | `ex_ns` | Date, midnight UTC. |
| `record_date` | `record_ns` | Date, midnight UTC. |
| `payment_date` | `payment_ns` | Date, midnight UTC. |
| `record_date_id` | `record_date_id` | The number after `D-`. |
| `outturn_security_id` | `outturn_security_id` | The number after `S-`. |
| `ratio_old`, `ratio_new` | `ratio_old`, `ratio_new` | Decimals scaled by 10⁹. |
| `option_id`, `serial_id` | `option_id`, `serial_id` | Whole numbers: `2.0` is 2. Empty becomes null. |
| `default_option_flag` | `action_flags` bit 0 | `True` sets the bit. `False` or empty clears it. |
| `event` | `event` | The source code, as text. |
| `event_subtype` | `subtype` | The source code, as text. |
| `event_action` | `action` | The source code, as text. |
| `global_status` | `status` | The source code, as text. |
| `mand_volu_flag` | `participation` | The source code, as text. |
| `event_date_label` | `date_label` | Copied exactly. |
| `payment_type`, `fraction`, `related_event`, `rate_currency`, `outturn_isin` | The fields of the same names | Copied exactly. |
| `related_event_id`, `event_id` | `related_event_id`, `event_id` | The whole source text, for example `E-3595409-SHOCH`. |
| `event_unique_id` | `unique_id` | The whole source text. |
| Every other filled column | `details` | Kept as JSON, as described in [The details text](#the-details-text). |

### The details text

Columns with no NWT field are kept in `details`, so no source value is dropped. `details` is one JSON object with sorted keys and no spaces. It is empty when the row has nothing to keep.

- A plain column is stored under its source column name as the exact source text: `"notification_date":"2020-08-25"`, `"to_date":"2020-08-28"`.
- The columns `date_info`, `rate_info` and `event_info` hold dictionary literals with single quotes and `None`. The converter parses them as literals, never runs them, and stores each one as a nested JSON object under its column name. `None` becomes `null`. A number becomes a string of its source digits, so `0.07` becomes `"0.07"` and no digit changes. An empty dictionary is stored as `{}`.
- The keys `source_decimals` and `source_dates` are added by the converter for rounded decimals and for dates before 1970, as described in [Rounding and dates before 1970](#rounding-and-dates-before-1970).
- A `details` text longer than 65,535 bytes stops the conversion.

A reader does not need `details` to interpret the fixed fields of the record. The `details` of one event in the `corporate-actions-us.nwt` sample:

```json
{"date_info":{},"event_info":{},"notification_date":"2020-08-25","rate_info":{},"ts_created":"2024-08-17 07:56:08.079026+00:00"}
```

## Rounding and dates before 1970

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

## Rebuild the samples

The kit keeps the source rows of every sample, so a rebuild needs no network. `fixtures/real/source/` holds the header line and the first 100 data rows of each public file, byte for byte; the two listed-securities files also keep the last row, which holds the file creation time. `fixtures/real-reference/source/` holds the rows of the security-master and corporate-actions exports. Each folder has a `SHA256SUMS` file.

1. Check the source rows. Every line of the output ends in `OK`.

   ```bash
   (cd fixtures/real/source && shasum -a 256 -c SHA256SUMS)
   (cd fixtures/real-reference/source && shasum -a 256 -c SHA256SUMS)
   ```
2. Convert the public files:

   ```bash
   python3 tools/nwt_convert_reference.py mic          fixtures/real/source/ISO10383_MIC.csv fixtures/real/venues.nwt          --retrieved 2026-10-13
   python3 tools/nwt_convert_reference.py nasdaqlisted fixtures/real/source/nasdaqlisted.txt fixtures/real/listings-nasdaq.nwt --retrieved 2026-10-13
   python3 tools/nwt_convert_reference.py otherlisted  fixtures/real/source/otherlisted.txt  fixtures/real/listings-other.nwt  --retrieved 2026-10-13
   python3 tools/nwt_convert_reference.py options      fixtures/real/source/options.txt      fixtures/real/options.nwt         --retrieved 2026-10-13
   ```
3. Convert the security-master and corporate-actions exports. Each command prints its provenance, and the rebuilt files are byte-identical to the samples.

   ```bash
   R=fixtures/real-reference
   python3 tools/nwt_convert_reference.py csv-secmaster         $R/source/secmaster-us.csv             $R/secmaster-us.nwt             --dataset REAL.SECMASTER.US
   python3 tools/nwt_convert_reference.py csv-secmaster         $R/source/secmaster-global.csv         $R/secmaster-global.nwt         --dataset REAL.SECMASTER.GLOBAL
   python3 tools/nwt_convert_reference.py csv-corporate-actions $R/source/corporate-actions-us.csv     $R/corporate-actions-us.nwt     --dataset REAL.CORPACT.US
   python3 tools/nwt_convert_reference.py csv-corporate-actions $R/source/corporate-actions-global.csv $R/corporate-actions-global.nwt --dataset REAL.CORPACT.GLOBAL
   ```
4. Write the JSON Lines view of a sample with the Python reference codec:

   ```bash
   python3 examples/python/nwt_example.py to-json fixtures/real/venues.nwt > fixtures/real/venues.jsonl
   ```
