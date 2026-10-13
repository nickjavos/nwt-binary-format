# Store profile

A store file is an NWT container written for fast selective reads: large frames, [Zstandard](https://github.com/facebook/zstd) compression, an `INDEX` and `FRAME_SUMMARY` records. This page shows how to write one, how a reader finds records in it by time, record type and instrument, and how to check it. It is for engineers who keep NWT files in an archive or in object storage and query them.

## Sections

- [What the store profile is](store/what-the-store-profile-is.md): The store profile is a set of choices a writer makes.
- [When to use it](store/when-to-use-it.md): Use the store profile for a complete file that is read many times and queried by time, by record type or by instrument: a daily archive, an object in a bucket that is read with range requests, a research file on disk.
- [Write a store file](store/write-a-store-file.md): [repack](tools/repack.md) rewrites any container as a store file.
- [File layout](store/file-layout.md): The parts of a store file, in order, and what each part holds.
- [How a reader seeks by time and instrument](store/how-a-reader-seeks-by-time-and-instrument.md): A reader needs one operation: read n bytes at an offset.
- [What a partial read returns](store/what-a-partial-read-returns.md): A selective read returns the matching records of the frames it read, and nothing of the frames it skipped.
- [Choose settings](store/choose-settings.md): Only `DATA` frames are compressed, and only when the compressed form is smaller.
- [Check a store file](store/check-a-store-file.md): [validate](tools/validate.md) reads the whole file and checks the structure, the state rules, the `ordering` declaration and every value of every `FRAME_SUMMARY` record against the frame it describes.
