# inspect

Prints what a container holds: its header, its manifest, every frame and the number of records of each type.

```bash
python3 tools/nwt.py inspect FILE
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |

The output is plain text, one item per line:

| Line starts with | Content |
|---|---|
| `file`, `size` | Path and size in bytes |
| `container` | `major`, `minor`, the stream ID as 32 hexadecimal digits, and the creation time in nanoseconds |
| `dataset`, `producer`, `profile` | Manifest: dataset, producer, profile, clock and `ordering` |
| `publisher` | One line per declared publisher: ID, name and venue |
| `schema` | One line per declared record type: number, schema version, name and `required` |
| `provenance` | `PROVENANCE` object as JSON, when the container has one |
| `frame` | Heading of the frame table. One row per frame follows: `frame_seq`, kind, codec, offset, stored bytes, raw bytes, record count, lowest and highest `ts_event`. A null time prints as `-`. |
| `end` | Totals of `END` and its status, `normal` or `aborted` |
| `records` | One line per record type that occurs: name and count |

The frame table and the lines after it, for the sample [equity-bars.nwt](files/samples/equity-bars.nwt):

```bash
python3 tools/nwt.py inspect fixtures/real-market/equity-bars.nwt | tail -n 7
```

```text
frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns
0 DATA 0 1856 103280 103280 922 1758006306677514564 1758067200000000000
1 INDEX 0 105200 40 40 0 - -
2 END 0 105304 32 32 0 - -
end data_frames=1 records=922 status=normal
records BAR 921
records INSTRUMENT_DEF 1
```
