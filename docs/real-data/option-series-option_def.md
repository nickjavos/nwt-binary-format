# Option series: OPTION_DEF

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
