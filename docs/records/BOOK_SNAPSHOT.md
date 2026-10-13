# BOOK_SNAPSHOT

A `BOOK_SNAPSHOT` record (type 5, 56 bytes plus 48 bytes per level) replaces a ranked aggregate book atomically, with up to 1,024 levels per side. The replacement fits in one record. A producer emits it to publish the whole depth: on every update of a depth-snapshot source, at the start of a stream, and to restore the book after a `GAP`. Level `i` pairs the bid at rank `i` with the ask at rank `i`.

## Fields

<!-- nwt-fields: BOOK_SNAPSHOT -->

## Rules

- The presence rules of each side match [`QUOTE`](QUOTE.md).
- Bid prices are strictly decreasing and ask prices strictly increasing. A duplicate price level is invalid.
- One side can have fewer levels than the other. The absent elements of a side form a suffix on that side.
- The last element has at least one present side, unless `levels` = 0.
- `levels` = 0 is an empty observed book.
- The depth-limited flag means deeper prices may exist beyond the reported ranks. A consumer cannot infer a full exchange book from it. A snapshot with zero levels can also be depth-limited when the producer cannot attest that the book is complete.
- The record initializes or replaces aggregate state only. It cannot rebuild individual orders or repair `MBO` state.
- `to-csv` rejects this type, because the number of levels varies from record to record. Use `to-json`.

## Example

<!-- nwt-example: 5 -->

## Write and decode

`record 5` writes the `book-two-levels` vector (152 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 5 work/type-5-python.bin
python3 examples/python/nwt_example.py decode-record work/type-5-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 5 work/type-5-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-5-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 5 work/type-5-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-5-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 5 work/type-5-cpp.bin
work/nwt-cpp decode-record work/type-5-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `book-two-levels` | `fixtures/records/020-book-two-levels.bin` | Two levels. The second has a bid only, so the absent ask forms the suffix of its side. |
| `book-empty` | `fixtures/records/021-book-empty.bin` | Zero levels: a valid empty book. |
| `book-depth-limited` | `fixtures/records/022-book-depth-limited.bin` | One level with the depth-limited flag. |
| `book-recovery` | `fixtures/records/034-book-recovery.bin` | The snapshot sent after the `GAP` vectors. Restores the aggregate book. |
| `book-snapshot` | `fixtures/golden/records/019-book-snapshot.bin` | The snapshot of the conformance file: two full levels. The `BOOK_DELTA` vectors change this book. |
