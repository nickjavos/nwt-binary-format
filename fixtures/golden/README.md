# Conformance files

This folder holds the conformance files for all 22 record types. The four reference codecs (Python, Rust, C#, C++) produce these files byte for byte. An implementation conforms when it does the same.

The records come from `fixtures/catalog-golden.json` and the manifest from `fixtures/manifest-golden.json`. Every value is synthetic.

## Check an implementation

`tests/golden_check.py` runs 16 checks of one codec against these files. Run it from the kit root with a label and the command that starts the codec:

```sh
python3 tests/golden_check.py python python3 examples/python/nwt_example.py
```

The last line of the output is `python: 16/16 checks pass`. The exit status is 1 when a check fails.

## Files

`EX` stands for `python3 examples/python/nwt_example.py`. Run the commands from the kit root.

| File | Command | Contents |
|---|---|---|
| `all-records.nwt` | `EX write-golden FILE` | Raw frames, `minor` 1. 47 records in 16 `DATA` frames, then `INDEX` and `END`. 10,064 bytes, SHA-256 `d46687605d31019b63c9b122688add01381fd42481a1eb5c3abfb27b299b10d7`. |
| `all-records.zst.nwt` | `EX write-golden FILE --zstd` | The same records in Zstandard frames, level 3. |
| `all-records.zst-checksum.nwt` | `python3 tools/generate_fixtures.py` | The same records. Every `DATA` frame carries the Zstandard content checksum. A reader MUST accept this file. |
| `all-fields.txt` | `EX read fixtures/golden/all-records.nwt` | One line per field. `read` prints the same text for both Zstandard files. |
| `all-records.jsonl` | `EX to-json fixtures/golden/all-records.nwt` | One JSON object per record, values as stored. |
| `all-records.pretty.jsonl` | `EX to-json fixtures/golden/all-records.nwt --pretty` | Decimal prices and quantities, ISO 8601 timestamps. |
| `type-NN.csv` | `EX to-csv fixtures/golden/all-records.nwt N` | One file per record type, `NN` from 01 to 22. `BOOK_SNAPSHOT` (type 5) carries levels and is exported with `to-json`. `type-20.csv` holds the header line only. |
| `type-NN.pretty.csv` | `EX to-csv fixtures/golden/all-records.nwt N --pretty` | The same rows with decimal prices and ISO 8601 timestamps. |
| `records/NNN-label.bin` | `python3 tools/generate_fixtures.py` | One encoded record per catalog entry, numbered in catalog order: 48 conformance vectors. For the first entry of each type from 10 to 22, `EX record N FILE` writes the same bytes. |
| `records/NNN-label.json` | `python3 tools/generate_fixtures.py` | The catalog entry of that record. `EX decode-record records/NNN-label.bin` prints its fields. |
| `malformed/*.nwt` | `python3 tools/generate_fixtures.py` | 15 invalid containers, described below. |
| `malformed/expected.json` | `python3 tools/generate_fixtures.py` | Maps every malformed file to `"reject"`. |

The stored bytes of a Zstandard frame depend on the version of libzstd. To compare a Zstandard file, compare the output of `read` or the raw re-encoding:

```sh
EX read fixtures/golden/all-records.zst.nwt again.nwt | cmp - fixtures/golden/all-fields.txt
cmp again.nwt fixtures/golden/all-records.nwt
```

## Malformed files

`read` MUST exit with a non-zero status for every file in `malformed/`. Each file has one defect and is valid in every other respect: all CRCs, lengths, sequences and index entries are correct. A reader that skips the one check accepts the file.

| File | Defect | Error of the reference codec |
|---|---|---|
| `bad-enum.nwt` | `STATISTICS` `stat_type` is 9. | `invalid stat_type` |
| `bad-mask.nwt` | `BOOK_DELTA` `delta_flags` is 2. | `invalid delta_flags bits` |
| `nonzero-reserved.nwt` | `LISTING`: the first byte of the second `reserved` field, at offset 66, is 1. | `nonzero reserved` |
| `text-over-limit.nwt` | `VENUE_DEF` `name` is 256 bytes; the limit is 255. One byte is taken from `legal_entity`, so the record size is the same. | `name text limit` |
| `wrong-text-exact.nwt` | `OPTION_DEF` `osi_symbol` is 20 bytes; the allowed lengths are 0 and 21. One byte is moved to `underlying_symbol`. | `osi_symbol text length` |
| `wrong-fixed-size.nwt` | A `STATISTICS` record is 88 bytes with eight extra zero bytes; the fixed size is 80. | `padding/record length` |
| `wrong-minor.nwt` | Header `minor` is 0 and the manifest declares types 10 to 22. | `container minor does not match the declared types` |
| `wrong-minor-new-types.nwt` | Header `minor` is 0 and the manifest declares types 1 to 9, 21 and 22. The file holds the five records of types 21 and 22. A reader whose rule stops at type 20 accepts it. | `container minor does not match the declared types` |
| `undeclared-type.nwt` | The manifest declares type 99 in place of 13, and the file holds type 13 records. | `undeclared record type` |
| `undeclared-publisher.nwt` | The manifest declares publisher 3 in place of 1, and the records use publisher 1. | `undeclared publisher` |
| `zstd-content-size.nwt` | First `DATA` frame: the content size in the Zstandard header is `raw_bytes` + 1. | `Zstd content size` |
| `zstd-window.nwt` | First `DATA` frame: window descriptor 0x78, a 32 MiB window. The frame decompresses correctly. | `Zstd window` |
| `zstd-dictionary.nwt` | First `DATA` frame: the dictionary ID flag is set. | `Zstd dictionary` |
| `zstd-skippable.nwt` | First `DATA` frame: a skippable frame precedes the Zstandard frame. | `Zstd magic` |
| `zstd-trailing-bytes.nwt` | First `DATA` frame: a skippable frame follows the Zstandard frame inside `stored_bytes`. | `Zstd frame must fill stored_bytes exactly` |

A reader built without libzstd rejects the five `zstd-*` files as well: four by the check of the Zstandard frame header, and `zstd-trailing-bytes.nwt` with `Zstd library not available`.

## Rebuild

Run these commands from the kit root after you edit the schema, a catalog or a manifest:

1. `python3 tools/sync_embedded_data.py` copies the schema, catalogs and manifests into the Python and C++ sources. Rebuild the Rust, C# and C++ codecs afterwards.
2. `python3 tools/generate_fixtures.py` rewrites the files in `fixtures/` and in this folder. It needs libzstd. Two runs give identical files.
3. `python3 tests/test_contract.py` checks the Python codec and confirms that the files here are current.
