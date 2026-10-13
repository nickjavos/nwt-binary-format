# The nwt command

`nwt` is the command-line tool of the kit: it inspects, validates, prints, filters, merges, splits, repacks, queries and converts NWT containers. The tool is the file `tools/nwt.py`, written in Python on top of the Python reference codec and the state rules. This reference is for engineers who work with NWT files in a shell or call the tool from Python. It has one page for each subcommand, one page about running the tool and one about using it from Python; the pages are listed below.

## Sections

- [Run it](tools/run-it.md): Run the tool from the kit root with Python 3.10 or later.
- [inspect](tools/inspect.md): Prints what a container holds: its header, its manifest, every frame and the number of records of each type.
- [validate](tools/validate.md): Checks a container completely and reports the first rule it breaks.
- [cat](tools/cat.md): Prints every record of a container as one JSON object per line.
- [extract](tools/extract.md): Writes the records that match a filter to a new container.
- [merge](tools/merge.md): Combines two or more containers into one, in an order you state.
- [split](tools/split.md): Writes one container for each record type, instrument or day of the input.
- [repack](tools/repack.md): Rewrites a container as a store file: the same records in the same order, in new frames, with Zstandard compression, an `INDEX` and `FRAME_SUMMARY` records.
- [query](tools/query.md): Prints the records that match a filter and reads only the frames that can hold a match.
- [resolve](tools/resolve.md): Looks up the instrument that a symbol or an identifier names.
- [stats](tools/stats.md): Prints the size of every part of a container and the bytes of each record type.
- [convert](tools/convert.md): Converts a source file, such as a CSV export or a public symbol directory, to a container.
- [Use from Python](tools/use-from-python.md): `tools/nwt.py` is importable.
