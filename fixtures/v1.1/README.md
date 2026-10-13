# NWT 1.1 golden files

Reference output of the Python codec for the 22-type catalog
(`fixtures/catalog-v1.1.json`, manifest `fixtures/manifest-v1.1.json`). Other
implementations must reproduce these files byte for byte, except where noted.
The exact output rules are in [FORMAT-NOTES.md](FORMAT-NOTES.md).

All data here is synthetic. These files are conformance vectors for comparing
the four codecs; they are not the kit's examples. Where a real example of a
record type exists (`fixtures/real*`), documentation should show that instead.

## Rebuild everything

Run from the kit root:

```sh
python3 tools/sync_embedded_data.py   # after editing the schema, catalog or manifest JSON
python3 tools/generate_fixtures.py    # rewrites fixtures/ (draft.2 files) and fixtures/v1.1/
python3 tests/test_contract.py        # checks the codec and that the files here are current
```

`generate_fixtures.py` needs the Zstd library (it writes the Zstd goldens). Running it twice gives identical files.

## Files and the command that reproduces each

`EX` stands for `python3 examples/python/nwt_example.py`. Commands are run from the kit root.

| File | Command | Notes |
|---|---|---|
| `all-records.nwt` | `EX write-v11 fixtures/v1.1/all-records.nwt` | Raw codec, `minor` 1, 47 records in 16 DATA frames (the last holds two), INDEX, END. 10072 bytes, SHA-256 `2e4f2bb08afa51f2ea0b981bc58ebd2939da5fd18e08b7b77696612333c75ba9`. |
| `all-records.zst.nwt` | `EX write-v11 fixtures/v1.1/all-records.zst.nwt --zstd` | Zstd level 3, libzstd 1.5.7. Bytes depend on the library version: compare the decoded report, or the raw re-encode, not these bytes. |
| `all-records.zst-checksum.nwt` | `python3 tools/generate_fixtures.py` | Same records; every DATA frame carries Zstd's own content checksum. Valid: a reader must accept it. No example command writes this variant. |
| `all-fields.txt` | `EX read fixtures/v1.1/all-records.nwt > fixtures/v1.1/all-fields.txt` | Also the exact output of `EX read` on both Zstd files. |
| `all-records.jsonl` | `EX to-json fixtures/v1.1/all-records.nwt > fixtures/v1.1/all-records.jsonl` | |
| `all-records.pretty.jsonl` | `EX to-json fixtures/v1.1/all-records.nwt --pretty > fixtures/v1.1/all-records.pretty.jsonl` | |
| `type-NN.csv` | `EX to-csv fixtures/v1.1/all-records.nwt N > fixtures/v1.1/type-NN.csv` | `NN` is the type with two digits: 01–04 and 06–22. There is no file for type 5, which `to-csv` refuses. `type-20.csv` is a header line only. |
| `type-NN.pretty.csv` | `EX to-csv fixtures/v1.1/all-records.nwt N --pretty > fixtures/v1.1/type-NN.pretty.csv` | |
| `records/NNN-label.bin` | `python3 tools/generate_fixtures.py` | One encoded record per catalog entry, numbered in catalog order (48 records, the standalone `048-frame-summary` included). For the first entry of each type 10–22, `EX record N FILE` writes the same bytes. |
| `records/NNN-label.json` | `python3 tools/generate_fixtures.py` | The catalog entry for that record. `EX decode-record records/NNN-label.bin` prints its fields. |
| `malformed/*.nwt` | `python3 tools/generate_fixtures.py` | Invalid containers; see below. |
| `malformed/expected.json` | `python3 tools/generate_fixtures.py` | Maps every malformed file to `"reject"`. |

Re-encoding checks:

```sh
EX read fixtures/v1.1/all-records.zst.nwt work/again.nwt | cmp - fixtures/v1.1/all-fields.txt
cmp work/again.nwt fixtures/v1.1/all-records.nwt
```

## Malformed files

Every file must make `read` exit with a non-zero status. Each has one defect and is otherwise valid: all CRCs, lengths, sequences and index entries are correct, so a reader that skips the one check accepts the file.

| File | Defect | Reference reader says |
|---|---|---|
| `bad-enum.nwt` | STATISTICS `stat_type` is 9 | `invalid stat_type` |
| `bad-mask.nwt` | BOOK_DELTA `delta_flags` is 2 | `invalid delta_flags bits` |
| `nonzero-reserved.nwt` | LISTING: first byte of the second `reserved` field (offset 66) is 1 | `nonzero reserved` |
| `text-over-limit.nwt` | VENUE_DEF `name` is 256 bytes (limit 255); one byte was moved from `legal_entity`, so the record size is unchanged | `name text limit` |
| `wrong-text-exact.nwt` | OPTION_DEF `osi_symbol` is 20 bytes (allowed: 0 or 21); one byte was moved to `underlying_symbol` | `osi_symbol text length` |
| `wrong-fixed-size.nwt` | STATISTICS record is 88 bytes (must be 80), with eight extra zero bytes | `padding/record length` |
| `wrong-minor.nwt` | Header `minor` is 0 while the manifest declares types 10–22 | `container minor does not match the declared types` |
| `wrong-minor-new-types.nwt` | Header `minor` is 0 while the manifest declares types 1–9, 21 and 22 only. The file holds the five type 21 and 22 records, sequences 1–5. A reader whose rule stops at type 20 accepts it | `container minor does not match the declared types` |
| `undeclared-type.nwt` | The manifest declares type 99 in place of 13, and the file contains type 13 records | `undeclared record type` |
| `undeclared-publisher.nwt` | The manifest declares publisher 3 in place of 1, and the records use publisher 1 | `undeclared publisher` |
| `zstd-content-size.nwt` | First DATA frame: the Zstd header's content size is `raw_bytes + 1` | `Zstd content size` |
| `zstd-window.nwt` | First DATA frame: Zstd window descriptor 0x78 (32 MiB); the frame still decompresses correctly | `Zstd window` |
| `zstd-dictionary.nwt` | First DATA frame: dictionary ID flag set | `Zstd dictionary` |
| `zstd-skippable.nwt` | First DATA frame: a skippable frame comes before the Zstd frame | `Zstd magic` |
| `zstd-trailing-bytes.nwt` | First DATA frame: a skippable frame follows the Zstd frame inside `stored_bytes` | `Zstd frame must fill stored_bytes exactly` |

The five `zstd-*` files are rejected by the hand-written header check or the one-frame rule. A build without the Zstd library rejects them as well: four by the header check, and `zstd-trailing-bytes.nwt` with `Zstd library not available`.
