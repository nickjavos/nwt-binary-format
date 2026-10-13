# Symbol directories: LISTING and SYMBOL_MAP

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

## Code letters

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
