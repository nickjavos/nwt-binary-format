# TRADE

A `TRADE` record (type 1, 88 bytes) is one trade print: price, quantity, trade identifier, aggressor and conditions. A producer emits it for every execution, and again when the venue corrects or cancels the trade. `NEW` starts a trade, `CORRECT` replaces its price, quantity, aggressor and conditions, and `CANCEL` ends it.

## Fields

<!-- nwt-fields: TRADE -->

## Rules

- `NEW` requires a non-null price, a positive non-null quantity, a nonzero `trade_id` and `original_sequence` = 0.
- A trade ID is unique for the instrument within the publisher and channel scope of a container. If the source has no ID, the producer assigns one deterministically within that scope.
- `CORRECT` carries the complete replacement price, quantity, aggressor and conditions. Its price and quantity follow the rules of `NEW`.
- `CANCEL` requires a null price, a null quantity, aggressor 0 and conditions 0.
- `CANCEL` and `CORRECT` use the `trade_id` of the trade and set `original_sequence` to the sequence of its `NEW` record in the same container, channel and instrument. The `NEW` record precedes them.
- Corrections can repeat. A cancel ends the trade. A correction or a cancel after it is invalid.
- An export that contains a correction also includes the original `NEW` and the lifecycle records between them, even when they lie outside the requested time interval. An export that cannot include them is rejected as unsupported.
- A correction cannot refer to a trade in another container.
- A stateless consumer can expose lifecycle events as they are. An aggregator applies each of them exactly once, in sequence order.
- A price can be negative or zero.
- A trade does not change an order-level book. The matching `MBO` `MODIFY` or `DELETE` from the venue does.

## Example

<!-- nwt-example: 1 -->

## Write and decode

`record 1` writes the `trade-new` vector (88 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 1 work/type-1-python.bin
python3 examples/python/nwt_example.py decode-record work/type-1-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 1 work/type-1-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-1-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 1 work/type-1-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-1-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 1 work/type-1-cpp.bin
work/nwt-cpp decode-record work/type-1-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `trade-new` | `fixtures/records/002-trade-new.bin` | `NEW`: price 123.45, quantity 10, `trade_id` 42, buyer aggressor. |
| `trade-correct` | `fixtures/records/003-trade-correct.bin` | `CORRECT` of trade 42: new price and quantity, seller aggressor, off-book condition. `original_sequence` names the `NEW` record. |
| `trade-cancel` | `fixtures/records/004-trade-cancel.bin` | `CANCEL` of trade 42 after the correction: null price and quantity, aggressor 0, conditions 0. `original_sequence` still names the `NEW` record. |
| `trade-negative-price` | `fixtures/records/005-trade-negative-price.bin` | `NEW` with a negative price (−1.25) and a fractional quantity (0.5), unknown aggressor, and the header flags `REPLAY` and `SUSPECT` set. |
| `trade-new` | `fixtures/golden/records/015-trade-new.bin` | The trade of the conformance file: `NEW`, buyer aggressor. |
