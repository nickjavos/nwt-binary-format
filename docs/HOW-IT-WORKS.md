# How it works

NWT Binary Format stores market data and reference data as fixed-layout records inside checksummed frames. This page explains the format with diagrams: the path from a source to a reader, the file from its first byte to its last, one frame, one record, the record types and the keys that join them, and the steps a writer and a reader follow. Read it first if the format is new to you. Every section links to the page that gives the exact rules.

## From source to reader

A converter maps the rows of a source file to records, and a writer packs the records into one container. The same container serves as a file and as a live stream. A reader validates the container, decodes it in full, or reads only the frames that a query needs.

![Sources feed a converter and a writer, which produce one NWT container; the nwt command, the four reference codecs and selective readers read it](diagrams/overview.svg "From source files to an NWT container and its readers")

[Use NWT in practice](USE-CASES.md) · [The nwt command](TOOLS.md) · [Implementation guide](IMPLEMENTATION-GUIDE.md)

## One file, front to back

A container starts with a 64-byte header and the metadata. The metadata holds the `MANIFEST`, which declares every publisher and every record type of the file, and the optional `PROVENANCE`. Everything after the metadata is a sequence of frames. `DATA` frames carry the records, optional `INDEX` frames list the `DATA` frames, and one 96-byte `END` frame closes the container.

![A container from byte 0 to the end: the container header, the metadata, DATA frames, optional INDEX frames and the END frame, each with its offset and size](diagrams/file-structure.svg "The parts of a container, with their offsets and sizes")

