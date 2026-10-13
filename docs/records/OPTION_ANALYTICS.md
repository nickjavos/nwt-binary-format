# OPTION_ANALYTICS

An `OPTION_ANALYTICS` record (type 14, 120 bytes) carries implied volatility, delta, gamma, theta, vega and rho of an option, with the underlying price and a theoretical price. A producer emits it when it recalculates the analytics. Every value is a fixed-point integer scaled by 10⁹ and independently nullable.

## Fields

<!-- nwt-fields: OPTION_ANALYTICS -->

## Rules

- The asset class in the `INSTRUMENT_DEF` of the instrument is option.
- Every `i64` field is scaled by 10⁻⁹ and is nullable on its own, with the null value `INT64_MIN`.
- A non-null implied volatility and a non-null gamma are ≥ 0. A non-null delta lies within −1 to +1.
- At least one of the six analytics, from `implied_volatility` through `rho`, is non-null.
- A producer rounds to nine decimals. The wire value is authoritative.
- Each record replaces the earlier analytics of the instrument.

## Example

<!-- nwt-example: 14 -->

## Write and decode

`record 14` writes the `analytics-full` vector (120 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 14 work/type-14-python.bin
python3 examples/python/nwt_example.py decode-record work/type-14-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 14 work/type-14-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-14-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 14 work/type-14-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-14-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 14 work/type-14-cpp.bin
work/nwt-cpp decode-record work/type-14-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `analytics-full` | `fixtures/golden/records/032-analytics-full.bin` | All eight values present; price basis mid, model Black-Scholes-Merton. |
| `analytics-iv-only` | `fixtures/golden/records/033-analytics-iv-only.bin` | Only the implied volatility is non-null; price basis and model are unspecified. |
| `analytics-put-negative` | `fixtures/golden/records/034-analytics-put-negative.bin` | Negative delta and rho, as for a put; price basis settlement, binomial model. |
