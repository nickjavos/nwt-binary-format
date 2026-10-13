# LISTING

A `LISTING` record (type 12, 72 bytes plus text) is one row of a symbol directory: symbol, name, listing venue, round lot, ETF and test-issue flags, market tier and financial status. A producer emits one record per listed instrument when it publishes or refreshes the directory. It is a reference record.

## Fields

<!-- nwt-fields: LISTING -->

## Rules

- The identity is `(publisher, instrument)`.
- Bits 1–3 of `financial_flags` require bit 0.
- `financial_flags` = 1 means a normal financial status. `financial_flags` = 0 means the source does not report a financial status.
- The `ts_event` of a directory row is often null.

## Example

<!-- nwt-example: 12 -->

## Write and decode

`record 12` writes the `listing-normal` vector (120 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 12 work/type-12-python.bin
python3 examples/python/nwt_example.py decode-record work/type-12-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 12 work/type-12-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-12-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 12 work/type-12-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-12-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 12 work/type-12-cpp.bin
work/nwt-cpp decode-record work/type-12-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `listing-normal` | `fixtures/golden/records/006-listing-normal.bin` | Common stock: round lot 100, `market_tier` 1, `financial_flags` 1 (reported, normal), null `ts_event`. |
| `listing-etf-deficient` | `fixtures/golden/records/007-listing-etf-deficient.bin` | ETF flag, `market_tier` 2, `financial_flags` 3 (reported and deficient), empty `cqs_symbol`. |
| `listing-minimal` | `fixtures/golden/records/008-listing-minimal.bin` | Only `symbol` is filled: both timestamps are null, `round_lot` is unknown (`UINT32_MAX`) and every optional text is empty. |
| `listing-awkward-text` | `fixtures/golden/records/009-listing-awkward-text.bin` | Test-issue flag and a `name` that contains a comma, double quotes, a backslash, a line break, a control character and a non-ASCII letter. Exercises escaping in JSON and CSV output. |
