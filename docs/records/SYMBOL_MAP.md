# SYMBOL_MAP

A `SYMBOL_MAP` record (type 17, 72 bytes plus text) states that a symbol names an instrument over a half-open time interval, in one of six symbologies: native, OSI, ISIN, FIGI, root or continuous. The instrument in the record header is the mapped instrument. A producer emits it to tie external identifiers to instrument IDs, and again when a symbol starts to name another instrument. It is a reference record.

## Fields

<!-- nwt-fields: SYMBOL_MAP -->

## Rules

- The interval is half-open.
- For symbologies 1–4 and 6, the intervals of one `(publisher, symbology, symbol)` do not overlap: a symbol names one instrument at any time.
- Symbology 5 (root) is one-to-many.
- One instrument can have many symbols.

## Example

<!-- nwt-example: 17 -->

## Write and decode

`record 17` writes the `symbol-map-native` vector (80 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 17 work/type-17-python.bin
python3 examples/python/nwt_example.py decode-record work/type-17-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 17 work/type-17-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-17-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 17 work/type-17-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-17-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 17 work/type-17-cpp.bin
work/nwt-cpp decode-record work/type-17-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `symbol-map-native` | `fixtures/golden/records/012-symbol-map-native.bin` | Native symbol with an open-ended interval (`valid_to_ns` null). |
| `symbol-map-closed-isin` | `fixtures/golden/records/013-symbol-map-closed-isin.bin` | ISIN with a closed interval. |
| `symbol-map-root` | `fixtures/golden/records/014-symbol-map-root.bin` | Root symbol (symbology 5) mapped to the option. The interval ends at the expiration. |
