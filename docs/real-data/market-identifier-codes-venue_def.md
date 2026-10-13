# Market identifier codes: VENUE_DEF

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
