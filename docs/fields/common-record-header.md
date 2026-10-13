# Common record header

Every record starts with these 48 bytes. The offsets in the tables of the record types continue from 48.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `record_bytes` | `u32` | 4 | Size of the whole record in bytes, from the first byte of this header through the final padding. A multiple of 8, from 48 to 1,048,576. The encoder computes it. |
| 4 | `record_type` | `u16` | 2 | Record type, 1 to 22 for the standard record types. Selects the layout of the fields after this header. |
| 6 | `schema_version` | `u8` | 1 | 1 for every standard record type. Another value is another wire layout. |
| 7 | `flags` | `u8` | 1 | Bit 0 is `REPLAY`, bit 1 is `SUSPECT`. Bits 2–7 are zero. |
| 8 | `publisher_id` | `u32` | 4 | Publisher, as declared in the manifest. Nonzero for types 1–8, 10–19, 21 and 22. `SYSTEM` can use 0 together with channel 0. `FRAME_SUMMARY` always uses 0. |
| 12 | `channel_id` | `u32` | 4 | Logical partition chosen by the producer. 0 is valid. |
| 16 | `instrument_id` | `u64` | 8 | Opaque instrument identifier, scoped by dataset and publisher. Nonzero for types 1–7, 11–19, 21 and 22. Zero for `GAP`, `SYSTEM`, `VENUE_DEF` and `FRAME_SUMMARY`. |
| 24 | `ts_event` | `u64` | 8 | Event time at the source, in nanoseconds since the Unix epoch. `UINT64_MAX` when it is unavailable. For a `BAR` it is the end of the interval. |
| 32 | `ts_recv` | `u64` | 8 | Capture time at the producer, in nanoseconds since the Unix epoch. `UINT64_MAX` when it is unavailable. |
| 40 | `sequence` | `u64` | 8 | Position of the record in the output of one container, publisher and channel. Starts at 1, increases by 1, never wraps. |

Four points apply to the header:

- `record_type` is not a message code of the source exchange, and `sequence` is not an exchange sequence number. A `GAP` record reports a loss at the source.
- `REPLAY` marks a record that the producer identifies as historical or replayed. `SUSPECT` marks a record with a known quality problem at the source. Neither flag changes the layout or relaxes validation.
- Sequence continuity is checked separately for each pair of publisher and channel.
- `ts_event` can move backward from one record to the next, and `ts_recv` is not necessarily later than `ts_event`.

The fields of each record type that follow this header are listed on the pages of [Record types](../records/INDEX.md).
