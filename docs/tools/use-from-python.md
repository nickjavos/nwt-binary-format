# Use from Python

`tools/nwt.py` is importable. Put `tools` and `examples/python` on `sys.path`, then import `nwt` for the tool and `nwt_example` for the codec.

| Function | What it does |
|---|---|
| `main(argv)` | Runs a command line, for example `main(["validate", path])`, and returns the exit status |
| `select(reader, types=None, instruments=None, t0=None, t1=None)` | Yields the raw bytes of the matching records in file order, reading only the frames that can hold a match. `instruments` holds IDs or `(low, high)` pairs with both ends included. A record matches when `t0 <= ts_event < t1`. |
| `summaries(reader)` | Returns the `FRAME_SUMMARY` records of a store file as a list of dictionaries of integers, found through `END` and `INDEX`. The list is empty for a file without summaries. |
| `parse_time(text)` | Converts a `TIME` of [Filters](run-it.md#filters) to nanoseconds |

`reader` is an `nwt_example.Reader`. `nwt_example.open_reader(file)` makes one for an open binary file, and `nwt_example.Reader(read_at, size)` makes one for any source that can read n bytes at an offset.

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt_example
import nwt as tool

with open("work/equity-quotes.store.nwt", "rb") as f:
    reader = nwt_example.open_reader(f)
    for summary in tool.summaries(reader):
        print(summary["data_frame_seq"], summary["stored_bytes"], bin(summary["type_mask"]))
    t0 = tool.parse_time("2025-09-16T08:03:00Z")
    t1 = tool.parse_time("2025-09-16T08:04:00Z")
    for raw in tool.select(reader, types=[18], t0=t0, t1=t1):
        record = nwt_example.decode_record(raw)
        print(record["fields"]["sequence"], record["fields"]["price"])
        break
```

```text
0 9605 0b1000000000001000100
1 9221 0b1000000000000000100
2 8735 0b1000000000000000100
3 7493 0b1000000000000000100
734 177290000000
```

[Store profile](../store/how-a-reader-seeks-by-time-and-instrument.md#over-any-byte-source) has a program that reads a store file through a `read_at` function and counts the bytes it fetches.
