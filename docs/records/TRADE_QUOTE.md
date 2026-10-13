# TRADE_QUOTE

A `TRADE_QUOTE` record (type 18, 120 bytes) is one trade print together with the top of book immediately before it. A producer emits it when the source publishes trades with the prevailing quote. It is a derived sampling record with no correction or cancellation lifecycle.

## Fields

<!-- nwt-fields: TRADE_QUOTE -->

## Rules

- The presence rules of the bid and ask sides match [`QUOTE`](QUOTE.md).
- The record is a derived sample. It has no correction or cancel lifecycle, and it does not initialize or replace `QUOTE` state.
- A producer cannot emit `TRADE` and `TRADE_QUOTE` for the same prints on one channel.

## Example

<!-- nwt-example: 18 -->

## Write and decode

`record 18` writes the `trade-quote` vector (120 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 18 work/type-18-python.bin
python3 examples/python/nwt_example.py decode-record work/type-18-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 18 work/type-18-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-18-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 18 work/type-18-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-18-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 18 work/type-18-cpp.bin
work/nwt-cpp decode-record work/type-18-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `trade-quote` | `fixtures/golden/records/037-trade-quote.bin` | Buyer-aggressor trade at the ask, with a two-sided top of book. |
| `trade-quote-one-sided` | `fixtures/golden/records/038-trade-quote-one-sided.bin` | Absent bid side, unknown ask order count, `trade_id` 0, seller aggressor and the off-book condition. |
