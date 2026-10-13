# Instrument definitions: INSTRUMENT_DEF and OPTION_DEF

The kind `csv-definition` converts a definitions export on its own. The other kinds apply the same mapping to the rows of the `--definitions` file.

| Source column | NWT field | Rule |
|---|---|---|
| `raw_symbol` | `symbol` | Copied exactly. An empty symbol stops the conversion. |
| `instrument_class` | `asset_class` | `K` is 1 (equity), `F` is 2 (future), `C` and `P` are 3 (option). `B`, `I`, `M`, `S`, `T`, `X` and `Y` are 0 (unspecified). Any other letter stops the conversion. |
| `min_price_increment` | `price_increment` | Exact decimal. Empty becomes null. Zero or a negative value stops the conversion. |
| `expiration` | `expiration_ns` | UTC timestamp. Empty becomes null. |
| `underlying_id` | `underlying_instrument_id` | Kept. 0 means that the instrument has no underlying. |
| `strike_price` | `strike` | Exact decimal. Empty becomes null. |
| `exchange` | `venue` | Copied exactly. When empty, the value of `--venue`, or an empty text. |
| `currency` | `currency` | Copied exactly. When empty, the value of `--currency`. |
| `security_update_action` | None | `A` and `M` write a definition. A `D` row is skipped and counted. Any other letter stops the conversion. |

The converter sets the remaining fields:

- `quantity_unit` is the value of `--quantity-unit`.
- `quantity_increment` is null. The export has lot sizes, not a size increment.
- `contract_multiplier` is null. The export has a contract size in a unit of measure, which is not a price multiplier.

A call or a put also gets an `OPTION_DEF`, directly after its `INSTRUMENT_DEF`:

| Source column | NWT field | Rule |
|---|---|---|
| `instrument_class` | `right` | `C` is 1 (call), `P` is 2 (put). |
| `underlying_id` | `underlying_instrument_id` | The same value as in the `INSTRUMENT_DEF`. |
| `expiration` | `expiration_ns` | The same value as in the `INSTRUMENT_DEF`. An option row with no expiration stops the conversion. |
| `strike_price` | `strike` | The same value as in the `INSTRUMENT_DEF`. An option row with no strike stops the conversion. |
| `asset` | `root` | Copied exactly. When empty, the root of the OSI symbol. A row with neither stops the conversion. |
| `underlying` | `underlying_symbol` | Copied exactly. |
| `raw_symbol` | `osi_symbol` | Only when the symbol has the 21-character OSI layout. Otherwise empty. |
| `cfi` | `exercise_style` | For a six-letter code that starts with `O`: third letter `A` is 1 (American), `E` is 2 (European). Anything else is 0 (unknown). |
| `currency` | `currency` | The same value as in the `INSTRUMENT_DEF`. |

- `settlement`, `closing_type` and `option_flags` are 0, and `contract_multiplier` is null.
- Exercise style is never inferred from a symbol.
- An option row with neither an underlying ID nor an underlying symbol cannot form an `OPTION_DEF`. It gets its `INSTRUMENT_DEF` only, and the provenance counts it under `notes`.

An option from the `option-definitions.nwt` sample, as its `INSTRUMENT_DEF` and its `OPTION_DEF`:

<!-- nwt-file: fixtures/real-market/option-definitions.jsonl lines=2-3 -->
