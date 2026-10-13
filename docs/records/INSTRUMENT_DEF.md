# INSTRUMENT_DEF

An `INSTRUMENT_DEF` record (type 6, 112 bytes plus text) is the definition that every market record depends on: symbol, venue, currency, quantity unit, price and quantity increments, contract multiplier, expiration, strike, underlying and one of eight asset classes. A producer emits it before the first market record of an instrument, and again when the definition changes.

## Fields

<!-- nwt-fields: INSTRUMENT_DEF -->

## Rules

**Values.**

- `currency` and `quantity_unit` are case-sensitive codes defined by the producer, for example `USD`, `BTC`, `share`, `contract` or `base-unit`. Systems that exchange data must agree on them.
- A non-null price increment, quantity increment and multiplier are positive. Null means unavailable.
- The price increment can be null for a venue with a variable tick schedule. The format does not encode such a schedule.
- A nonzero underlying refers to the namespace of the same publisher. It need not have a definition in this container.
- `INSTRUMENT_DEF` does not carry option rights, exercise style or settlement rules. [`OPTION_DEF`](OPTION_DEF.md) carries them, [`SECURITY_DEF`](SECURITY_DEF.md) carries identifiers and listing facts, and [`CORPORATE_ACTION`](CORPORATE_ACTION.md) carries events.
- A producer that lacks a fact says "unknown". A consumer cannot infer these facts from the symbol.

**Scope and order.**

- The scope of a definition is `(publisher, instrument)` across all channels.
- A definition precedes every market record of the instrument in byte order. The market records are listed in [Scope and required schemas](../specification/record-types.md#scope-and-required-schemas).
- A later definition replaces the current one for the records that follow it, whatever its timestamp. `ts_event` describes the definition event at the source. It does not permit applying the definition to earlier records.
- The dataset, the economic identity, the currency and the quantity unit never change for an existing instrument ID. The symbol, the increments, the multiplier and other reference attributes can change.
- Values already in a book stay encoded in the same units. A definition update does not rescale stored orders.

## Example

<!-- nwt-example: 6 -->

## Write and decode

`record 6` writes the `definition-1` vector (136 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 6 work/type-6-python.bin
python3 examples/python/nwt_example.py decode-record work/type-6-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 6 work/type-6-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-6-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 6 work/type-6-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-6-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 6 work/type-6-cpp.bin
work/nwt-cpp decode-record work/type-6-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `definition-1` | `fixtures/records/001-definition-1.bin` | Equity (`asset_class` 1): null expiration and strike, no underlying. The other vectors of types 1–7 in this catalog refer to this instrument. |
| `definition-0` | `fixtures/records/043-definition-0.bin` | `asset_class` 0, unspecified. |
| `definition-2` | `fixtures/records/044-definition-2.bin` | Future (`asset_class` 2) with an expiration. |
| `definition-3` | `fixtures/records/045-definition-3.bin` | Option (`asset_class` 3) with an expiration, a strike and an underlying instrument. |
| `definition-4` | `fixtures/records/046-definition-4.bin` | FX (`asset_class` 4). |
| `definition-5` | `fixtures/records/047-definition-5.bin` | Crypto (`asset_class` 5). |
| `definition-6` | `fixtures/records/048-definition-6.bin` | Index (`asset_class` 6). |
| `definition-7` | `fixtures/records/049-definition-7.bin` | Fixed income (`asset_class` 7). |
| `def-equity` | `fixtures/golden/records/001-def-equity.bin` | The equity that the market vectors of the conformance file refer to. |
| `def-option` | `fixtures/golden/records/002-def-option.bin` | The option on that equity: expiration, strike, underlying, multiplier 100 and a 21-byte OSI symbol. |
