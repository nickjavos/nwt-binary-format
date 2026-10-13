# Specification

The specification defines NWT Binary Format: the bytes of a container, its metadata and its frames, the rules that a reader and a writer follow, and the 22 standard record types. It is the normative reference for engineers who implement a reader, a writer or a data pipeline for market data and reference data. Each section listed below is its own page, and together they cover everything that is not specific to one record type. Each record type has a page of its own with its fields and rules, linked from the table in [Record types](specification/record-types.md).

[How it works](HOW-IT-WORKS.md) introduces the format with diagrams. The [Field reference](FIELD-REFERENCE.md) describes how values are encoded and the structures shared by all records, and [Working with the examples](FEED-COOKBOOK.md) shows how to build and run the reference codecs. The [Implementation guide](IMPLEMENTATION-GUIDE.md) covers building a reader and a writer. [State and recovery](STATE-AND-RECOVERY.md) covers the state a consumer keeps.

## Sections

- [Conformance](specification/conformance.md): How the specification states its rules, what the format covers and which capabilities it defines.
- [File structure](specification/file-structure.md): A container is one byte sequence: a container header, metadata, a series of frames, and one `END` frame that closes it.
- [Data types and conventions](specification/data-types-and-conventions.md): How integers, alignment, text, time, decimal and null values and identifiers are represented.
- [Container header](specification/container-header.md): The 64-byte header at byte 0 of every container.
- [Metadata](specification/metadata.md): The metadata is a sequence of TLV elements.
- [Frames](specification/frames.md): Everything after the metadata is a sequence of frames.
- [Record header](specification/record-header.md): Every record starts with the same 48-byte header, whatever its record type.
- [Record types](specification/record-types.md): The format defines 22 standard record types.
- [Ordering, gaps, snapshots and replay](specification/ordering-gaps-snapshots-and-replay.md): How a consumer orders records, starts from an initial state, applies MBO snapshots, recovers after a gap and drops duplicates.
- [Compression and integrity](specification/compression-and-integrity.md): The CRC-32C checksums and the Zstandard compression of frames.
- [Store profile](specification/store-profile.md): The choices a writer makes to produce a store file, which is a normal container.
- [Transport and recovery](specification/transport-and-recovery.md): Over TCP, TLS or a reliable QUIC stream, the sender transmits one container header, the metadata and then the frames.
- [Schema evolution and registries](specification/schema-evolution-and-registries.md): How the container version, the schema versions and the type registries change, and how a reader treats unknown records.
- [Reader and writer requirements](specification/reader-and-writer-requirements.md): What a reader and a writer must do: incremental decoding, record iteration, error categories and the obligations of a writer.
- [Security and resource use](specification/security-and-resource-use.md): The security rules, the maximum sizes, the quantities that have no bound, and data quality.
- [Conversion from other formats](specification/conversion-from-other-formats.md): Data in another format needs an explicit converter.
- [Conformance files and examples](specification/conformance-files-and-examples.md): The four reference codecs (Python, Rust, C#, C++) read and write every record type and produce byte-identical output for the conformance files.
- [Implementation notes](specification/implementation-notes.md): Sizes, byte access, an order of work and measurements that help a new implementation.
- [References](specification/references.md): The RFCs and other standards that the format refers to.
