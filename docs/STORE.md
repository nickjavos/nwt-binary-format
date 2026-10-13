# The NWT store

A store file is not a new format. It is an ordinary NWT container written with a few settings that make it fast to search: big frames, Zstd compression, an INDEX, a summary of every frame, and an honest statement of its time order. Every NWT reader can read it. A reader that knows the store layout can answer a time, type or instrument query by reading only the frames that can contain an answer.

All commands run from the kit root (quote the path: the kit lives in a folder whose name ends in a space). They use the real files in `fixtures/real-reference/` and `fixtures/real-market/`.

## What makes a container a store file

| Choice | Store setting | Why |
|---|---|---|
| Frame size | 1 MiB of raw payload by default; up to the 16 MiB limit | Fewer headers, better compression, fewer reads |
| Codec | Zstd (level 3), raw for any frame that does not shrink | Smaller file, faster reads from slow storage |
| INDEX | Always written | One entry per DATA frame: offset, first and last `ts_event`, size, count |
| FRAME_SUMMARY | Always written | Per frame: record types present, lowest and highest instrument ID, stored size, codec, flags |
| `ordering` | Declared in the manifest when it is true | Tells a reader the time bounds of frames are monotone |

Records are never reordered. Byte order is the delivery order, and definitions, snapshots and trade corrections depend on it. `repack` re-frames and recompresses; it does not sort.

## Making one

```sh
mkdir -p work
python3 tools/nwt.py repack fixtures/real-reference/corporate-actions-us.nwt work/corporate-actions-us.store.nwt --frame-bytes 65536
```

`--frame-bytes 65536` is used here only because this file is under one megabyte; with the default 1 MiB it would be a single frame and there would be nothing to skip. Real market data files, which are larger, can use the default:

```sh
python3 tools/nwt.py repack fixtures/real-market/equity-orders.nwt work/equity-orders.store.nwt
```

`repack` reads the input twice. The first pass checks it completely and finds out which orderings are true (the manifest has to say so before the first frame is written). The second pass writes the frames. It writes the file to a temporary name and renames it when done. The output has a new stream ID, the input's sequences, and `minor` 1 (the manifest now declares FRAME_SUMMARY, type 20, with `required` false). `--raw` skips compression, `--no-summary` leaves out the summaries, `--level` sets the Zstd level. Without `libzstd`, a notice is printed and frames are raw.

## File layout

```
container header + metadata (manifest, provenance)
DATA frame 0 ... DATA frame n-1       the records, in original order
DATA frames (summaries only)          FRAME_SUMMARY records, one per frame above
INDEX frame(s)                        one 40-byte entry per DATA frame
END frame                             96 bytes; points at the first INDEX frame
```

The summary frames are DATA frames that hold FRAME_SUMMARY records and nothing else. Together they describe every other DATA frame exactly once, in ascending frame order. A 1.0 reader treats FRAME_SUMMARY as an optional type it may skip, so a store file is still a valid file for it. The summary frames' own entries in the INDEX have null time bounds.

A FRAME_SUMMARY record (type 20, 104 bytes, publisher 0, channel 0, instrument 0, null timestamps) holds:

| Field | Meaning |
|---|---|
| `data_frame_seq`, `data_frame_offset` | Which frame, and where it starts, from byte 0 of the container |
| `stored_bytes`, `codec` | Size on disk and codec of that frame (the INDEX does not carry these) |
| `type_mask` | Bit n (1 to 63) set when type n occurs in the frame; bit 0 set when any other type occurs |
| `min_instrument_id`, `max_instrument_id` | Over non-zero instrument IDs; both 0 when the frame has none |
| `summary_flags` | Bit 0: some `ts_event` in the frame is null. Bit 1: the non-null `ts_event` values are non-decreasing in the frame (true when there are none or one) |

`validate` computes all of these from the real frames and fails if a single value disagrees.

## Reading one

`query`, `resolve` and `select` all use the same path. A reader that only has `read_at(offset, n)` does this:

1. Read the last 96 bytes: the END frame. It gives the offset of the first INDEX frame and the number of DATA frames.
2. Read the INDEX frames (everything between that offset and END). Each 40-byte entry gives a DATA frame's offset, `min_event_ns`, `max_event_ns`, raw size and record count.
3. Walk back from the last DATA frame while the frame looks like a summary frame (104-byte records, null time bounds, only type 20). Read those frames. The records are the summaries.
4. Keep a frame only if it can contain a match:
   - **Time.** With `--from` or `--to`, a frame is kept when its `[min, max]` can overlap `[from, to)`. A frame whose bounds are null holds only records without a `ts_event`, and a null time never matches a time bound, so it is skipped.
   - **Type.** The frame's `type_mask` must share a bit with the requested types. Types outside 1 to 63 use bit 0.
   - **Instrument.** The requested IDs must overlap the frame's `[min, max]`. The summary says nothing about instrument 0, so a request that includes 0 is never skipped on this test.
