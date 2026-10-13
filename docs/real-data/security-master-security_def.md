# Security master: SECURITY_DEF

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
