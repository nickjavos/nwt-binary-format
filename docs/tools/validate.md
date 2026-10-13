# validate

Checks a container completely and reports the first rule it breaks.

```bash
python3 tools/nwt.py validate FILE
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to check |

`validate` runs these checks and stops at the first one that fails:

1. The structure: header, metadata and every frame, with all CRC-32C values, lengths, sequences, declared record types and publishers, frame time bounds, the `INDEX` entries and the totals of `END`.
2. The manifest: `BOOK_DELTA` is declared with `required` true, `FRAME_SUMMARY` with `required` false, and record types 10–19 appear only under the profile `market-data`.
3. Every record against the state rules of `examples/python/market_state.py`: definitions before market data, trade lifecycles, order-level and aggregate books, statistics, symbol intervals and the other rules of [State and recovery](../STATE-AND-RECOVERY.md).
4. The end of the container: the status of `END` is normal, and no snapshot is open.
5. The `ordering` declaration of the manifest against the records.
6. When the container has `FRAME_SUMMARY` records: they fill the last `DATA` frames, there is one for every other `DATA` frame, and every value equals the value computed from the frame.

On success it prints one line and exits with status 0:

```bash
python3 tools/nwt.py validate fixtures/real-reference/corporate-actions-us.nwt
```

```text
valid records=1641 data_frames=1 summaries=0 ordering=none
```

On the first broken rule it prints the reason and exits with status 1. A reason from the state rules names the record. The file in this example holds order records without the definition of their instrument:

```bash
python3 tools/nwt.py extract fixtures/real-market/equity-orders.nwt work/orders-only.nwt --type MBO
python3 tools/nwt.py validate work/orders-only.nwt
```

```text
NWT error: record 1 (MBO, sequence 1): definition must precede data
```
