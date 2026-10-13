# repack

Rewrites a container as a store file: the same records in the same order, in new frames, with Zstandard compression, an `INDEX` and `FRAME_SUMMARY` records.

```bash
python3 tools/nwt.py repack FILE OUT [--frame-bytes N] [--level N] [--raw] [--no-summary] [--stream-id HEX] [--created-ns NS]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `OUT` | Store file to write |
| `--frame-bytes N` | Raw bytes per `DATA` frame, from 48 to 16777216. The default is 1048576. |
| `--level N` | Zstandard level, from 1 to 22. The default is 3. |
| `--raw` | Writes every frame raw |
| `--no-summary` | Leaves out the `FRAME_SUMMARY` frames |
| `--stream-id HEX`, `--created-ns NS` | Same as for [extract](extract.md) |

- The output keeps every record and every sequence, and has a new stream ID.
- A frame is stored with Zstandard only when the compressed form is smaller.
- The manifest declares `FRAME_SUMMARY`, so `minor` of the output is 1. It declares an `ordering` when the records have one. The command rejects an input that declares an `ordering` its records do not have.
- `FRAME_SUMMARY` records of the input are replaced by new ones for the new frames.
- Without `libzstd`, the command prints `NWT notice: Zstd library not available; writing raw frames` on standard error and writes raw frames.

```bash
python3 tools/nwt.py repack fixtures/real-market/equity-quotes.nwt work/equity-quotes.store.nwt --frame-bytes 65536
python3 tools/nwt.py validate work/equity-quotes.store.nwt
```

```text
valid records=2481 data_frames=5 summaries=4 ordering=ts_event
```

The input has 2,477 records. The output has four more: one `FRAME_SUMMARY` for each of the four frames that hold the records. [Store profile](../STORE.md) describes the layout and how to choose the settings.
