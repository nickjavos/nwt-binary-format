# Field reference

This page explains how the format encodes values and lists the fields of the structures that every container shares: the common record header, the container header, the metadata, the frame header, the index entries and the end structure. For each field it gives the offset, the type, the width, the unit, the null value and the validation rules. Use it while you write a decoder or an encoder, and when a value in a file needs an explanation. The fields of each record type are on its own page; start from [Record types](records/INDEX.md). The [Specification](SPECIFICATION.md) states the rules in full, and [Working with the examples](FEED-COOKBOOK.md) shows how to build and run the reference codecs.

## Sections

- [How values are encoded](fields/how-values-are-encoded.md): The three kinds of type and version numbers, the constants and conversions, and how to read a field table.
- [Common record header](fields/common-record-header.md): Every record starts with these 48 bytes.
- [Container structures](fields/container-structures.md): A container is a 64-byte container header, a metadata block, a run of frames and one `END` frame.
- [Interpretation checklist](fields/interpretation-checklist.md): A correct decoder or encoder agrees with every point below.
