# One file, front to back

A container starts with a 64-byte header and the metadata. The metadata holds the `MANIFEST`, which declares every publisher and every record type of the file, and the optional `PROVENANCE`. Everything after the metadata is a sequence of frames. `DATA` frames carry the records, optional `INDEX` frames list the `DATA` frames, and one 96-byte `END` frame closes the container.

![A container from byte 0 to the end: the container header, the metadata, DATA frames, optional INDEX frames and the END frame, each with its offset and size](../diagrams/file-structure.svg "The parts of a container, with their offsets and sizes")

[Specification: File structure](../specification/file-structure.md) · [Specification: Container header](../specification/container-header.md) · [Specification: Metadata](../specification/metadata.md)
