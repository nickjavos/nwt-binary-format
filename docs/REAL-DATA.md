# Real reference data

This page covers the real examples of the reference record types and the converters that made them:

| Record type | Example | Source |
|---|---|---|
| VENUE_DEF (10) | `fixtures/real/venues.nwt` | ISO 10383 market identifier list |
| OPTION_DEF (11) | `fixtures/real/options.nwt` | Option series directory |
| LISTING (12), SYMBOL_MAP (17) | `fixtures/real/listings-nasdaq.nwt`, `fixtures/real/listings-other.nwt` | Symbol directories |
| SECURITY_DEF (21) | `fixtures/real-reference/secmaster-us.nwt`, `secmaster-global.nwt` | Security-master CSV export |
| SECURITY_DEF (21), CORPORATE_ACTION (22) | `fixtures/real-reference/corporate-actions-us.nwt`, `corporate-actions-global.nwt` | Corporate-actions CSV export |

Real market data (trades, quotes, books, bars) is covered in [REAL-DATA-MARKET.md](REAL-DATA-MARKET.md).

The converter is `tools/nwt_convert_reference.py`. It registers six kinds with `tools/nwt_convert.py` and also runs on its own:

```sh
python3 tools/nwt_convert_reference.py KIND SRC OUT [--dataset NAME] [--retrieved YYYY-MM-DD]
```

It prints the provenance it wrote, as JSON. On any failure it prints `NWT error: line N: ...`, exits with status 1 and writes no output file.

## Rules that hold for every kind

