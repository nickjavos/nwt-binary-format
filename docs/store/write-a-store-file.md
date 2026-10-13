# Write a store file

## With the nwt command

[repack](../tools/repack.md) rewrites any container as a store file.

```bash
mkdir -p work
python3 tools/nwt.py repack fixtures/real-market/equity-quotes.nwt work/equity-quotes.store.nwt --frame-bytes 65536
python3 tools/nwt.py validate work/equity-quotes.store.nwt
```

```text
valid records=2481 data_frames=5 summaries=4 ordering=ts_event
```

The input is the sample [equity-quotes.nwt](files/samples/equity-quotes.nwt), 251,520 bytes with 2,477 records. With the default frame size it fits in one `DATA` frame. `--frame-bytes 65536` gives four frames of records, so the examples on this page have frames to skip.

`repack` works in two passes:

1. It reads the whole input, checks its structure and finds out which `ordering` holds. The manifest carries the declaration, and the manifest is written before the first frame.
2. It writes the header, the metadata, the `DATA` frames, one `FRAME_SUMMARY` record for each of them, the `INDEX` and `END`.

The output has the same records in the same order with the same sequences, and a new stream ID. Its `minor` is 1, because the manifest declares `FRAME_SUMMARY`, type 20, with `required` false. `repack` writes to `OUT.tmp` and renames the file when it is complete.

When `libzstd` is not available, `repack` prints `NWT notice: Zstd library not available; writing raw frames` on standard error and writes raw frames. The rest of the profile stays in place.

## From Python

`tools/nwt.py` is importable. `main` runs any command of the tool and returns its exit status:

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt as tool

status = tool.main(["repack", "fixtures/real-market/equity-quotes.nwt",
                    "work/equity-quotes.store.nwt", "--frame-bytes", "65536"])
```

To write a store file from records you produce yourself, use the classes behind `repack`. `Facts` tracks the record types and the orderings that hold, and `Sink` writes the frames, the summaries, the `INDEX` and `END`. This program writes one instrument definition and 5,000 trades:

```python
import os, sys, time
sys.path[:0] = ["tools", "examples/python"]
import nwt_example as codec
import nwt as tool

start = 1_758_000_000_000_000_000                 # 2025-09-16T05:20:00Z
records = [codec.make_record(
    6, instrument_id=1001, ts_event=start, sequence=1,
    price_increment=10_000_000, quantity_increment=1_000_000_000, contract_multiplier=codec.NULL_I64,
    expiration_ns=codec.NULL, underlying_instrument_id=0, strike=codec.NULL_I64, asset_class=1,
    texts={"symbol": "NWTX", "venue": "XNAS", "currency": "USD", "quantity_unit": "share"},
)]
for i in range(1, 5001):                          # one trade per millisecond
    records.append(codec.make_record(
        1, instrument_id=1001, ts_event=start + i * 1_000_000, sequence=1,
        price=124_250_000_000 + i * 10_000_000, quantity=100_000_000_000, trade_id=i,
        original_sequence=0, action=1, aggressor=0, conditions=0,
    ))
raws = [codec.encode_record(r) for r in records]

facts = tool.Facts()                              # record types present and the orderings that hold
for raw in raws:
    facts.add(raw)
ordering = facts.ordering()
manifest = codec.build_manifest(
    "EXAMPLE.STORE", "my-writer/1", [{"id": 1, "name": "Example Feed", "venue": "XNAS"}],
    types=facts.types | {20}, ordering=None if ordering == "none" else ordering,
)
identity = dict(stream_id=os.urandom(16), created_ns=time.time_ns())
level = 3 if codec.zstd_available() else None     # None writes raw frames

with tool.atomic("work/trades.store.nwt") as out:
    sink = tool.Sink(out, manifest, None, identity, renumber=True,
                     frame_bytes=65536, level=level, summaries=True)
    for raw in raws:
        sink.add(raw)
    sink.finish()
```

`renumber=True` makes the sink assign the sequences, so the value passed to `make_record` is a placeholder. Type 20 in `types` declares `FRAME_SUMMARY` in the manifest. Check the result:

```bash
python3 tools/nwt.py validate work/trades.store.nwt
```

```text
valid records=5008 data_frames=8 summaries=7 ordering=ts_event
```
