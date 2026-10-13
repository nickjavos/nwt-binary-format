# Compression and integrity

## CRC-32C

All CRC fields use CRC-32C (Castagnoli).

| Parameter | Value |
|---|---|
| Width | 32 bits |
| Polynomial | `0x1EDC6F41` |
| Reflected polynomial | `0x82F63B78` |
| Initial value | `0xFFFFFFFF` |
| Input and output | Reflected |
| Final XOR | `0xFFFFFFFF` |
| Check value for the ASCII text `123456789` | `0xE3069283` |
| Value for empty input | `0x00000000` |

- The result is stored as a little-endian `u32`.
- The CRC of a container header and of a frame header covers the whole 64-byte header with only its own CRC field set to zero.
- The metadata CRC covers every metadata byte, including the padding of TLV elements.
- The payload CRC covers exactly the raw payload. It excludes the padding after the payload.
- Every CRC is mandatory, also when the computed value is zero. There is no "CRC absent" convention.
- A CRC detects errors. It does not authenticate.

The algorithm is specified in [RFC 3720, Appendix B.4](https://www.rfc-editor.org/rfc/rfc3720.html#appendix-B.4).

## Zstandard

Codec 1 stores the payload as one [Zstandard](https://github.com/facebook/zstd) frame that conforms to [RFC 8878](https://www.rfc-editor.org/rfc/rfc8878.html). Codec 1 is allowed on `DATA` frames only.

**Stored payload.**

- The stored payload is exactly one ordinary Zstandard frame: no dictionary, no skippable frame, no second frame and no trailing bytes.
- The content size is present and equal to `raw_bytes`.
- The window size is at most 16,777,216 bytes. For a single-segment frame, the content size takes the place of the window size.
- The content checksum of Zstandard is optional. The CRC-32C of NWT stays mandatory.
- The decompressor consumes exactly `stored_bytes`.

**Header check.** A reader checks the frame header descriptor byte of the Zstandard frame before it calls the library.

| Bits | Meaning | Rule |
|---|---|---|
| 7–6 | Size of the content-size field | The content size is present |
| 5 | Single-segment flag | Allowed |
| 3 | Reserved | Zero |
| 2 | Content-checksum flag | Allowed. When the checksum is present, the library checks it |
| 1–0 | Dictionary ID flag | Zero |

A reader also checks that the size of the first frame the library finds equals `stored_bytes`. A skippable frame before or after it, a second frame and trailing bytes are therefore rejected.

**Zstandard library.** The reference codecs decode codec 1 with the system `libzstd` (Python, C#, C++) or the [zstd](https://github.com/gyscos/zstd-rs) crate (Rust). Raw frames need no library.

A reader without the library reads raw frames normally. For a codec 1 frame it fails with an error that says the library is not available. The header check runs first, so a malformed Zstandard header is rejected also without the library.

**Writer.**

- The compression level is the choice of the writer. A reader does not depend on it.
- Frames are independent. A frame cannot depend on a dictionary or on the compression state of an earlier frame.
- A writer stores a frame with codec 1 only when the compressed payload is smaller than the raw payload. Otherwise it uses codec 0. Both codecs can appear in one container.
- Compressed bytes differ between versions of the library, so two conforming writers need not produce the same compressed bytes. Compare decoded records, not compressed bytes.
- A very small batch can cost more to compress than it saves.

A reader enforces the output and window maximums before and during decompression.