- No value passes through floating point. Decimals, dates and timestamps are parsed with integer arithmetic (`tools/nwt_parse.py`).
- An unknown code, a text outside its byte limit, a missing column or a malformed value fails the conversion. Nothing is truncated, trimmed or guessed.
- Rows keep their order. Output sequences start at 1 on publisher 1, channel 0. `ts_recv` is the source record timestamp where the source has one, otherwise null.
- A source date becomes midnight UTC of that date.
- Output is deterministic. The container `created_ns` is fixed at 2026-10-13T00:00:00Z, and the stream ID is the first 16 bytes of the SHA-256 of the source file. The same source bytes give the same container bytes.
- Every container has a PROVENANCE element with the source kind, the SHA-256 and row count of the source, the record counts, the policy text, and the counts described under [Policies](#policies).

## Public files

Retrieved on 13 October 2026.

| Kind | URL | Size retrieved | Rows |
|---|---|---:|---:|
| `nasdaqlisted` | `https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt` | 349,212 bytes | 5,626 |
| `otherlisted` | `https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt` | 542,753 bytes | 7,659 |
| `options` | `https://www.nasdaqtrader.com/dynamic/SymDir/options.txt` | first 1,048,576 bytes of about 88 MB, by HTTP range request; 1,048,522 bytes after the last, partial line was dropped | 19,631 |
| `mic` | `https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv` | 590,760 bytes | 2,889 |

The fixtures are built from small slices saved in `fixtures/real/source/`, so they rebuild offline. Each slice is the header line and the first 100 data rows, bytes unchanged. The two listed-securities slices also keep the file's last row, which holds the file creation time. `fixtures/real/source/SHA256SUMS` lists the slices.

### Code tables

The letters and their meanings were checked against the publisher's page "Symbol Look-Up/Directory Data Fields & Definitions", `https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs`, read on 13 October 2026. A letter that is not in a table fails the conversion.

Market Category (`nasdaqlisted`) to LISTING `market_tier`:

| Letter | Publisher's meaning | `market_tier` |
|---|---|---:|
| Q | Nasdaq Global Select Market | 1 |
| G | Nasdaq Global Market | 2 |
| S | Nasdaq Capital Market | 3 |

Financial Status (`nasdaqlisted`) to LISTING `financial_flags` (bit 0 reported, bit 1 deficient, bit 2 delinquent, bit 3 bankrupt):

| Letter | Publisher's meaning | `financial_flags` |
|---|---|---:|
| N | Normal: not deficient, delinquent or bankrupt | 1 |
| D | Deficient | 3 |
| E | Delinquent | 5 |
| Q | Bankrupt | 9 |
| G | Deficient and bankrupt | 11 |
| H | Deficient and delinquent | 7 |
| J | Delinquent and bankrupt | 13 |
| K | Deficient, delinquent and bankrupt | 15 |

Exchange (`otherlisted`) to LISTING `listing_mic`:

| Letter | Publisher's meaning | `listing_mic` | Name of that MIC in the ISO 10383 list |
|---|---|---|---|
| A | NYSE MKT | XASE | NYSE AMERICAN LLC |
| N | New York Stock Exchange (NYSE) | XNYS | NEW YORK STOCK EXCHANGE, INC. |
| P | NYSE ARCA | ARCX | NYSE ARCA |
| Z | BATS Global Markets (BATS) | BATS | CBOE BZX U.S. EQUITIES EXCHANGE |
| V | Investors' Exchange, LLC (IEXG) | IEXG | INVESTORS EXCHANGE |

Options Closing Type and Options Type (`options`):

| Column | Letter | Publisher's meaning | NWT value |
|---|---|---|---|
| Options Closing Type | N | Normal hours | `closing_type` 1 |
| Options Closing Type | L | Late hours | `closing_type` 2 |
| Options Type | C | Call | `right` 1 |
| Options Type | P | Put | `right` 2 |

Yes/no columns (Test Issue, ETF, NextShares, Pending) accept `Y` and `N` only.

What the page does not settle:

- **Exchange letters F and M.** The other-listed file retrieved on 13 October 2026 has 21 rows with exchange `F` and one with `M`. The page lists neither. The converter therefore stops at the first such row of the full file. The saved slice holds only N, Z, P and A.
- **The MIC for each exchange letter** is this kit's choice. The page gives market names, not MICs. The names agree with the ISO 10383 list for N, P, V and Z (whose acronym there is BATS). For A the page says "NYSE MKT" and the list says "NYSE AMERICAN LLC"; that these are one market under an older and a newer name is not stated on either page.
- **ETF and NextShares in the Nasdaq-listed file.** The page defines the ETF column only for the other-listed file, and does not define NextShares at all. Both are read as yes/no flags.
- **Time zone of the file creation time.** The page gives the layout `mmddyyyyhh:mm` but no zone. The converter reads it as US Eastern time. The evidence: the file retrieved on 13 October 2026 says `12:11` and the server's `Last-Modified` header for it was `16:11:10 GMT`.

### `nasdaqlisted` and `otherlisted`: LISTING and SYMBOL_MAP

Each row gives one LISTING and then one SYMBOL_MAP for the same instrument.

| NWT | `nasdaqlisted` column | `otherlisted` column |
|---|---|---|
| `instrument_id` | ID of (`XNAS`, Symbol) | ID of (`listing_mic`, ACT Symbol) |
| `ts_event` | file creation time | file creation time |
| `round_lot` | Round Lot Size | Round Lot Size |
| `listing_flags` bit 0 | ETF | ETF |
| `listing_flags` bit 1 | Test Issue | Test Issue |
| `listing_flags` bit 2 | NextShares | not in the file: 0 |
| `market_tier` | Market Category | not in the file: 0 |
| `financial_flags` | Financial Status | not in the file: 0 (not reported) |
| `symbol` | Symbol | ACT Symbol |
| `name` | Security Name | Security Name |
| `listing_mic` | `XNAS` | from Exchange |
| `cqs_symbol` | empty | CQS Symbol |
| `alt_symbol` | empty | NASDAQ Symbol |

The SYMBOL_MAP has `symbology` 1 (native), `symbol` as above, `valid_from_ns` equal to the file creation time and a null `valid_to_ns` (open-ended). A file with data rows but no creation-time row fails, because `valid_from_ns` would be unknown. A symbol that appears twice in one file fails.

### `options`: OPTION_DEF

| NWT | Source column |
|---|---|
| `instrument_id` | ID of (`XNDQ`, key); the key is the root, the expiration as `YYYY-MM-DD`, `C` or `P`, and the strike with nine decimals, joined by a vertical bar: `A\|2028-01-21\|P\|100.000000000` |
| `ts_event` | file creation time, or null when the source has no creation-time row (the saved slice has none: it is the start of the file) |
| `expiration_ns` | Expiration Date (`mm/dd/yyyy`), midnight UTC |
| `strike` | Explicit Strike Price, exact |
| `right` | Options Type |
| `closing_type` | Options Closing Type |
| `option_flags` bit 0 (pending) | Pending |
| `root` | Root Symbol |
| `underlying_symbol` | Underlying Symbol |
| `underlying_instrument_id` | 0: the file names the underlying by symbol only |
| `exercise_style`, `settlement` | 0 (unknown): not in the file, and never inferred |
| `contract_multiplier` | null: not in the file |
| `option_flags` bit 1 (adjusted) | 0: not in the file |
| `osi_symbol`, `currency` | empty: not in the file |

Underlying Issue Name has no OPTION_DEF field and is not carried; the provenance says so. XNDQ is the MIC that the ISO 10383 list names "NASDAQ OPTIONS MARKET". A series that appears twice fails.

### `mic`: VENUE_DEF

| NWT | Source column |
|---|---|
| `mic` | MIC |
| `operating_mic` | OPERATING MIC |
| `kind` | OPRT/SGMT: `OPRT` 1, `SGMT` 2 |
| `status` | STATUS: `ACTIVE` 1, `UPDATED` 2, `EXPIRED` 3 |
| `created_ns` | CREATION DATE (`YYYYMMDD`) |
| `updated_ns` | LAST UPDATE DATE |
| `expiry_ns` | EXPIRY DATE; null when empty |
| `country` | ISO COUNTRY CODE (ISO 3166) |
| `category` | MARKET CATEGORY CODE |
| `acronym` | ACRONYM |
| `city` | CITY |
| `name` | MARKET NAME-INSTITUTION DESCRIPTION |
| `legal_entity` | LEGAL ENTITY NAME |
| `lei` | LEI |

The header instrument is 0 and `ts_event` is null; the source dates are in the three date fields. An `OPRT` row whose MIC differs from its OPERATING MIC fails. WEBSITE, LAST VALIDATION DATE and COMMENTS have no VENUE_DEF field and are not carried; the provenance says so. A column the converter does not know fails the conversion.

### Instrument IDs

The symbol directories carry no numeric IDs. The converter uses `instrument_id_for(namespace, key)` from `tools/nwt_ids.py`: the first 63 bits of the SHA-256 of the namespace, a NUL byte and the key. The ID of a symbol does not change when other rows come or go. Two different keys that give one ID fail the conversion with both keys named.

## Security master and corporate actions

The source is a licensed vendor CSV export; see `fixtures/real-reference/NOTICE.md`. The fixtures are built from the rows saved in `fixtures/real-reference/source/` (listed in its `SHA256SUMS`): both security-master files in full, the US corporate-actions file in full, and the first 500 rows of the global corporate-actions file.

The manifest publisher is 1, named `reference-data`. The dataset is set with `--dataset`: `REAL.SECMASTER.US`, `REAL.SECMASTER.GLOBAL`, `REAL.CORPACT.US`, `REAL.CORPACT.GLOBAL`.

### `csv-secmaster`: SECURITY_DEF

One SECURITY_DEF per row. The same mapping builds the SECURITY_DEF of a corporate-actions row, from the listing columns that row has.

| NWT | Source column | Note |
|---|---|---|
| `instrument_id` | `listing_id` | number after `L-`; must not be zero |
| `ts_event` | `ts_effective` | in a corporate-actions row: `event_date` |
| `ts_recv` | `ts_record` | |
| `listing_group_id` | `listing_group_id` | number after `LG-` |
| `security_id` | `security_id` | number after `S-` |
| `issuer_id` | `issuer_id` | number after `I-` |
| `listing_created_ns` | `listing_created_date` | |
| `listing_ns` | `listing_date` | |
| `delisting_ns` | `delisting_date` | |
| `shares_outstanding` | `shares_outstanding` | whole count; `855630000.0` is 855630000 |
| `shares_outstanding_ns` | `shares_outstanding_date` | |
| `lot_size` | `lot_size` | × 10⁹ |
| `par_value` | `par_value` | × 10⁹ |
| `votes_per_share` | `vote_per_sec` | × 10⁹ |
| `cik`, `sic`, `naics` | same names | whole numbers; `7370.0` is 7370, `7370.5` fails; empty is 0 |
| `listing_source` | `listing_source` | `M` (main) 1, `S` (secondary) 2, empty 0 |
| `security_flags` bit 0 | `multi_currency` | `True` sets it; `False` or empty clears it |
| `issuer_name` | `issuer_name` | |
| `description` | `security_description` | |
| `security_type`, `structure`, `listing_status`, `voting` | same names | source codes, as text |
| `primary_exchange`, `exchange`, `operating_mic`, `segment_mic` | same names | |
| `segment_name` | `segment_mic_name` | |
| `symbol` | `symbol` | |
| `alt_symbol` | `nasdaq_symbol` | |
| `local_code`, `isin`, `figi`, `figi_ticker`, `fisn`, `lei`, `cfi`, `cic`, `gics` | same names | |
| `cusip` | `us_code` | |
| `composite_figi` | `bbg_comp_id` | |
| `composite_ticker` | `bbg_comp_ticker` | |
| `incorporation_country`, `listing_country`, `register_country` | same names | |
| `trading_currency`, `par_value_currency` | same names | |

An identifier without its prefix fails with the column and line named. An empty number is null (or 0 for an ID, `cik`, `sic`, `naics`); an empty text is empty.

SECURITY_DEF has no free text, so two things differ from corporate actions:

- `ts_created` (when the vendor added the row to its database) has no field and is not carried. The provenance lists it under `columns_not_carried`.
- A column the converter does not know fails the conversion, rather than being dropped.

### `csv-corporate-actions`: SECURITY_DEF and CORPORATE_ACTION

Every row carries a copy of the listing's facts. For each row, in order:

1. A SECURITY_DEF is written if the listing has not been seen in this file, or if any of its listing columns differs from the previous row of the same listing. Its `ts_event` is the row's event date: the date of the event whose row carried the facts, not a date on which they became effective.
2. The CORPORATE_ACTION is written.

A corporate-actions row lacks these listing columns, so its SECURITY_DEF leaves them empty, zero or null: `listing_created_date`, `fisn`, `lei`, `sic`, `cik`, `gics`, `naics`, `cic`, `cfi`, `incorporation_country`, `structure`, `voting`, `vote_per_sec`, `shares_outstanding`, `shares_outstanding_date`.

| NWT | Source column | Note |
|---|---|---|
| `instrument_id` | `listing_id` | number after `L-` |
| `ts_event` | `event_date` | |
| `ts_recv` | `ts_record` | |
| `security_id`, `issuer_id` | same names | numbers after `S-` and `I-` |
| `created_ns` | `event_created_date` | |
| `effective_ns` | `effective_date` | |
| `ex_ns` | `ex_date` | |
| `record_ns` | `record_date` | |
| `payment_ns` | `payment_date` | |
| `record_date_id` | `record_date_id` | number after `D-` |
| `outturn_security_id` | `outturn_security_id` | number after `S-` |
| `ratio_old`, `ratio_new` | same names | × 10⁹ |
| `option_id`, `serial_id` | same names | whole numbers; `1.0` is 1; empty is null |
| `action_flags` bit 0 | `default_option_flag` | `True` sets it |
| `event` | `event` | |
| `subtype` | `event_subtype` | |
| `action` | `event_action` | |
| `status` | `global_status` | |
| `participation` | `mand_volu_flag` | |
| `payment_type`, `fraction`, `related_event`, `rate_currency`, `outturn_isin` | same names | |
| `date_label` | `event_date_label` | |
| `related_event_id`, `event_id` | same names | whole source text, for example `E-3595409-SHOCH` |
| `unique_id` | `event_unique_id` | whole source text |
| `details` | every other filled column | see below |

## Policies

### Codes stay as text

Status, action, type and participation letters in the security-master and corporate-actions data are carried as the source codes, in text fields. They are not turned into enums, because their lookup tables are not part of the material this kit was built from. The one exception is `listing_source`, whose two letters are explained by the column's own description (main, secondary).

Systems that exchange these files must agree on the code set, as they must for a currency code.

### Rounding

NWT prices and ratios hold nine decimal places. A few source values are floating-point artefacts with more, for example `0.30000000000000004`.

- Such a value is rounded half to even at nine places. `0.30000000000000004` becomes 300000000.
- The provenance counts them in `rounded_decimals`.
- In a corporate-actions file, the original text is kept in the row's `details`, under `source_decimals`, by source column name: `"source_decimals":{"par_value":"0.139682539682"}`. The count and the kept text are per source row, also when the row's SECURITY_DEF was not written again.
- In a security-master file there is no `details` text, so the provenance lists each one under `not_exact`, with its line, column and source text.
- Numbers such as `6e-06` and `7370.0` are not rounded. They are parsed exactly.
- Values in the public files are never rounded. A strike with more than nine decimals fails.

Dates before 1970 are handled the same way, because an NWT timestamp cannot hold them. The field is null, the provenance counts them in `dates_before_1970`, and the source text is kept under `source_dates` in `details` (or under `not_exact` for a security-master file). An example from the fixtures: `"source_dates":{"listing_date":"1929-02-14"}`.

In the fixtures: one rounded decimal and one date before 1970 in `corporate-actions-us`; one date before 1970 in `corporate-actions-global`; none in the two security-master files.

### `details`

`details` of a CORPORATE_ACTION is one JSON object with sorted keys and no spaces. It holds every filled source column that has no field or text of its own, so no source value is dropped:

- A plain column is stored under its source column name as the source text, unchanged: `"rd_priority":"1.0"`, `"to_date":"2020-08-28"`, `"ts_created":"2024-08-17 07:29:41.538303+00:00"`.
- Three columns (`date_info`, `rate_info`, `event_info`) hold Python-style dictionaries with single quotes and `None`. They are parsed as literals with `ast.literal_eval` and are never run. Each is stored as a nested JSON object under its column name. `None` becomes `null`. A number becomes a string of its source digits (`0.07` becomes `"0.07"`), so no float is created and no digit changes. An empty dictionary is stored as `{}`.
- `source_decimals` and `source_dates` are added by the converter, as described above.

A reader does not need `details` to interpret the fixed fields. A `details` text over 65,535 bytes fails the conversion.

## What could not be confirmed

- The meanings of the vendor's code letters (listing status, event action, global status, participation, payment type, fraction, voting, security type, structure, event and subtype codes). They are carried as text for that reason.
- `status` is filled from `global_status`, which the column reference describes as the activity status of the security, not of the event. It is the only status column besides the listing status.
- `symbol` is described in the column reference as the symbol the export was requested with. It is stored as `symbol`; `nasdaq_symbol` is stored as `alt_symbol` and `local_code` as `local_code`.
- `record_date_id` and `related_event_id` are typed as dates in the column reference but hold identifiers (`D-6746356`, `E-6703187-RTS`). `option_id` and `serial_id` are typed as strings but hold numbers written like `1.0`. The converter follows the data.
- The four points listed under [Code tables](#code-tables).

## Rebuild

From the kit root. The slices are already in place, so no network is needed.

```sh
(cd fixtures/real/source && shasum -a 256 -c SHA256SUMS)
(cd fixtures/real-reference/source && shasum -a 256 -c SHA256SUMS)
C="tools/nwt_convert_reference.py"

python3 $C mic          fixtures/real/source/ISO10383_MIC.csv fixtures/real/venues.nwt          --retrieved 2026-10-13
python3 $C nasdaqlisted fixtures/real/source/nasdaqlisted.txt fixtures/real/listings-nasdaq.nwt --retrieved 2026-10-13
python3 $C otherlisted  fixtures/real/source/otherlisted.txt  fixtures/real/listings-other.nwt  --retrieved 2026-10-13
python3 $C options      fixtures/real/source/options.txt      fixtures/real/options.nwt         --retrieved 2026-10-13

R=fixtures/real-reference
python3 $C csv-secmaster         $R/source/secmaster-us.csv             $R/secmaster-us.nwt             --dataset REAL.SECMASTER.US
python3 $C csv-secmaster         $R/source/secmaster-global.csv         $R/secmaster-global.nwt         --dataset REAL.SECMASTER.GLOBAL
python3 $C csv-corporate-actions $R/source/corporate-actions-us.csv     $R/corporate-actions-us.nwt     --dataset REAL.CORPACT.US
python3 $C csv-corporate-actions $R/source/corporate-actions-global.csv $R/corporate-actions-global.nwt --dataset REAL.CORPACT.GLOBAL
```

`python3 tools/nwt_convert.py KIND SRC OUT ...` takes the same arguments.

The two views of each fixture come from the reference codec:

```sh
for f in fixtures/real/*.nwt fixtures/real-reference/*.nwt; do
  python3 examples/python/nwt_example.py to-json "$f" > "${f%.nwt}.jsonl"
  python3 examples/python/nwt_example.py read    "$f" > "${f%.nwt}.fields.txt"
done
```

Add `--pretty` to `to-json` for decimal prices and ISO 8601 timestamps.

A rebuild must give these files:

| Fixture | Source rows | Records | Bytes | SHA-256 |
|---|---:|---|---:|---|
| `fixtures/real/venues.nwt` | 100 | 100 VENUE_DEF | 20,560 | `93d535dfe26c4171949d76fb5653b6be575006dcf10883e750f2a4927a161cc0` |
| `fixtures/real/listings-nasdaq.nwt` | 100 | 100 LISTING, 100 SYMBOL_MAP | 22,720 | `5e4ad00de5cf80da838ed1f57a5b8fae1481636498331f914de8dd615e870e93` |
| `fixtures/real/listings-other.nwt` | 100 | 100 LISTING, 100 SYMBOL_MAP | 23,312 | `c69fa1810dbdbeb3cc86b9d539a126b8b71b0f5fbb26b257bdc4995bf249d15c` |
| `fixtures/real/options.nwt` | 100 | 100 OPTION_DEF | 12,424 | `f6a279dba6a68b9626c17851d8e5b0e863cc309ed877bd16e808086260b578e4` |
| `fixtures/real-reference/secmaster-us.nwt` | 28 | 28 SECURITY_DEF | 12,704 | `b17425d3a128597b5ab078954606d2cd1e33c8af44126959c8066b42dd0cb8e4` |
| `fixtures/real-reference/secmaster-global.nwt` | 195 | 195 SECURITY_DEF | 76,224 | `b93c797c7c25356aa5bff4a6cbc4fe5815e16415f4fc7aa83a793cb0f71867c1` |
| `fixtures/real-reference/corporate-actions-us.nwt` | 864 | 777 SECURITY_DEF, 864 CORPORATE_ACTION | 798,520 | `1d24f5636a5e16546b914b4d1ed390aea203d71ad91d2f7c251442f8f1ad56ac` |
| `fixtures/real-reference/corporate-actions-global.nwt` | 500 | 442 SECURITY_DEF, 500 CORPORATE_ACTION | 442,672 | `e7d3d3a318c02406cdec62d2119209e710a86b0ef61c47bc4d443a6c5a88c551` |

To convert a whole public file, download it and pass it as `SRC`. For the option series file, a range request for the first megabyte is enough for a sample; drop the last, partial line before converting.
