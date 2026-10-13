# STATISTICS

A `STATISTICS` record (type 13, 80 bytes) is one official statistic of an instrument: open, high, low, close, settlement, VWAP, volume or open interest, with the session or date it refers to in `ts_ref`. A producer emits it when the venue publishes, revises or withdraws an official value.

## Fields

<!-- nwt-fields: STATISTICS -->

## Rules

- Statistic types 1–6 are price types. Types 7 and 8 are quantity types.
- `SET` of a price type requires a non-null price and a null quantity. `SET` of a quantity type requires a non-null quantity and a null price.
- `DELETE` requires both values null and `stat_flags` = 0.
- The latest `SET` for `(instrument, stat_type, ts_ref)` replaces the earlier ones. `DELETE` withdraws the value.

## Example

<!-- nwt-example: 13 -->

## Write and decode

`record 13` writes the `stat-open` vector (80 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 13 work/type-13-python.bin
python3 examples/python/nwt_example.py decode-record work/type-13-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 13 work/type-13-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-13-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 13 work/type-13-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-13-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 13 work/type-13-cpp.bin
work/nwt-cpp decode-record work/type-13-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `stat-open` | `fixtures/golden/records/027-stat-open.bin` | `SET` of the open price: non-null price, null quantity. |
| `stat-settlement-preliminary` | `fixtures/golden/records/028-stat-settlement-preliminary.bin` | `SET` of the settlement price with the preliminary flag. |
| `stat-volume` | `fixtures/golden/records/029-stat-volume.bin` | `SET` of the volume, a quantity type: null price, non-null quantity. |
| `stat-open-interest` | `fixtures/golden/records/030-stat-open-interest.bin` | `SET` of the open interest of the option. |
| `stat-delete` | `fixtures/golden/records/031-stat-delete.bin` | `DELETE` of the settlement price: both values null, flags 0. |
