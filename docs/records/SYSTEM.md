# SYSTEM

A `SYSTEM` record (type 9, 64 bytes plus text) is a heartbeat or a diagnostic message with UTF-8 text of up to 4,096 bytes. A producer emits heartbeats on a quiet stream and info, warning and error messages for operators. Diagnostics never trigger commands or state repair.

## Fields

<!-- nwt-fields: SYSTEM -->

## Rules

- The instrument is 0.
- Publisher 0 requires channel 0 and means the scope of the container. A nonzero publisher means the scope of that declared publisher and channel.
- Heartbeat and info require severity 0. Warning requires severity 1. Error requires severity 2.
- A heartbeat requires an empty text and `related_recovery_id` = 0.
- Diagnostics are descriptive. They cannot trigger automatic commands, state repair or schema changes.
- A `SYSTEM` error does not end a container. The `END` frame reports termination.
- `related_recovery_id` is 0 or the `recovery_id` of an earlier `GAP`.

## Example

<!-- nwt-example: 9 -->

## Write and decode

`record 9` writes the `system-1` vector (64 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 9 work/type-9-python.bin
python3 examples/python/nwt_example.py decode-record work/type-9-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 9 work/type-9-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-9-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 9 work/type-9-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-9-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 9 work/type-9-cpp.bin
work/nwt-cpp decode-record work/type-9-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `system-1` | `fixtures/records/039-system-1.bin` | Heartbeat: no text, `related_recovery_id` 0. |
| `system-2` | `fixtures/records/040-system-2.bin` | Info message that refers to the `GAP` with `recovery_id` 4. Its text mixes ASCII, accented Latin and CJK characters, so its byte length differs from its character count. |
| `system-3` | `fixtures/records/041-system-3.bin` | Warning, `severity` 1, with the same text. |
| `system-4` | `fixtures/records/042-system-4.bin` | Error, `severity` 2, with the same text. |
| `system-heartbeat` | `fixtures/golden/records/042-system-heartbeat.bin` | The heartbeat of the conformance file, sent with publisher 0. |
