# Use NWT in practice

This document shows what NWT Binary Format is good for and how to do real work with it. It has seven recipes: inspect and validate a file, convert a CSV export, print records, build an archive and query it, rebuild an order book, join market data to reference data, and read and write files from your own code. Each recipe is its own page, with the commands to run and the output to expect. The list below also holds the reasons to use a binary container, what to prepare before the first recipe and where to read next. The document is for engineers who want to try the format on real files before they read the [Specification](SPECIFICATION.md).

## Sections

- [Why a binary container](use-cases/why-a-binary-container.md): The reasons to keep market data in a binary container: exact values, nanosecond timestamps, a self-describing file, checksums, optional compression and selective reads.
- [Before you start](use-cases/before-you-start.md): The recipes use the `nwt` command, `tools/nwt.py`, and the Python reference codec, `examples/python/nwt_example.py`.
- [Inspect and validate a file](use-cases/inspect-and-validate-a-file.md): Find out what an NWT file holds and whether it is complete and consistent, without knowing anything about it in advance.
- [Convert a CSV export](use-cases/convert-a-csv-export.md): Turn a top-of-book export in CSV into an NWT file and prove that the conversion kept every value.
- [Print records as JSON Lines or CSV](use-cases/print-records-as-json-lines-or-csv.md): Read the records of a file as text, with the stored integers for a program or with readable values for a person.
- [Build an archive and query it](use-cases/build-an-archive-and-query-it.md): Combine several files into one compressed archive and read one time range or one instrument from it without reading the whole file.
- [Rebuild an order book](use-cases/rebuild-an-order-book.md): Replay order-level records into an order book and read the best bid and the best ask at a chosen time.
- [Join market data to reference data](use-cases/join-market-data-to-reference-data.md): Give a market event its symbol, venue, currency and unit, and give an instrument of a feed its listing name from a symbol directory.
- [Read and write a file from your code](use-cases/read-and-write-a-file-from-your-code.md): Read an NWT file in a program, compute with its values, and write a new NWT file.
- [Where to go next](use-cases/where-to-go-next.md): Where to read next: the documents on the format, the tool, the state rules and the downloads.

<!-- nwt-repo-card -->
