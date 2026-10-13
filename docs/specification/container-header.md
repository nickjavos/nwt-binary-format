# Container header

The container starts at byte 0 with this 64-byte header.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `magic` | bytes | 8 | `4e 57 54 42 49 4e 0d 0a`, the ASCII text `NWTBIN\r\n` |
| 8 | `major` | u16 | 2 | 1 |
| 10 | `minor` | u16 | 2 | 0 or 1, by the rule below |
| 12 | `header_bytes` | u16 | 2 | 64 |
| 14 | `flags` | u16 | 2 | 0 |
| 16 | `metadata_bytes` | u32 | 4 | Total size of the metadata, including padding |
| 20 | `metadata_crc32c` | u32 | 4 | CRC of all metadata bytes, including padding |
| 24 | `stream_id` | bytes | 16 | Opaque nonzero 128-bit identifier |
| 40 | `created_ns` | u64 | 8 | Creation time, or null |
| 48 | `reserved` | u64 | 8 | 0 |
| 56 | `header_crc32c` | u32 | 4 | CRC of the 64 header bytes with this field set to zero |
| 60 | `reserved` | u32 | 4 | 0 |

**Version.**

- `minor` is 1 when the manifest declares at least one of the standard record types 10–22, and 0 otherwise. Declaring only private types (32,768–65,534) does not make it 1.
- A writer sets `minor` by this rule.
- A reader accepts 0 and 1. It rejects a header whose `minor` disagrees with the declared types.

**Metadata size.**

- `metadata_bytes` is a multiple of 8, at least 8 and at most 1,048,576.
- The first frame begins at offset `64 + metadata_bytes`.
- A reader validates the header before it trusts the metadata length.
- The CRC parameters are in [Compression and integrity](compression-and-integrity.md).

**Stream identifier.**

- `stream_id` is a byte string. It is not a little-endian integer and not a GUID structure of a programming language. Its text form is 32 lower-case hexadecimal characters in byte order.
- It identifies one immutable container byte sequence, including metadata and frames. A retransmission of the same bytes keeps it.
- A new connection that produces different framing, a filtered export, a repaired file and a recompressed file each get a new ID.
- We recommend generating it with a cryptographically strong random generator.
- A writer that regenerates the same bytes deterministically, such as a generator of conformance files, can use a fixed ID.
