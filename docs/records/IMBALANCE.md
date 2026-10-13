# IMBALANCE

An `IMBALANCE` record (type 16, 104 bytes) is the imbalance of an opening, closing or intraday auction: the reference, near and far prices, the paired quantity, and the unmatched quantity with its side. A producer emits it while the venue publishes imbalance information ahead of an auction. It is informational and changes no book or status state.

## Fields

<!-- nwt-fields: IMBALANCE -->

## Rules

- `imbalance_side` = 0 requires `imbalance_quantity` = 0, and `imbalance_quantity` = 0 requires `imbalance_side` = 0.
- The record is informational. It changes no book state and no status state.
- Each record replaces the earlier imbalance of the instrument.
- `reference_price` and `imbalance_quantity` are never null. The auction time, the near and far prices and the paired quantity can be null.

## Example

<!-- nwt-example: 16 -->

## Write and decode

`record 16` writes the `imbalance-buy` vector (104 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 16 work/type-16-python.bin
python3 examples/python/nwt_example.py decode-record work/type-16-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 16 work/type-16-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-16-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 16 work/type-16-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-16-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 16 work/type-16-cpp.bin
work/nwt-cpp decode-record work/type-16-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `imbalance-buy` | `fixtures/golden/records/035-imbalance-buy.bin` | Closing auction with a buy imbalance; every price and quantity is present. |
| `imbalance-none` | `fixtures/golden/records/036-imbalance-none.bin` | No imbalance: `imbalance_side` 0 and `imbalance_quantity` 0. The auction time, the near and far prices and the paired quantity are null; the auction type is unspecified. |
