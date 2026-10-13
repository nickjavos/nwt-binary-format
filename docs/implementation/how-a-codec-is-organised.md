# How a codec is organised

All four codecs have the same parts under the same names, so you can read one and find your way in the others. Nothing in a codec is written per record type: field order, widths, signedness, enumerations, flag masks and text length bounds come from the schema file [records.json](files/records.json).

A decoded record is a dictionary of decimal strings in Python, Rust and C#, and a vector of 64-bit integers in C++. Prices, quantities and timestamps stay integers from the wire to the output. Every integer is converted with explicit little-endian operations, and a byte buffer is never reinterpreted as a native structure.

Read the code in this order:

| Part | Python | Rust | C# | C++ |
|---|---|---|---|---|
| Fields to bytes and back | `encode_fields`, `decode_fields` | `enc_fields`, `dec_fields` | `EncFields`, `DecFields` | `wr`, `ldv` |
| Schema rules of a record | `check_schema` | `check_schema` | `CheckSchema` | `check_schema` |
| One record | `encode_record`, `decode_record` | `encode_record`, `decode_record` | `EncodeRecord`, `DecodeRecord` | `encode_record`, `decode_record` |
| Frame header and checksums | `frame`, `Reader.frame_info` | `frame`, `Reader::next` | `FrameBytes`, `Reader.Scan` | `frame`, `Reader::scan` |
| Metadata and `MANIFEST` | `tlv`, `parse_metadata`, `parse_manifest` | `tlv`, `parse_metadata`, `parse_manifest` | `Tlv`, `ParseMetadata`, `ParseManifest` | `tlv`, `parse_metadata`, `parse_manifest` |
| Zstandard frame check | `zstd_check`, `zstd_decompress` | `zstd_check`, `zstd_decompress` | `ZstdCheck`, `ZstdDecompress` | `zstd_check`, `zstd_decompress` |
| Container writer | `Writer` | `Writer` | `Writer` | `Writer` |
| Container reader | `Reader` | `Reader` | `Reader` | `Reader` |

The field codec is the smallest part. It walks the field list of the schema and converts each value with the width and signedness the schema gives:

<!-- nwt-file: examples/python/nwt_example.py lines=81-102 -->

The record decoder reads the 48-byte record header with the same field codec, selects the schema by `record_type`, reads the body fields, the depth levels and the texts, and then checks that the padded length equals `record_bytes` and that the padding is zero:

<!-- nwt-file: examples/python/nwt_example.py lines=145-170 -->

The frame header parser checks the header CRC-32C first, then the magic, the envelope version, the codec and the reserved bytes, and returns the sizes, the count and the time bounds of the frame:

<!-- nwt-file: examples/python/nwt_example.py lines=666-679 -->

The Python `Reader` has two paths. `scan` validates a container from the first byte to `END`. `index` and `read_frame` start from `END` and `INDEX` and read single frames; the [Store profile](../STORE.md) and the `query` command use them. The layouts these parts implement are defined in the [Specification](../SPECIFICATION.md), and every field is described in the [Field reference](../FIELD-REFERENCE.md).
