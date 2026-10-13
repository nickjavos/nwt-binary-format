# Decode throughput

The `bench` command of each reference codec loads the file into memory and then walks the container. It checks the CRC-32C of every frame, decompresses Zstandard frames and decodes every record into typed values. No text is parsed: a field of a fixed-width record is read at a known offset. For a file with Zstandard frames the figure includes decompression.

The codecs compute CRC-32C differently. The C++ and C# codecs use the CRC instruction of the processor, the Rust codec uses lookup tables, and the Python codec computes it in interpreted code.

<!-- nwt-chart: decode-throughput -->

| Codec | Frames | Records per second | MB per second |
|---|---|---|---|
| Python | Raw frames | 157,000 | 15 |
| Python | Zstandard frames | 149,000 | 14.3 |
| Rust | Raw frames | 7,080,000 | 680 |
| Rust | Zstandard frames | 5,980,000 | 574 |
| C# | Raw frames | 4,340,000 | 416 |
| C# | Zstandard frames | 3,770,000 | 362 |
| C++ | Raw frames | 10,700,000 | 1,030 |
| C++ | Zstandard frames | 9,620,000 | 923 |
