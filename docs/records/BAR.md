# BAR

A `BAR` record (type 3, 112 bytes) is one completed time bucket built from trades: open, high, low, close, volume and trade count over the half-open interval `[interval_start_ns, interval_end_ns)`. A producer emits it when the interval closes. `ts_event` equals the interval end, so timestamp order can differ from arrival order.

## Fields

<!-- nwt-fields: BAR -->

## Rules

- The interval is half-open, `[start, end)`, with start < end.
- `ts_event` equals `interval_end_ns`.
- A nonempty bar requires non-null open, high, low and close, a positive non-null volume, a positive count, `low` ≤ `open` ≤ `high`, `low` ≤ `close` ≤ `high`, and the empty bit clear.
- An empty bar requires the empty bit, four null prices, zero volume and zero count. An empty bar does not carry prices forward from an earlier bar.
- Each `(publisher, channel, instrument, start, end)` appears at most once in a container.
- A bar that can be revised, and a bar built from auctions or quotes, needs a private schema.
- We recommend describing the aggregation policy in `PROVENANCE`, including the treatment of off-book trades and the cutoff for corrections.

## Example

<!-- nwt-example: 3 -->

## Write and decode

`record 3` writes the `bar-complete` vector (112 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 3 work/type-3-python.bin
python3 examples/python/nwt_example.py decode-record work/type-3-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 3 work/type-3-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-3-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 3 work/type-3-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-3-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 3 work/type-3-cpp.bin
work/nwt-cpp decode-record work/type-3-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `bar-complete` | `fixtures/records/010-bar-complete.bin` | A 60-second bar built from four trades. `ts_event` is the interval end, which is earlier than the `ts_event` of the records before it in the catalog. |
| `bar-empty` | `fixtures/records/011-bar-empty.bin` | Empty flag, four null prices, volume 0 and trade count 0. |
| `bar-complete` | `fixtures/golden/records/017-bar-complete.bin` | The bar of the conformance file: one trade, so open, high, low and close are equal. |
