# What was measured

**Samples.** Sizes are measured on six samples of the kit. Each one holds real records of a different kind.

| Sample | Record types |
|---|---|
| [equity-quotes.nwt](files/samples/equity-quotes.nwt) | `INSTRUMENT_DEF`, `QUOTE`, `TRADE_QUOTE` |
| [equity-orders.nwt](files/samples/equity-orders.nwt) | `INSTRUMENT_DEF`, `MBO`, `TRADE` |
| [equity-bars.nwt](files/samples/equity-bars.nwt) | `INSTRUMENT_DEF`, `BAR` |
| [option-best-quotes.nwt](files/samples/option-best-quotes.nwt) | `INSTRUMENT_DEF`, `OPTION_DEF`, `BEST_QUOTE` |
| [statistics.nwt](files/samples/statistics.nwt) | `INSTRUMENT_DEF`, `OPTION_DEF`, `STATISTICS` |
| [corporate-actions-us.nwt](files/samples/corporate-actions-us.nwt) | `SECURITY_DEF`, `CORPORATE_ACTION` |

**Larger file.** Throughput and selective reads need more records than a sample holds. The script builds a file of 1,000,000 records through the writer of the Python reference codec: it writes the instrument definition of `equity-quotes` once and repeats the 2,476 data records of that sample. Each repetition moves `ts_event` and `ts_recv` forward by the time the sample spans, and the sequence numbers continue, so the file is in time order and `nwt validate` accepts it. Compressed sizes are measured on the samples only, because repeated records compress better than distinct ones.

**Text encodings.** CSV and JSON Lines are the output of the `to-csv` and `to-json` commands of the reference codec. CSV is one file per record type with a header line, and JSON Lines is one object per record. Each command has a plain output with integers and a `--pretty` output with decimal prices and ISO 8601 timestamps. The script counts the smaller of the two.

**Machine and units.** Hardware: Apple M5, 10 cores, 16 GB of memory. Sizes and frame counts are the same on every machine, and throughput is not. 1 MB is 1,048,576 bytes.

**How to rerun.** The script builds the Rust, C# and C++ reference codecs into a scratch folder, makes every measurement and writes the chart data to `docs/data/`. It needs `cargo`, `dotnet`, a C++ compiler and [libzstd](https://github.com/facebook/zstd). A codec whose toolchain is missing is left out of the decode chart. The source of the script is on [GitHub](https://github.com/nickjavos/nwt-binary-format).

<!-- nwt-title: All measurements -->
```bash
python3 tools/bench.py
```

<!-- nwt-title: A shorter run: 100,000 records, 3 timed runs -->
```bash
python3 tools/bench.py --quick
```
