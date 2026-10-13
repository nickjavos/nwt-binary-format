# File layout

| Part | Content |
|---|---|
| Container header and metadata | The 64-byte header, the `MANIFEST` and, when the source had one, the `PROVENANCE` |
| `DATA` frames with records | The records, in their original order |
| Summary frames | `DATA` frames that hold `FRAME_SUMMARY` records and nothing else: one record for each frame above, in ascending frame order |
| `INDEX` frames | One 40-byte entry per `DATA` frame, summary frames included |
| `END` frame | 96 bytes at the end of the file: the offset of the first `INDEX` frame and the totals |

The frame table of [inspect](../tools/inspect.md) shows the layout of the file written above:

```bash
python3 tools/nwt.py inspect work/equity-quotes.store.nwt | tail -n 13
```

```text
frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns
0 DATA 1 2120 9605 65480 652 1758006306677514564 1758009758289670910
1 DATA 1 11792 9221 65520 652 1758009758289672303 1758009809048757997
2 DATA 1 21080 8735 65496 647 1758009809049258043 1758009844980010260
3 DATA 1 29880 7493 52752 526 1758009844980046859 1758009883915993953
4 DATA 1 37440 102 416 4 - -
5 INDEX 0 37608 200 200 0 - -
6 END 0 37872 32 32 0 - -
end data_frames=5 records=2481 status=normal
records QUOTE 2000
records INSTRUMENT_DEF 1
records TRADE_QUOTE 476
records FRAME_SUMMARY 4
```

Frames 0–3 hold the records. Frame 4 is the summary frame: 4 records of 104 bytes, with `-` for both time bounds because a `FRAME_SUMMARY` has no event time. Codec 1 is Zstandard. The stored sizes and the offsets after frame 0 depend on the version of the Zstandard library.

A `FRAME_SUMMARY` record is 104 bytes. Its publisher, channel and instrument are 0, and both timestamps are null.

| Field | Meaning |
|---|---|
| `data_frame_seq` | `frame_seq` of the frame it describes |
| `data_frame_offset` | Offset of that frame from byte 0 of the container |
| `stored_bytes` | Payload size of that frame as stored, after compression |
| `codec` | 0 raw, 1 Zstandard |
| `type_mask` | Bit n, for n from 1 to 63, is set when record type n occurs in the frame. Bit 0 is set when any other type occurs. |
| `min_instrument_id`, `max_instrument_id` | Lowest and highest non-zero instrument ID in the frame. Both are 0 when the frame has none. |
| `summary_flags` | Bit 0: some `ts_event` in the frame is null. Bit 1: the non-null `ts_event` values do not decrease within the frame. |

The first summary of the file describes frame 0:

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type FRAME_SUMMARY 2> /dev/null | head -n 1
```

```text
{"type_name":"FRAME_SUMMARY","record_bytes":"104","record_type":"20","schema_version":"1","flags":"0","publisher_id":"0","channel_id":"0","instrument_id":"0","ts_event":"18446744073709551615","ts_recv":"18446744073709551615","sequence":"1","data_frame_seq":"0","data_frame_offset":"2120","stored_bytes":"9605","codec":"1","summary_flags":"2","type_mask":"262212","min_instrument_id":"11667","max_instrument_id":"11667"}
```

`type_mask` 262212 is 2¹⁸ + 2⁶ + 2²: the frame holds `TRADE_QUOTE`, `INSTRUMENT_DEF` and `QUOTE` records. The masks of frames 1–3 are 262148, without the bit of `INSTRUMENT_DEF`. The Specification defines the record in [FRAME_SUMMARY](../records/FRAME_SUMMARY.md).
