# extract

Writes the records that match a filter to a new container.

```bash
python3 tools/nwt.py extract FILE OUT [--type TYPES] [--instrument IDS] [--from TIME] [--to TIME] [--stream-id HEX] [--created-ns NS]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `OUT` | Container to write |
| `--type`, `--instrument`, `--from`, `--to` | [Filters](run-it.md#filters) |
| `--stream-id HEX` | Stream ID of the output as 32 hexadecimal digits. The default is random. |
| `--created-ns NS` | Creation time of the output in nanoseconds. The default is the current time. |

- The output has a new stream ID, sequences renumbered from 1, and a manifest that declares only the record types kept.
- The `PROVENANCE` of the input is carried over with three added strings: `derived_by`, `derived_note` and `source_stream_ids`.
- `FRAME_SUMMARY` records are left out: they describe the framing of the input. `repack` writes them for the output.
- When no record matches, the command fails with `no record to write`.

`--stream-id` and `--created-ns` make the output reproducible byte for byte.

```bash
python3 tools/nwt.py extract fixtures/real-market/equity-quotes.nwt work/trade-quotes.nwt --type INSTRUMENT_DEF,TRADE_QUOTE --stream-id 00112233445566778899aabbccddeeff --created-ns 1758020700000000000
python3 tools/nwt.py validate work/trade-quotes.nwt
```

```text
valid records=477 data_frames=1 summaries=0 ordering=ts_event
```

The filter of this example keeps the `INSTRUMENT_DEF` record, so the output passes the state rules. `extract` copies the records that match and no others. Add the definitions to the filter when the output has to stand on its own.