[Specification: File structure](SPECIFICATION.md#file-structure) · [Specification: Container header](SPECIFICATION.md#container-header) · [Specification: Metadata](SPECIFICATION.md#metadata)

## Frames

A frame is the unit of integrity and the unit of compression. Its 64-byte header states the kind of the frame, the codec and the sizes of the payload, and it carries two CRC-32C values: one over the header and one over the raw payload. The payload of a `DATA` frame is stored as it is or as one Zstandard frame, so a reader decodes each frame on its own. A reader trusts a record only after the frame that holds it passes both checks.

![A frame is a 64-byte header, a payload and zero padding; the payload is stored raw or as one Zstandard frame, and the raw payload is a run of whole records covered by a CRC-32C](diagrams/frame-anatomy.svg "A frame: header, payload and padding, and what each CRC-32C covers")

[Specification: Frames](SPECIFICATION.md#frames) · [Specification: Compression and integrity](SPECIFICATION.md#compression-and-integrity)

## Records

Every record starts with the same 48-byte header: its length and type, its publisher, channel and instrument, two timestamps in nanoseconds and a sequence number. The fixed fields of the record type follow. Some record types end with a variable part: texts or order book levels. The fixed fields give its size, so a reader never scans for a terminator. Prices and quantities are 64-bit integers scaled by 10⁹.

![A record is a 48-byte header, the fixed fields of its record type, an optional variable part and zero padding; TRADE, BOOK_SNAPSHOT and INSTRUMENT_DEF show the three shapes](diagrams/record-anatomy.svg "A record: the common header, the fixed fields, the variable part and the padding")

[Specification: Record header](SPECIFICATION.md#record-header) · [Field reference](FIELD-REFERENCE.md) · [Examples by record type](FEED-COOKBOOK.md)

## How the record types relate

The 22 record types form three groups. `INSTRUMENT_DEF` and the six reference record types describe instruments and venues. The twelve market record types say what happened to one instrument, and each needs an `INSTRUMENT_DEF` for that instrument earlier in the file. The three stream record types describe the stream itself. Above all of them stands the `MANIFEST`, which declares the publishers and the record types before the first record.

![The MANIFEST, then three groups of record types: instruments and venues, market records and stream records, with the key that links each group to the one above](diagrams/data-model.svg "The manifest and the three groups of record types")

Records about the same instrument share the pair `publisher_id` and `instrument_id`. The pair joins a market record to the definition of its instrument, and the definition to the option terms, the listing, the symbols, the security record and the corporate actions of that instrument. A `VENUE_DEF` is keyed by its market identifier code.

![Market records, INSTRUMENT_DEF, OPTION_DEF, SYMBOL_MAP, CORPORATE_ACTION, SECURITY_DEF and LISTING attach to one key, publisher_id with instrument_id; VENUE_DEF is keyed by mic](diagrams/data-model-keys.svg "The keys that join the records of one instrument")

[Specification: Record types](SPECIFICATION.md#record-types) · [Field reference](FIELD-REFERENCE.md) · [Glossary](GLOSSARY.md)

## Writing a file

A writer emits the container header and the metadata first. After that the `MANIFEST` cannot change. It takes the records in the order of the source, checks each one and collects whole records into a frame. When the frame is full, the writer computes the CRC-32C of the raw payload, optionally compresses the payload with Zstandard, and writes the frame. The `INDEX` frames and the `END` frame close the container.

![Five steps of a writer: open the container, check each record, fill a frame, seal the frame, close the container; beside them the bytes each step writes](diagrams/write-path.svg "The steps of a writer and the bytes each step writes")

[Implementation guide: Write a file](IMPLEMENTATION-GUIDE.md#write-a-file) · [Specification: Writer obligations](SPECIFICATION.md#writer-obligations)

## Reading a file

A reader of a whole file checks the container header and the metadata once. Then it repeats the same steps for every frame: check the frame header, read the payload, decompress it when the codec is Zstandard, and check the CRC-32C of the raw payload. The kind of the frame decides what follows: a `DATA` frame delivers records, an `INDEX` frame is compared with the frames already read, and the `END` frame ends the file. A failed check stops the read.

![A reader checks the container header and the metadata, then loops over frames: frame header, payload, and a branch by kind into records, index or end](diagrams/read-path.svg "Reading a whole file, frame by frame")

[Implementation guide: Read a file](IMPLEMENTATION-GUIDE.md#read-a-file) · [Specification: Incremental decoding](SPECIFICATION.md#incremental-decoding) · [The nwt command](TOOLS.md)

## Reading only what you need

A store file is an ordinary container written with large compressed frames, an index and one `FRAME_SUMMARY` record for every frame. A reader starts at the `END` frame, reads the index and the summaries, and learns the time range, the record types and the instrument range of every frame. It then reads only the frames that can hold a match. The result holds the same records in the same order as a full scan with the same filter. It does not include the definitions and the book state that the skipped frames built, so it is a partial read.

![In a store file a reader goes from the END frame to the INDEX frames, then to the summary frames, and reads only the DATA frames that can hold a match](diagrams/selective-read.svg "From END to INDEX to the summaries, then to the chosen frames")

[Store profile](STORE.md) · [Specification: Store profile](SPECIFICATION.md#store-profile) · [Size and speed](PERFORMANCE.md)

## Keeping state and recovering from gaps

A consumer that builds order books, quotes or a trade tape applies the records in byte order and keeps state for each publisher, channel and instrument. An order-level book starts as unknown. It becomes valid after an `MBO` `CLEAR` or after a snapshot that runs from `SNAPSHOT_BEGIN` to `SNAPSHOT_END`.

![An order-level book has three states, Unknown, Snapshot open and Valid; the MBO actions move it between them and a GAP returns it to Unknown](diagrams/order-book-state.svg "States of an order-level book and the MBO actions that move it")

A `GAP` record reports that the producer lost data from the source. It makes the order books, the quotes and the trading status of its publisher and channel unknown. Each of them becomes valid again when its own record arrives. An aggregate book is also valid again after a `BOOK_DELTA` with action `CLEAR` and `side` 0, and an order-level book after an `MBO` `CLEAR`. A damaged or missing frame is a different event: it is a transfer failure, and the reader stops.

![After a GAP record the top of book, the best quote, the aggregate book, the order-level book and the trading status are unknown until QUOTE, BEST_QUOTE, BOOK_SNAPSHOT, a completed snapshot and STATUS restore them](diagrams/recovery.svg "What a GAP record invalidates and which record restores each state")

[State and recovery](STATE-AND-RECOVERY.md) · [Specification: Ordering, gaps, snapshots and replay](SPECIFICATION.md#ordering-gaps-snapshots-and-replay)

## Files to open

- [all-records.nwt](files/samples/all-records.nwt) and [all-records.zst.nwt](files/samples/all-records.zst.nwt): the conformance files. Each holds 47 records of 21 record types (every type except `FRAME_SUMMARY`), the first in raw frames and the second in Zstandard frames.
- [records.json](files/records.json): the machine-readable schema of all 22 record types.
- [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip): the whole kit, with the documents, the schema, the reference codecs, the tools and the fixtures.

[Downloads](DOWNLOADS.md) · [Specification](SPECIFICATION.md) · [Field reference](FIELD-REFERENCE.md)
