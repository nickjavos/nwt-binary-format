# stats

Prints the size of every part of a container and the bytes of each record type.

```bash
python3 tools/nwt.py stats FILE
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |

The output is plain text, one item per line:

| Line | Content |
|---|---|
| `file_bytes` | Size of the file |
| `header_and_metadata_bytes` | 64-byte header plus the metadata |
| `data_frames` | Number of `DATA` frames, how many of them are Zstandard, and their stored and raw payload bytes |
| `compression_ratio` | Raw payload bytes divided by stored payload bytes of the `DATA` frames, with three decimals; `-` when the file has no data |
| `index_bytes`, `end_bytes` | Size of the `INDEX` frames and of the `END` frame, headers included |
| `records` | Number of records |
| `type` | One line per record type: number, name, record count and record bytes |

The store file written in [repack](repack.md):

```bash
python3 tools/nwt.py stats work/equity-quotes.store.nwt
```

```text
file_bytes 37968
header_and_metadata_bytes 2120
data_frames 5 zstd_frames=5 stored_bytes=35156 raw_bytes=249664
compression_ratio 7.101  (raw payload bytes / stored payload bytes, DATA frames)
index_bytes 264
end_bytes 96
records 2481
type 2 QUOTE records=2000 record_bytes=192000
type 6 INSTRUMENT_DEF records=1 record_bytes=128
type 18 TRADE_QUOTE records=476 record_bytes=57120
type 20 FRAME_SUMMARY records=4 record_bytes=416
```

The stored bytes depend on the version of the Zstandard library.
