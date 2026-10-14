# NWT Binary Format

NWT Binary Format is a binary file and stream format for market data and reference data. It stores trades, quotes, order books, bars, instrument definitions and corporate actions as fixed-layout records inside checksummed frames. This repository contains what you need to build a reader, a writer or a data pipeline: the specification, a field reference, reference codecs in Python, Rust, C# and C++, the `nwt` command, conformance files and samples.

Documentation: <https://dev.nwt.one/fmt/>

## What is in this repository

| Folder | Content |
|---|---|
| `docs/` | Documentation sources |
| `schemas/records.json` | Machine-readable schema of the 22 record types |
| `examples/` | Reference codecs in Python, Rust, C# and C++ |
| `tools/` | The `nwt` command and the converters |
| `fixtures/` | Conformance files and samples |
| `tests/` | Checks of the codecs and of the format |

## Quick start

Run the commands from the repository root. The `nwt` command and the Python codec need Python 3.10 or later and use the standard library only.

Inspect and validate a sample, then read the frames that hold `TRADE_QUOTE` records:

```bash
python3 tools/nwt.py inspect fixtures/real-market/equity-quotes.nwt
python3 tools/nwt.py validate fixtures/real-market/equity-quotes.nwt
python3 tools/nwt.py query fixtures/real-market/equity-quotes.nwt --type TRADE_QUOTE --pretty | head -n 3
```

Write the conformance file with the Python codec, read it back and compare both results with the file in `fixtures/golden/`:

```bash
mkdir -p work
python3 examples/python/nwt_example.py write-golden work/golden.nwt
cmp work/golden.nwt fixtures/golden/all-records.nwt
python3 examples/python/nwt_example.py read work/golden.nwt work/golden-again.nwt > work/golden-fields.txt
cmp work/golden-again.nwt fixtures/golden/all-records.nwt
```

`cmp` prints nothing when the files are byte-identical. `work/golden-fields.txt` lists every field of every record. The `work/` folder is excluded by `.gitignore`.

The [documentation](https://dev.nwt.one/fmt/tools/) describes every subcommand of `nwt`.

## Reference codecs

Each block builds one codec, writes the conformance file, reads it back and compares both results with `fixtures/golden/all-records.nwt`. Zstandard frames need the system library `libzstd`; the [implementation guide](docs/IMPLEMENTATION-GUIDE.md) lists the toolchains and the library options.

Rust:

```bash
mkdir -p work
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example write-golden work/rust.nwt
examples/rust/target/debug/nwt-example read work/rust.nwt work/rust-again.nwt > work/rust-fields.txt
cmp work/rust.nwt fixtures/golden/all-records.nwt
cmp work/rust-again.nwt fixtures/golden/all-records.nwt
```

C#:

```bash
mkdir -p work
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll write-golden work/csharp.nwt
dotnet work/csharp/NwtExample.dll read work/csharp.nwt work/csharp-again.nwt > work/csharp-fields.txt
cmp work/csharp.nwt fixtures/golden/all-records.nwt
cmp work/csharp-again.nwt fixtures/golden/all-records.nwt
```

C++:

```bash
mkdir -p work
c++ -std=c++20 -O2 -DNWT_ZSTD examples/cpp/main.cpp -o work/nwt-cpp -lzstd
work/nwt-cpp write-golden work/cpp.nwt
work/nwt-cpp read work/cpp.nwt work/cpp-again.nwt > work/cpp-fields.txt
cmp work/cpp.nwt fixtures/golden/all-records.nwt
cmp work/cpp-again.nwt fixtures/golden/all-records.nwt
```

## Check a codec against the conformance files

`tests/golden_check.py` runs 16 checks of one codec against the files in `fixtures/golden/` and prints `NAME: 16/16 checks pass` when all succeed. The first argument is a label; the rest is the command that starts the codec.

```bash
python3 tests/golden_check.py python python3 examples/python/nwt_example.py
python3 tests/golden_check.py rust examples/rust/target/debug/nwt-example
python3 tests/golden_check.py csharp dotnet work/csharp/NwtExample.dll
python3 tests/golden_check.py cpp work/nwt-cpp
```

To check your own implementation, pass the command that starts it. The [implementation guide](docs/IMPLEMENTATION-GUIDE.md) lists the same steps one by one.

## Record types

| Type | Name | Purpose |
|---:|---|---|
| 1 | [`TRADE`](docs/records/TRADE.md) | Trade, with its correction and cancellation |
| 2 | [`QUOTE`](docs/records/QUOTE.md) | Best bid and ask |
| 3 | [`BAR`](docs/records/BAR.md) | Completed OHLCV bar |
| 4 | [`MBO`](docs/records/MBO.md) | Change to the order book, one order at a time |
| 5 | [`BOOK_SNAPSHOT`](docs/records/BOOK_SNAPSHOT.md) | Aggregate order book, ranked by price |
| 6 | [`INSTRUMENT_DEF`](docs/records/INSTRUMENT_DEF.md) | Instrument definition |
| 7 | [`STATUS`](docs/records/STATUS.md) | Trading status |
| 8 | [`GAP`](docs/records/GAP.md) | Discontinuity in the source |
| 9 | [`SYSTEM`](docs/records/SYSTEM.md) | Heartbeat and diagnostics |
| 10 | [`VENUE_DEF`](docs/records/VENUE_DEF.md) | Trading venue or segment, by market identifier code |
| 11 | [`OPTION_DEF`](docs/records/OPTION_DEF.md) | Option contract terms |
| 12 | [`LISTING`](docs/records/LISTING.md) | Symbol directory entry |
| 13 | [`STATISTICS`](docs/records/STATISTICS.md) | Open, high, low, close, settlement, VWAP, volume, open interest |
| 14 | [`OPTION_ANALYTICS`](docs/records/OPTION_ANALYTICS.md) | Implied volatility and Greeks |
| 15 | [`BOOK_DELTA`](docs/records/BOOK_DELTA.md) | Change to one price level of the aggregate order book |
| 16 | [`IMBALANCE`](docs/records/IMBALANCE.md) | Auction imbalance |
| 17 | [`SYMBOL_MAP`](docs/records/SYMBOL_MAP.md) | Symbol of an instrument over a time interval |
| 18 | [`TRADE_QUOTE`](docs/records/TRADE_QUOTE.md) | Trade with the top of book immediately before it |
| 19 | [`BEST_QUOTE`](docs/records/BEST_QUOTE.md) | Best bid and ask with the venue of each side |
| 20 | [`FRAME_SUMMARY`](docs/records/FRAME_SUMMARY.md) | Summary of one frame, for selective reads |
| 21 | [`SECURITY_DEF`](docs/records/SECURITY_DEF.md) | Security master entry with identifiers and key dates |
| 22 | [`CORPORATE_ACTION`](docs/records/CORPORATE_ACTION.md) | Corporate action event |

## Licenses

Third-party software and the notices of the sample data are listed in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
