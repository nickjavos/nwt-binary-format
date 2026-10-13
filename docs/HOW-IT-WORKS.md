# How it works

NWT Binary Format stores market data and reference data as fixed-layout records inside checksummed frames. This page explains the format with diagrams: the path from a source to a reader, the file from its first byte to its last, one frame, one record, the record types and the keys that join them, and the steps a writer and a reader follow. Read it first if the format is new to you. Every section links to the page that gives the exact rules.

## Sections

- [From source to reader](how-it-works/from-source-to-reader.md): A converter maps the rows of a source file to records, and a writer packs the records into one container.
- [Why the format looks like this](how-it-works/why-the-format-looks-like-this.md): Four choices explain most of the format.
- [One file, front to back](how-it-works/one-file-front-to-back.md): A container starts with a 64-byte header and the metadata.
- [Frames](how-it-works/frames.md): A frame is the unit of integrity and the unit of compression.
- [Records](how-it-works/records.md): Every record starts with the same 48-byte header: its length and type, its publisher, channel and instrument, two timestamps in nanoseconds and a sequence number.
- [From a value to bytes](how-it-works/from-a-value-to-bytes.md): This section follows one trade from the sample [equity-orders.nwt](files/samples/equity-orders.nwt) from its values to its bytes and back.
- [How the record types relate](how-it-works/how-the-record-types-relate.md): The 22 record types form three groups.
- [Writing a file](how-it-works/writing-a-file.md): A writer emits the container header and the metadata first.
- [Reading a file](how-it-works/reading-a-file.md): A reader of a whole file checks the container header and the metadata once.
- [Reading only what you need](how-it-works/reading-only-what-you-need.md): A store file is an ordinary container written with large compressed frames, an index and one `FRAME_SUMMARY` record for every frame.
- [How the file works as a database](how-it-works/how-the-file-works-as-a-database.md): A store file answers a query the way a database does: it consults a catalogue first and reads only the blocks the catalogue points to.
- [Keeping state and recovering from gaps](how-it-works/keeping-state-and-recovering-from-gaps.md): A consumer that builds order books, quotes or a trade tape applies the records in byte order and keeps state for each publisher, channel and instrument.
- [Files to open](how-it-works/files-to-open.md): The conformance files, the schema and the kit archive to open first.
