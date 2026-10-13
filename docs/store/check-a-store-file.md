# Check a store file

[validate](../tools/validate.md) reads the whole file and checks the structure, the state rules, the `ordering` declaration and every value of every `FRAME_SUMMARY` record against the frame it describes.

```bash
python3 tools/nwt.py validate work/equity-quotes.store.nwt
```

```text
valid records=2481 data_frames=5 summaries=4 ordering=ts_event
```

[stats](../tools/stats.md) shows how many frames are compressed and what the compression saved:

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

A file that was cut off fails every command with a reason that starts with `incomplete`. A seek needs the `END` frame at the end of the file:

```bash
head -c 30000 work/equity-quotes.store.nwt > work/cut.nwt
python3 tools/nwt.py query work/cut.nwt --type QUOTE
```

```text
NWT error: incomplete: no END frame at the end of the file
```

The command exits with status 1 and prints no record.
