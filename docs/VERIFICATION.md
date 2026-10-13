# Verification report

**Release:** NWT 1.1-draft.1 developer kit
**Date:** 13 October 2026

This report lists what was run for this release and what was not. Nothing here is a performance claim or a statement that an implementation is production-ready.

## Environment

| Item | Version |
|---|---|
| Platform | macOS, arm64 |
| Python | 3.13.15 |
| .NET SDK | 10.0.401 |
| C++ compiler | Apple Clang 21.0.0, C++20 |
| Rust | rustc and cargo 1.99.0 |
| Zstandard library | libzstd 1.5.7 (system library for Python, C# and C++; the Rust build bundles its own copy) |
| nlohmann/json | 3.12.0 |

## What was run

### All four codecs against the conformance vectors

Each codec was built once and compared with the files in `fixtures/v1.1/`, which the Python reference codec produced. The same 16 checks were run for every language.

| Check | Python | C++ | C# | Rust |
|---|:-:|:-:|:-:|:-:|
| `write` reproduces the 1.0-draft.2 container byte for byte | pass | pass | pass | pass |
| `write-v11` reproduces the 22-type container byte for byte | pass | pass | pass | pass |
| `read` of the 1.0 container prints the expected field report | pass | pass | pass | pass |
| `read` of the raw 1.1 container | pass | pass | pass | pass |
| `read` of the Zstd container | pass | pass | pass | pass |
| `read` of the Zstd container whose frames carry a content checksum | pass | pass | pass | pass |
| Re-encoding the Zstd container gives the raw container byte for byte | pass | pass | pass | pass |
| `to-json` | pass | pass | pass | pass |
| `to-json --pretty` | pass | pass | pass | pass |
| `to-csv` and `to-csv --pretty` for every record type without levels (42 files) | pass | pass | pass | pass |
| `to-csv` refuses record type 5 | pass | pass | pass | pass |
| `record` for types 10–22 and `decode-record` for all 48 single-record files | pass | pass | pass | pass |
| All 15 malformed containers are rejected | pass | pass | pass | pass |
| A Zstd container written by the codec is read back by the codec | pass | pass | pass | pass |
| The same container is read by the Python reference codec | pass | pass | pass | pass |
| `bench` runs and prints its result line | pass | pass | pass | pass |

Builds: C++ and Rust compiled with no errors; C# built with 0 errors and 0 warnings.

Also run:

- C++ built without the Zstandard library, C# with the library hidden, and Rust built with `--no-default-features`: each reads the raw container and fails on the Zstd container with `Zstd library not available`.
- C++ and C# each read the Zstd container written by the other.
- The Python contract tests (`tests/test_contract.py`) passed, 20 of 20, for the 20-type contract. They were then updated for 22 types and not run again.
- The shared parsers in `tools/nwt_parse.py` were checked against 27 example values (exact decimals, scientific notation, half-even rounding, timestamps, dates, identifier prefixes): all correct.

### Real data

- **Order book against top of book.** The book rebuilt from the converted order-level records has the same best bid and ask as the venue's top-of-book file at every shared source sequence: 8,835 sequences on the equities venue and 5,578 on the futures venue, with no mismatch.
- **Bars against trades.** For all 434 one-minute bars of the equities day, the bar volume equals the summed size of the trades in that minute.
- Each real fixture was produced by one run of its converter and read back by the Python reference codec.

## What was not run

- **The corpus check.** `tools/corpus_check.py` was written but not run. Of the 121 sample files, 9 have been through the converters, as small slices. The converters are strict, so some of the other files may fail.
- **`tools/nwt.py`.** The command-line tool (`inspect`, `validate`, `cat`, `extract`, `merge`, `split`, `repack`, `query`, `resolve`, `stats`) was written and parsed for syntax. No command was executed.
- **The semantic checker for types 10–22.** The new rules in `examples/python/market_state.py` were not run, and the real fixtures were not passed through it.
- **Real fixtures in C++, C# and Rust.** The cross-language comparison used the synthetic conformance vectors only.
- **A second, independent build of the real fixtures** to confirm byte-identical output.
- **Benchmarks.** No throughput was measured on a file of meaningful size. The `bench` command was run only on the 47-record container, where its numbers mean nothing.
- **Review.** No independent code review was done for any part of this release.

## Known limits

- Zstandard needs the system `libzstd` for Python, C# and C++. Without it, codec 1 fails with a clear message and raw containers still work.
- The store features (`repack`, `query`, frame summaries), the converters and the semantic checks exist in Python only.
- The published other-listed symbol file contains two exchange letters that its publisher's definitions page does not list. The converter stops on them by design; the 100-row fixture slice is not affected.
- Timestamps before 1970 cannot be stored. A converter writes such a date as null, counts it in the provenance, and keeps the source text in the record's `details`.
- A modify event for an order that the converter has not seen is written as ADD. This happens when a slice starts after the order was placed.
- The real fixtures come from licensed data. See the `NOTICE.md` file in each fixture folder before redistributing them.
