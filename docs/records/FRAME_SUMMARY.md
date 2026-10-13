# FRAME_SUMMARY

A `FRAME_SUMMARY` record (type 20, 104 bytes) summarizes one `DATA` frame: its offset, stored size, codec, the record types it contains and its range of instrument IDs. A writer that follows the store profile emits one record per `DATA` frame, so a reader can skip frames by type and instrument without reading them. The manifest declares this type with `required` false, so a reader that does not use summaries skips the records.

## Fields

<!-- nwt-fields: FRAME_SUMMARY -->

## Rules

- A summary record has publisher 0, channel 0, instrument 0 and both timestamps null. Its `sequence` continues the sequence of the system scope (publisher 0, channel 0).
- The schema is declared with `required` false. A reader that does not know record type 20 skips the records, and the container stays valid for it.
- If a container has `FRAME_SUMMARY` records, they fill one or more trailing `DATA` frames that contain nothing else. These are the summary frames.
- Summary frames are `DATA` frames. `INDEX` entries and the counts in `END` include them.
- Together the summary records describe every `DATA` frame that is not a summary frame exactly once, in ascending frame order, with values equal to the real frames.
- A reader finds the summaries from `END` to `INDEX` to the last `DATA` frame. It then walks backward while the first record of a frame has record type 20.
- A validator checks every value against a full scan. A summary that disagrees with the file is an error.
- A reader can skip a frame in three cases: the `type_mask` of the frame lacks the wanted record type, the wanted instrument ID lies outside `[min_instrument_id, max_instrument_id]`, or the time range in `INDEX` does not overlap the query.

[Store profile](../STORE.md) describes files that carry these records, and [State and recovery](../STATE-AND-RECOVERY.md) explains what a selective read can and cannot conclude.

## Example

<!-- nwt-example: 20 -->

## Write and decode

`record 20` writes the `frame-summary` vector (104 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 20 work/type-20-python.bin
python3 examples/python/nwt_example.py decode-record work/type-20-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 20 work/type-20-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-20-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 20 work/type-20-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-20-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 20 work/type-20-cpp.bin
work/nwt-cpp decode-record work/type-20-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `frame-summary` | `fixtures/golden/records/048-frame-summary.bin` | Summary of `DATA` frame 0 of the conformance file: offset 2,272, 480 stored bytes, raw codec, `type_mask` bits 6 and 10 (`INSTRUMENT_DEF` and `VENUE_DEF`), instrument IDs 2001–2002. A standalone vector: `write-golden` does not put it into the conformance file. |
