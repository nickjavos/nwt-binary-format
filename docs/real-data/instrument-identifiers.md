# Instrument identifiers

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
