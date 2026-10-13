# Implementation notes

## Record and frame sizes

- An uncompressed `TRADE` is 88 bytes, a `QUOTE` is 96, a `BAR` is 112 and an `MBO` is 88.
- A raw frame of 1,000 trades is 88,064 bytes, without the container metadata and the index. The frame header is 64 of 88,000 payload bytes, about 0.073%.
- A frame with a single trade is 152 bytes. The 64-byte frame header is about 72.7% of the 88-byte record.
- For bulk transfer, start with frames of 65,536 to 1,048,576 raw bytes and measure. A live system tunes a flush policy triggered by latency.
- The manifest JSON is parsed once per container. The record path uses fixed binary layouts.

## Byte access

- An uncompressed buffer can be read through views without copying payload fields, when ownership, lifetime, alignment and byte order are safe. A compressed frame needs storage for the decompressed bytes.
- CRC and validation still cost CPU time. Reading without copies does not remove validation, memory use or buffering.
- For a C or C++ implementation, we recommend explicit little-endian accessors, or a copy into validated aligned storage.
- A Rust implementation accounts for unaligned input and byte order. It does not cast arbitrary byte slices to references.
- A Python implementation can use `struct.unpack_from` after it has validated the bounds.

## Order of work

A practical order for a new implementation:

1. Container header, frame header and CRC.
2. Metadata and raw records.
3. The rules of the standard schemas.
4. `INDEX` and `END`.
5. Bounded Zstandard.
6. Incremental streaming and resume.
7. Fuzzing and independent interoperability tests.

For a public API, we recommend raw record access next to typed decoding, and a clear distinction between a valid container and a complete history of the source market.

## Measurements

- Measure records per second, bytes per second, CPU time, peak memory, compression ratio and end-to-end latency at the 50th, 95th and 99th percentiles.
- Report the hardware, the compiler or runtime, the codec version and level, the batch policy, the mix of record types, the checksum policy and whether book reconstruction is enabled.
- Include incompressible inputs and adversarially large inputs.
- A comparison with another format is valid only on equivalent data, fidelity and processing work.
