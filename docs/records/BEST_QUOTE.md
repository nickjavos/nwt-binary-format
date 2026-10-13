# BEST_QUOTE

A `BEST_QUOTE` record (type 19, 112 bytes) is the best bid and offer across venues, with the venue that set each side. The producer of a consolidated feed emits it on every change, or once per sampling interval. It keeps its own state and does not replace `QUOTE` state.

## Fields

<!-- nwt-fields: BEST_QUOTE -->

## Rules

- The presence rules match [`QUOTE`](QUOTE.md).
- A nonzero `bid_publisher_id` or `ask_publisher_id` is a declared publisher.
- `interval_ns` is a duration, not a timestamp. When it is greater than 0, the record is a sample taken at the end of the interval, and `ts_event` equals the end of the interval.
- `BEST_QUOTE` keeps its own state. It does not replace `QUOTE` state.
- A `GAP` invalidates this state; the next `BEST_QUOTE` restores it.

## Example

<!-- nwt-example: 19 -->

## Write and decode

`record 19` writes the `best-quote-event` vector (112 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 19 work/type-19-python.bin
python3 examples/python/nwt_example.py decode-record work/type-19-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 19 work/type-19-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-19-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 19 work/type-19-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-19-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 19 work/type-19-cpp.bin
work/nwt-cpp decode-record work/type-19-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `best-quote-event` | `fixtures/golden/records/039-best-quote-event.bin` | Event-driven quote (`interval_ns` 0) with a different venue on each side. |
| `best-quote-sampled` | `fixtures/golden/records/040-best-quote-sampled.bin` | Quote sampled once per second: `ts_event` at the interval end, an absent ask with `ask_publisher_id` 0, and the indicative flag. |
