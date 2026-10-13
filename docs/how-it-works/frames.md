# Frames

A frame is the unit of integrity and the unit of compression. Its 64-byte header states the kind of the frame, the codec and the sizes of the payload, and it carries two CRC-32C values: one over the header and one over the raw payload. The payload of a `DATA` frame is stored as it is or as one Zstandard frame, so a reader decodes each frame on its own. A reader trusts a record only after the frame that holds it passes both checks.

![A frame is a 64-byte header, a payload and zero padding; the payload is stored raw or as one Zstandard frame, and the raw payload is a run of whole records covered by a CRC-32C](../diagrams/frame-anatomy.svg "A frame: header, payload and padding, and what each CRC-32C covers")

[Specification: Frames](../specification/frames.md) · [Specification: Compression and integrity](../specification/compression-and-integrity.md)
