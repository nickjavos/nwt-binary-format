# Reading a file

A reader of a whole file checks the container header and the metadata once. Then it repeats the same steps for every frame: check the frame header, read the payload, decompress it when the codec is Zstandard, and check the CRC-32C of the raw payload. The kind of the frame decides what follows: a `DATA` frame delivers records, an `INDEX` frame is compared with the frames already read, and the `END` frame ends the file. A failed check stops the read.

![A reader checks the container header and the metadata, then loops over frames: frame header, payload, and a branch by kind into records, index or end](../diagrams/read-path.svg "Reading a whole file, frame by frame")

[Implementation guide: Read a file](../implementation/read-a-file.md) · [Specification: Incremental decoding](../specification/reader-and-writer-requirements.md#incremental-decoding) · [The nwt command](../TOOLS.md)
