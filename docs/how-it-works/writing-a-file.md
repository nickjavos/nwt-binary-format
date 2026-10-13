# Writing a file

A writer emits the container header and the metadata first. After that the `MANIFEST` cannot change. It takes the records in the order of the source, checks each one and collects whole records into a frame. When the frame is full, the writer computes the CRC-32C of the raw payload, optionally compresses the payload with Zstandard, and writes the frame. The `INDEX` frames and the `END` frame close the container.

![Five steps of a writer: open the container, check each record, fill a frame, seal the frame, close the container, with the bytes each step writes](../diagrams/write-path.svg "The steps of a writer and the bytes each step writes")

[Implementation guide: Write a file](../implementation/write-a-file.md) · [Specification: Writer obligations](../specification/reader-and-writer-requirements.md#writer-obligations)