5. Read each kept frame (header, payload, CRC), split it into records, and apply the filter record by record.

Without FRAME_SUMMARY records, steps 3 and the type and instrument tests are skipped and only time prunes frames. Without an INDEX, nothing can be pruned and the reader falls back to a full scan (`query` refuses such a file; use `cat` or `extract`).

The result equals a full scan filtered the same way. Frames are read in file order and records come out in file order.

### Seeking is partial

Reading in the middle of a file means the instrument definitions, snapshots and trade history before that point were not read. Specification section 11 says such results must be labelled raw or partial and must not be presented as a reconstructed book. `query` writes this line on stderr before any record:

```
# partial: earlier definitions and book state are not included
```

To get a usable slice, also fetch the definitions (`--type INSTRUMENT_DEF` first) or use `extract`, which reads the whole file and writes a new container.

### Time order and binary search

INDEX time ranges may overlap and go backward unless something says otherwise (specification section 11), so a reader must look at every entry. A container that declares `"ordering": "ts_event"` makes the claim that all non-null `ts_event` values are non-decreasing in byte order across the container (records with a null time are exempt). Then the entries are monotone and a binary search by time is valid. `repack` declares the claim only when it is true and `validate` checks any claim it finds. The `nwt` tool still scans the entries in order, since all of them are already in memory after step 2; the declaration matters to readers that want to avoid even reading the whole INDEX.

`"instrument,ts_event"` means the records are ordered by instrument and then by time, and the same rules about null times apply.

## From a program, over any byte source

`nwt_example.Reader` takes a `read_at(offset, n)` function instead of a file, so the same code runs on a local file, on a memory-mapped file or on HTTP range requests. No HTTP client is included. This program stands in for a remote object with a byte string and counts what the reader asks for:

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt_example
import nwt as tool

path = "work/corporate-actions-us.store.nwt"
data = open(path, "rb").read()          # stands in for a remote object
fetched = []

def read_at(offset, n):                 # replace with an HTTP Range request
    fetched.append(n)
    return data[offset : offset + n]

reader = nwt_example.Reader(read_at, len(data))
found = list(tool.select(reader, types=[22], instruments=[17103508]))
print(len(found), "records;", sum(fetched), "of", len(data), "bytes asked for in", len(fetched), "reads")
```

`tool.summaries(reader)` returns the FRAME_SUMMARY records as dicts, found through END and INDEX alone. Run the program on the file made above: the number it prints for bytes asked for is the evidence of how much of the file the query touched; it depends on the data and the frame size.

## Choosing settings

- **Frame size.** Bigger frames compress better and cost fewer reads; a query pays for a whole frame even when one record matches. 1 MiB is the default. Frames can be up to 16 MiB. A record larger than the limit gets a frame of its own.
- **Zstd.** Only DATA frames are compressed, and only when the compressed form is strictly smaller. INDEX and END are always raw so a reader can find them without a codec. The compressed bytes depend on the library version, so compare decoded records, not compressed files.
- **When not to use a store file.** A live feed. The INDEX, the summaries and the `ordering` claim can only be written once the file is complete. Stream containers while they are live and `repack` them when they are closed.

## Checking a store file

```sh
python3 tools/nwt.py validate work/corporate-actions-us.store.nwt
python3 tools/nwt.py inspect work/corporate-actions-us.store.nwt
python3 tools/nwt.py stats work/corporate-actions-us.store.nwt
```

`validate` ends with `valid records=... data_frames=... summaries=... ordering=...`. `inspect` shows the summary frames as DATA frames with `-` for both times and the FRAME_SUMMARY count in the record table. `stats` shows how many frames are Zstd and the compression ratio.

A file cut off anywhere, including a store file whose END was lost, fails every one of these with a message containing `incomplete`:

```sh
head -c 100000 work/corporate-actions-us.store.nwt > work/cut.nwt
python3 tools/nwt.py query work/cut.nwt --type CORPORATE_ACTION
```

This exits 1, prints `NWT error: incomplete: ...` on stderr, and prints no records.
