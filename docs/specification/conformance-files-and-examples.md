# Conformance files and examples

## Conformance files

The four reference codecs (Python, Rust, C#, C++) read and write every record type and produce byte-identical output for the conformance files.

| File | Content |
|---|---|
| [all-records.nwt](files/samples/all-records.nwt) | Conformance file: one container with 47 records of 21 record types (every type except `FRAME_SUMMARY`), raw frames |
| [all-records.zst.nwt](files/samples/all-records.zst.nwt) | The same records in Zstandard frames |
| [records.json](files/records.json) | Machine-readable schema of all 22 record types |
| [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip) | The whole kit: documents, schema, reference codecs, tools and fixtures |
| [SHA256SUMS.txt](files/SHA256SUMS.txt) | Checksums of every hosted file |

In the kit, the conformance files are in `fixtures/golden/`, and the conformance vectors are listed in `fixtures/catalog-golden.json`. The conformance vectors cover every field of all 22 record types, so that implementations can be compared byte for byte.

The samples in `fixtures/real/`, `fixtures/real-market/` and `fixtures/real-reference/` show records converted from source files. See [Reference data samples](../REAL-DATA.md) and [Market data samples](../REAL-DATA-MARKET.md). Every hosted file is listed in [Downloads](../DOWNLOADS.md).

## Minimal example file

The minimal example file, `fixtures/basic/example.nwt`, is one uncompressed market-data container of 920 bytes. It has three frames (`DATA`, `INDEX`, `END`) and two records: an `INSTRUMENT_DEF` followed by a `TRADE`. The `END` frame reports normal completion.

<!-- nwt-title: SHA-256 of example.nwt -->
```text
7bd77cec1d742d752942b41ff1dbcec82b625e50c4ea8b0ca9cf4fe81216fa85
```

| Component | Offset |
|---|---:|
| Container header | 0 |
| Metadata | 64 |
| `DATA` frame header | 432 |
| `INSTRUMENT_DEF` record | 496 |
| `TRADE` record | 632 |
| `INDEX` frame header | 720 |
| `END` frame header | 824 |

The `TRADE` record has these values:

| Field | Value |
|---|---|
| `publisher_id`, `channel_id`, `instrument_id` | 1, 0, 1001 |
| `sequence` | 2. The `INSTRUMENT_DEF` has sequence 1 |
| `ts_event` | `1700000000000000000` |
| `ts_recv` | `1700000000000000100` |
| `price` | `123450000000`, which is 123.45 USD |
| `quantity` | `10000000000`, which is 10 shares |
| `trade_id`, `original_sequence` | 42, 0 |
| `action`, `aggressor` | `NEW`, buyer |

The complete 88-byte record follows. Offsets in the dump are from the start of the record.

<!-- nwt-title: TRADE record -->
```hex
00000000  58 00 00 00 01 00 01 00 01 00 00 00 00 00 00 00
00000010  e9 03 00 00 00 00 00 00 00 00 2a 36 fe 9c 97 17
00000020  64 00 2a 36 fe 9c 97 17 02 00 00 00 00 00 00 00
00000030  80 82 31 be 1c 00 00 00 00 e4 0b 54 02 00 00 00
00000040  2a 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00000050  01 01 00 00 00 00 00 00
```

In the explicit little-endian syntax of the Python `struct` module, the 48-byte record header is `<IHBBIIQQQQ` and the body of `TRADE` is `<qQQQBBHI`. The record header is 48 bytes, an `INDEX` entry is 40 bytes and a `TRADE` record is 88 bytes. These strings describe the serialization. They do not permit the use of a native structure layout without a check.

## Conformance tests

An implementation is tested with round trips between independent writers and readers and with the cases below.

| Area | Required cases and expected result |
|---|---|
| Conformance files | Decode the values of the conformance files. Reproduce their exact bytes with the fixed stream ID and creation time |
| Fragmentation | Every split point of the header and of a short file, single-byte reads, many frames in one read. The events are identical |
| Primitive values | Negative and zero prices, epoch and null times, maximum legal integers. The values are exact |
| CRC | The known check value. An altered header, altered metadata and an altered raw payload are rejected |
| Lengths | Too short, too long, overflow, misalignment, count mismatch and trailing bytes are rejected |
| Padding | Nonzero padding of a TLV element, a record or a frame is rejected |
| Metadata | Duplicate keys, duplicate TLV types, an unknown required TLV or schema, an undeclared publisher or type are rejected |
| Evolution | An unknown optional record is skipped and counted. An unknown required version is rejected |
| Compression | Raw, Zstandard and mixed containers. A dictionary, an excess window, concatenation, extra bytes and a wrong output size are rejected |
| Zstandard header | A frame with a content checksum is accepted. A dictionary, a skippable frame, trailing bytes, a wrong content size and an oversized window are rejected. A missing library is reported and does not affect raw frames |
| Index | A bad offset, a missing or duplicate entry, a mismatch and an illegal frame order are rejected |
| Completion | Normal and aborted `END` are distinguished. A missing or truncated `END` is reported as incomplete |
| Sequencing | Continuity across frames. A duplicate, a gap and a wrap are rejected. Channels are independent |
| Container `minor` | `minor` 1 when a record type 10–22 is declared, `minor` 0 otherwise. A mismatch in either direction is rejected, including `minor` 0 in a file whose only such types are 21 and 22 |
| Trades | The lifecycle of new, correct and cancel. A missing original and an update after a cancel are rejected |
| Quotes and books | Empty and crossed quotes are accepted. An invalid encoding of an absent side and duplicate price levels are rejected |
| `MBO` | Clear, add, modify and delete. A snapshot across frames is atomic. A nested and an unfinished snapshot are rejected |
| Book deltas | A delta on an invalid book, a delete of a missing level, growth past 1,024 levels and invalidation by `GAP` |
| Source gaps | Each kind of state is invalidated. Recovery restores only the state of the corresponding record type |
| Definitions | The before-use rule, updates, immutable units and identity, preserved private fields |
| Fields and texts | Every field, enum, flag mask and reserved field. Text maximums are counted in bytes: a 255-byte text accepts 127 two-byte characters plus one ASCII byte and rejects one byte more. Exact fixed sizes. Wrong text lengths are rejected |
| Reference and market records | The null rules of `STATISTICS`, the side and quantity rule of `IMBALANCE`, overlapping `SYMBOL_MAP` intervals, `OPTION_DEF` against `INSTRUMENT_DEF`, replacement by identity for `VENUE_DEF`, `OPTION_DEF`, `LISTING`, `SECURITY_DEF` and `CORPORATE_ACTION` |
| Summaries and ordering | A `FRAME_SUMMARY` that disagrees with a full scan is rejected. A false `ordering` claim is rejected. A query answered from summaries equals a full scan with the same filter |
| Text output | CSV and JSON escaping of a text with a comma, a double quote, a line feed and a control byte is identical in every language |
| Resource maximums | Declared oversized values are rejected before allocation. Decompression and state are bounded |
| Fuzzing | Truncated, random and mutated inputs cannot crash, hang, read out of bounds or allocate without bound |

- For interoperability testing, we recommend two independently developed implementations, preferably in different languages, with both valid and deliberately malformed files.
- Re-encoding with another compressor need not give identical compressed bytes. The decoded raw records and the meaning of the metadata agree.
- A retry that claims to be byte-identical keeps the original compressed bytes.
