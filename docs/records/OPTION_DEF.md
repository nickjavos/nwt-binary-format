# OPTION_DEF

An `OPTION_DEF` record (type 11, 96 bytes plus text) carries the terms of one option contract: underlying, expiration, strike, multiplier, right, exercise style, settlement, and the root, underlying and OSI symbols. A producer emits it for each option contract, and again when the terms change. A fact the producer does not know is written as “unknown”.

## Fields

<!-- nwt-fields: OPTION_DEF -->

## Rules

- The identity is `(publisher, instrument)`. A later record replaces the earlier one.
- `underlying_instrument_id` = 0 requires a non-empty `underlying_symbol`.
- If an `INSTRUMENT_DEF` exists for the same instrument, its asset class is option, and its expiration, strike and underlying equal the values of this record.
- A producer that does not know a fact uses "unknown". It cannot infer the exercise style or the settlement from the symbol.

## Example

<!-- nwt-example: 11 -->

## Write and decode

`record 11` writes the `option-def-call` vector (128 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 11 work/type-11-python.bin
python3 examples/python/nwt_example.py decode-record work/type-11-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 11 work/type-11-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-11-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 11 work/type-11-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-11-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 11 work/type-11-cpp.bin
work/nwt-cpp decode-record work/type-11-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `option-def-call` | `fixtures/golden/records/010-option-def-call.bin` | Call with American exercise, physical settlement, a normal-hours close, multiplier 100 and a 21-byte OSI symbol. The underlying is given by instrument ID. |
| `option-def-unknowns` | `fixtures/golden/records/011-option-def-unknowns.bin` | Put with `underlying_instrument_id` 0 and the underlying named by symbol. Multiplier, exercise style, settlement and closing type are unknown; the pending and adjusted flags are set; the OSI symbol and the currency are empty. |
