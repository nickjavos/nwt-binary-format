# Record header

Every record starts with the same 48-byte header, whatever its record type. The header gives the length and the type of the record, its publisher, channel and instrument, two timestamps and a sequence number. The body of the record follows at offset 48.

![A record is a 48-byte header, the fixed fields of its record type, an optional variable part and zero padding; TRADE, BOOK_SNAPSHOT and INSTRUMENT_DEF show the three shapes](../diagrams/record-anatomy.svg "A record: the common header, the fixed fields, the variable part and the padding")

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `record_bytes` | u32 | 4 | Size of the record, including this header and the padding |
| 4 | `record_type` | u16 | 2 | Record type. Selects the body layout |
| 6 | `schema_version` | u8 | 1 | Schema version. 1 for every standard schema |
| 7 | `flags` | u8 | 1 | Bit 0 `REPLAY`, bit 1 `SUSPECT`; bits 2–7 are zero |
| 8 | `publisher_id` | u32 | 4 | Publisher declared in the manifest, or 0 for the system scope |
| 12 | `channel_id` | u32 | 4 | Logical partition defined by the producer. 0 is valid |
| 16 | `instrument_id` | u64 | 8 | Instrument in the namespace of the publisher, or 0 |
| 24 | `ts_event` | u64 | 8 | Source event time, or null |
| 32 | `ts_recv` | u64 | 8 | Capture time at the producer, or null |
| 40 | `sequence` | u64 | 8 | Output position within the publisher and channel |

**Length.**

- `record_bytes` is a multiple of 8, at least 48 and at most 1,048,576.
- A fixed-size standard schema requires its exact length. A variable-size standard schema requires the exact computed padded length.
- A record carries no additional trailing fields under an existing schema version.

**Flags.**

- `REPLAY`: the producer marks the record as historical or replayed. It does not alter the sequence or the identity of the record.
- `SUSPECT`: the producer knows of a quality problem at the source. It does not excuse a malformed record.
- A retransmission of a container preserves all bytes, including flags.

**Sequence.**

- `sequence` is the output position within `(stream_id, publisher_id, channel_id)`. It begins at 1 and increases by exactly 1 for each record in that scope, across instruments and record types. Zero is invalid.
- A new container restarts the sequences.
- The maximum value can be used once. Another record in that scope needs a new container.
- A channel is a logical partition defined by the producer. It need not be an exchange channel.
- `sequence` is an output sequence, not the sequence number of an exchange. Gaps at the source are reported by [`GAP`](../records/GAP.md) records.
- Filtering, merging and re-batching into a different container assign new output sequences. A consumer cannot read a missing sequence in a filtered export as a gap in the source feed.
