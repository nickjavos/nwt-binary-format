# BOOK_DELTA

A `BOOK_DELTA` record (type 15, 72 bytes) changes one price level of the aggregate book that `BOOK_SNAPSHOT` replaces. A producer emits it for incremental depth updates between snapshots. Levels are keyed by price, not by rank. The manifest declares this type with `required` true.

## Fields

<!-- nwt-fields: BOOK_DELTA -->

## Rules

- `SET` requires a non-null price and a quantity from 1 through `UINT64_MAX` − 1. It adds the level or replaces its size and count.
- `DELETE` requires a non-null price, quantity 0 and a null count. It applies to an existing level, unless the book is depth-limited.
- `CLEAR` requires a null price, quantity 0 and a null count. It empties one side, or the whole book when `side` is 0.
- The book is valid after a `BOOK_SNAPSHOT` or after a `CLEAR` with `side` 0. A delta against an invalid book is a semantic error. `GAP` invalidates the book.
- A depth-limited snapshot leaves the book depth-limited until the next snapshot that is not depth-limited.
- `LAST_IN_EVENT` marks the last delta of one source event.
- A producer never grows a side beyond 1,024 levels, so that the state can always be sent again as one `BOOK_SNAPSHOT`.
- A book that is crossed for a moment is not an encoding error.

[State and recovery](../STATE-AND-RECOVERY.md) describes the aggregate book with deltas.

## Example

<!-- nwt-example: 15 -->

## Write and decode

`record 15` writes the `delta-set-bid` vector (72 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 15 work/type-15-python.bin
python3 examples/python/nwt_example.py decode-record work/type-15-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 15 work/type-15-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-15-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 15 work/type-15-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-15-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 15 work/type-15-cpp.bin
work/nwt-cpp decode-record work/type-15-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `delta-set-bid` | `fixtures/golden/records/020-delta-set-bid.bin` | `SET` of a new bid level with order count 1. The first of two deltas of one source event. |
| `delta-set-ask-last` | `fixtures/golden/records/021-delta-set-ask-last.bin` | `SET` that replaces an ask level, with an unknown order count and `LAST_IN_EVENT` set. It has the same `ts_event` as `delta-set-bid`. |
| `delta-delete` | `fixtures/golden/records/022-delta-delete.bin` | `DELETE` of the bid level at 149.23: quantity 0, order count `UINT32_MAX`. |
| `delta-clear-side` | `fixtures/golden/records/023-delta-clear-side.bin` | `CLEAR` of the ask side, with a null price. |
| `delta-clear-all` | `fixtures/golden/records/024-delta-clear-all.bin` | `CLEAR` with `side` 0: empties the whole book and leaves it valid. |
