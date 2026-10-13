# File structure

A container is one byte sequence: a container header, metadata, a series of frames, and one `END` frame that closes it. `DATA` frames carry the records. The layout is the same for a file and for a live stream.

![A container from byte 0 to the end: the container header, the metadata, DATA frames, optional INDEX frames and the END frame, each with its offset and size](../diagrams/file-structure.svg "The parts of a container, with their offsets and sizes")

```text
Container
  container header     64 bytes
  metadata             TLV elements, each padded to 8 bytes
  DATA frame 0
  DATA frame 1
  ...
  INDEX frames         optional, contiguous
  END frame            96 bytes

DATA frame
  frame header         64 bytes
  stored payload       raw records, or one Zstandard frame
  zero padding         to an 8-byte boundary

Raw DATA payload
  record               48-byte record header, body, zero padding
  record
  ...
```

| Part | Bytes | Content |
|---|---|---|
| [Container header](container-header.md) | 64 | Magic, version, metadata size, stream identifier, checksums |
| [Metadata](metadata.md) | 8 to 1,048,576 | `MANIFEST` and the optional `PROVENANCE` |
| [`DATA` frames](frames.md#data-frames) | 64 + align8(`stored_bytes`) each | Records |
| [`INDEX` frames](frames.md#index-frames) | 64 + align8(`stored_bytes`) each | Optional. One 40-byte entry for each `DATA` frame |
| [`END` frame](frames.md#end-frame) | 96 | Totals, completion status and the offset of the first `INDEX` frame |

## Terms

- **Container.** One complete NWT byte sequence, from the container header to the `END` frame. One file or one stream holds one container.
- **Metadata.** The TLV elements between the container header and the first frame.
- **Manifest.** The content of the `MANIFEST` element: the dataset, the publishers and the schemas of the container.
- **Frame.** A checksummed unit of the container. Its kind is `DATA`, `INDEX` or `END`. A frame kind is not a record type.
- **Record.** One message of one record type inside a `DATA` frame.
- **Schema.** A record type together with a schema version: one wire layout and its rules. A feed type of a data source maps to a record type.
- **Writer** and **reader.** The implementations that encode and decode a container.
- **Producer** and **consumer.** The systems that own them. The producer decides what the writer emits and owns the identifier namespaces. The consumer applies the decoded records.

## Structural rules

- The container has no global compression wrapper. Each `DATA` frame is decodable on its own after the metadata is known.
- A record never crosses a frame boundary.
- Metadata is immutable for a container. Instrument definitions that change over time are records.
- Every schema and every publisher is declared in the metadata before a record refers to it.
- The stored length of a frame excludes its outer padding. The length of a record includes its internal padding. Offsets in an index refer to frame headers, never to record starts.
- The recommended file name suffix is `.nwt`, whether or not frames are compressed. The suggested private media type is `application/x-nwt`.

## Design principles

1. **Fixed layouts.** Every standard record has a fixed size or a size computed from stated lengths. A reader never scans for a terminator.
2. **Frames are the unit of integrity.** A frame carries one CRC over its raw payload. No record is trusted before its frame passes.
3. **Byte order is delivery order.** Records are never sorted. Definitions, snapshots and trade lifecycles depend on the order in which they arrive.
4. **Exact numbers.** Prices and quantities are integers scaled by 10⁻⁹. There is no floating point on the wire.
5. **Nothing is inferred.** A fact the producer does not know is null or "unknown". A consumer does not derive it from a symbol.
6. **One container for transport and storage.** A [store file](store-profile.md) is an ordinary container written with particular choices. Nothing is added to the container to support it.

Frames give batching, bounded decompression and corruption boundaries. They cost 64 bytes per batch and can add buffering latency. The 48-byte record header carries both timestamps, a 64-bit instrument ID and a sequence number in every record.
