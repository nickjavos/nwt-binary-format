# Run it

Run the tool from the kit root with Python 3.10 or later. It uses the standard library only. Zstandard frames need the system [libzstd](https://github.com/facebook/zstd); raw frames need no library.

```bash
python3 tools/nwt.py COMMAND [ARGUMENTS]
```

`python3 tools/nwt.py --help` lists the subcommands, and `python3 tools/nwt.py COMMAND --help` lists the arguments of one.

| Command | What it does |
|---|---|
| [inspect](inspect.md) | Prints the header, the manifest, the frame table and the record counts |
| [validate](validate.md) | Checks the structure, the state rules, the summaries and the `ordering` declaration |
| [cat](cat.md) | Prints every record as one JSON object per line |
| [extract](extract.md) | Writes the records that match a filter to a new container |
| [merge](merge.md) | Combines containers under a stated ordering policy |
| [split](split.md) | Writes one container per record type, instrument or day |
| [repack](repack.md) | Rewrites a container as a store file |
| [query](query.md) | Prints matching records, reading only the frames that can hold a match |
| [resolve](resolve.md) | Looks up a symbol, ISIN, CUSIP or FIGI |
| [stats](stats.md) | Prints sizes, bytes per record type and the compression ratio |
| [convert](convert.md) | Converts a source file to a container |

The examples read the samples in `fixtures/real/`, `fixtures/real-reference/` and `fixtures/real-market/`, which are also on the [Downloads](../DOWNLOADS.md) page. They write to the folder `work/`:

```bash
mkdir -p work
```

## Rules for every command

- **Records keep their order.** No command reorders records. `repack` changes framing and compression; `extract`, `merge` and `split` keep the order of the records they keep.
- **A derived container has its own identity.** `extract`, `merge` and `split` write a container with a new random stream ID and with sequences that start at 1 for each publisher and channel. `repack` writes a new stream ID and keeps every sequence.
- **Manifests are exact.** The output of `extract`, `merge` and `split` declares only the record types it holds, and it declares an `ordering` only when its records have it.
- **Output is complete or absent.** A writing command writes to `OUT.tmp` and renames the file when it is finished. `OUT` cannot be one of the inputs.
- **A whole-file command validates what it reads.** `inspect`, `validate`, `cat`, `stats` and the writing commands read every frame and check every CRC-32C, length and sequence. `query` and `resolve` check the frames they read.

## Exit status

| Status | Meaning |
|---|---|
| 0 | The command succeeded. |
| 1 | The command failed. One line `NWT error: <reason>` is on standard error. |
| 2 | The arguments are wrong. The usage text is on standard error. |

A file that ends early fails with a reason that starts with `incomplete`. A Zstandard frame on a system without `libzstd` fails with `Zstd library not available`.

## Filters

`extract` and `query` take the same filters. Every filter is optional, and a record matches when it passes all the filters that are given.

| Option | Meaning |
|---|---|
| `--type TYPES` | Record types, by number or by name, separated by commas: `2,TRADE` |
| `--instrument IDS` | Instrument IDs and inclusive ranges, separated by commas: `2001,3000-3999` |
| `--from TIME` | Start of the `ts_event` range, inclusive: a record matches when its `ts_event` is at or after `TIME` |
| `--to TIME` | End of the `ts_event` range, exclusive: a record matches when its `ts_event` is before `TIME` |

`TIME` has one of three forms:

| Form | Example |
|---|---|
| Nanoseconds since 1970-01-01 UTC | `1758009784530300000` |
| Date, read as midnight UTC | `2025-09-16` |
| Timestamp with a zone and up to nine fractional digits | `2025-09-16T08:03:04.5303Z` |

A record whose `ts_event` is null never matches `--from` or `--to`. Reference records such as `LISTING` often have a null `ts_event`, so select them by record type or by instrument.
