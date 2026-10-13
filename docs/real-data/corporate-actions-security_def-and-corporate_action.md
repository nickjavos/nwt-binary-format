# Corporate actions: SECURITY_DEF and CORPORATE_ACTION

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

## The details text

Columns with no NWT field are kept in `details`, so no source value is dropped. `details` is one JSON object with sorted keys and no spaces. It is empty when the row has nothing to keep.

- A plain column is stored under its source column name as the exact source text: `"notification_date":"2020-08-25"`, `"to_date":"2020-08-28"`.
- The columns `date_info`, `rate_info` and `event_info` hold dictionary literals with single quotes and `None`. The converter parses them as literals, never runs them, and stores each one as a nested JSON object under its column name. `None` becomes `null`. A number becomes a string of its source digits, so `0.07` becomes `"0.07"` and no digit changes. An empty dictionary is stored as `{}`.
- The keys `source_decimals` and `source_dates` are added by the converter for rounded decimals and for dates before 1970, as described in [Rounding and dates before 1970](rounding-and-dates-before-1970.md).
- A `details` text longer than 65,535 bytes stops the conversion.

A reader does not need `details` to interpret the fixed fields of the record. The `details` of one event in the `corporate-actions-us.nwt` sample:

```json
{"date_info":{},"event_info":{},"notification_date":"2020-08-25","rate_info":{},"ts_created":"2024-08-17 07:56:08.079026+00:00"}
```
