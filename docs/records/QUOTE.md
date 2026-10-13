# QUOTE

A `QUOTE` record (type 2, 96 bytes) is the best bid and the best ask of one instrument, each with its quantity and order count. A producer emits it whenever the top of book changes. Every record replaces both sides, and an empty quote is valid and clears both.

## Fields

<!-- nwt-fields: QUOTE -->

## Rules

- An absent side has a null price, zero quantity and zero count.
- A present side has a non-null price and a quantity from 1 through `UINT64_MAX` − 1. Its count is positive or null.
- Negative prices are allowed.
- A crossed or locked quote is representable. Bid ≥ ask is not a reason for a reader to reject a quote.
- An empty quote is valid and clears both sides. It does not clear `MBO` state or aggregate-depth state kept from other record types.

## Example

<!-- nwt-example: 2 -->

## Write and decode

`record 2` writes the `quote-two-sided` vector (96 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 2 work/type-2-python.bin
python3 examples/python/nwt_example.py decode-record work/type-2-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 2 work/type-2-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-2-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 2 work/type-2-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-2-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 2 work/type-2-cpp.bin
work/nwt-cpp decode-record work/type-2-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `quote-two-sided` | `fixtures/records/006-quote-two-sided.bin` | Both sides present, with order counts. |
| `quote-one-sided` | `fixtures/records/007-quote-one-sided.bin` | Bid only. The ask has a null price, quantity 0 and count 0; the bid order count is unknown (`UINT32_MAX`). |
| `quote-empty` | `fixtures/records/008-quote-empty.bin` | Both sides absent. Clears the quote. |
| `quote-crossed` | `fixtures/records/009-quote-crossed.bin` | Bid above ask, with the indicative flag set. Valid. |
| `quote-recovery` | `fixtures/records/033-quote-recovery.bin` | The first quote after the `GAP` vectors. Restores the quote state. |
| `quote-two-sided` | `fixtures/golden/records/016-quote-two-sided.bin` | The quote of the conformance file: both sides present. |
