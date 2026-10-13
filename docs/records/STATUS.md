# STATUS

A `STATUS` record (type 7, 64 bytes) is the trading status of one instrument on one channel, with a reason. A producer emits it when the venue changes the trading state, and each record replaces the previous status. It does not clear books and does not forbid trades during a halt or an auction.

## Fields

<!-- nwt-fields: STATUS -->

## Rules

- `STATUS` does not clear books.
- It does not prohibit trades during an auction or a halt. Reported data and administrative state may not be perfectly synchronized.
- A `GAP` invalidates status. A new `STATUS` record restores it.

## Example

<!-- nwt-example: 7 -->

## Write and decode

`record 7` writes the `status-0` vector (64 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 7 work/type-7-python.bin
python3 examples/python/nwt_example.py decode-record work/type-7-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 7 work/type-7-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-7-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 7 work/type-7-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-7-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 7 work/type-7-cpp.bin
work/nwt-cpp decode-record work/type-7-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `status-0` | `fixtures/records/023-status-0.bin` | `status` 0 (unknown), `reason` 0 (unspecified). |
| `status-1` | `fixtures/records/024-status-1.bin` | `status` 1 (pre-open), `reason` 1 (scheduled). |
| `status-2` | `fixtures/records/025-status-2.bin` | `status` 2 (open), `reason` 2 (volatility). |
| `status-3` | `fixtures/records/026-status-3.bin` | `status` 3 (halted), `reason` 3 (regulatory). |
| `status-4` | `fixtures/records/027-status-4.bin` | `status` 4 (closed), `reason` 4 (technical). |
| `status-5` | `fixtures/records/028-status-5.bin` | `status` 5 (auction), `reason` 0 (unspecified). |
| `status-recovery` | `fixtures/records/038-status-recovery.bin` | The status sent after the `GAP` vectors: open, reason technical. Restores the status state. |
| `status-open` | `fixtures/golden/records/018-status-open.bin` | The status of the conformance file: open, reason scheduled. |
