# GAP

A `GAP` record (type 8, 80 bytes) reports a discontinuity in the source feed, not a missing NWT frame. A producer emits it when source messages were lost or may have been lost. It applies to every instrument of its publisher and channel and invalidates all book and status state there.

## Fields

<!-- nwt-fields: GAP -->

## Rules

- The publisher is nonzero and the instrument is 0.
- Both bounds are null when they are unknown. Otherwise both are non-null with first ≤ last.
- The bounds are advisory values in the sequence space of the source. They are not NWT output sequences.
- A source whose sequence space does not fit, or whose loss is not one interval, uses null bounds.
- `recovery_id` correlates diagnostics. It is not a snapshot identifier.
- `GAP` invalidates all book state and trading-status state in its scope, including the aggregate book that `BOOK_DELTA` maintains.
- A valid `QUOTE`, a `BOOK_SNAPSHOT`, an `MBO` snapshot or `CLEAR`, and a `STATUS` each restore their own state independently.
- The completeness of trades and bars stays uncertain for the affected interval, even after a book has recovered.
- The source sequence bounds are inclusive.
- `recovery_id` is nonzero and unique among the `GAP` records of the container.

[State and recovery](../STATE-AND-RECOVERY.md) describes recovery after a `GAP`.

## Example

<!-- nwt-example: 8 -->

## Write and decode

`record 8` writes the `gap-1` vector (80 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 8 work/type-8-python.bin
python3 examples/python/nwt_example.py decode-record work/type-8-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 8 work/type-8-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-8-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 8 work/type-8-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-8-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 8 work/type-8-cpp.bin
work/nwt-cpp decode-record work/type-8-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `gap-1` | `fixtures/records/029-gap-1.bin` | `reason` 1, source packet loss, with the known bounds 100–105. |
| `gap-2` | `fixtures/records/030-gap-2.bin` | `reason` 2, source reset. Both bounds are null. |
| `gap-3` | `fixtures/records/031-gap-3.bin` | `reason` 3, producer overflow. Both bounds are null. |
| `gap-4` | `fixtures/records/032-gap-4.bin` | `reason` 4, unknown discontinuity. Both bounds are null. |
| `gap` | `fixtures/golden/records/041-gap.bin` | The `GAP` of the conformance file: source packet loss, bounds 500–509. |
