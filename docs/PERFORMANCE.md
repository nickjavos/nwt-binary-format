# Size and speed

This page gives measurements of NWT Binary Format made on the files of this kit: the size of the same records as text and as NWT, the decode and encode throughput of the four reference codecs, and the number of frames a time-range query reads. One script, `tools/bench.py`, produces every number, and you can rerun it on your own machine. The page is for engineers who choose a storage format for market data and want figures they can check.

## What was measured

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

**Machine and units.** Machine: Apple M5, 10 cores, 16 GB of memory. Sizes and frame counts are the same on every machine, and throughput is not. 1 MB is 1,048,576 bytes.

**How to rerun.** The script builds the Rust, C# and C++ reference codecs into a scratch folder, makes every measurement and writes the chart data to `docs/data/`. It needs `cargo`, `dotnet`, a C++ compiler and [libzstd](https://github.com/facebook/zstd). A codec whose toolchain is missing is left out of the throughput charts.

<!-- nwt-title: All measurements -->
```bash
python3 tools/bench.py
```

<!-- nwt-title: A shorter run: 100,000 records, 3 timed runs -->
```bash
python3 tools/bench.py --quick
```

## Bytes per record

The chart divides the size of each file by the number of records in it. A record of NWT has binary fields of fixed width. A nanosecond timestamp takes 8 bytes, and the same value takes 19 digits as decimal text. JSON Lines also repeats every field name in every record. The records of `corporate-actions-us` carry long text fields, which NWT stores as UTF-8 without change, so the relative difference between CSV and NWT is the smallest there.

<!-- nwt-chart: bytes-per-record -->

| Sample | CSV | JSON Lines | NWT, raw frames |
|---|---|---|---|
| `equity-quotes` | 127 | 428 | 102 |
| `equity-orders` | 121 | 375 | 89.3 |
| `equity-bars` | 177 | 465 | 114 |
| `option-best-quotes` | 171 | 567 | 124 |
| `statistics` | 161 | 517 | 120 |
| `corporate-actions-us` | 578 | 1,800 | 487 |

## Bytes per record with Zstandard

NWT compresses each `DATA` frame separately. The chart compares the store file that `nwt repack` writes with the CSV files compressed whole, both with Zstandard level 3. Zstandard removes most of the redundancy of decimal text, so the two results are close: NWT is smaller for four samples and CSV for two. The NWT figure includes the manifest, the `INDEX` and the `FRAME_SUMMARY` records, a fixed part that weighs more in a smaller file.

The two forms are read differently. A reader of a store file decompresses only the frames it needs, and a compressed CSV file is decompressed from its first byte.

<!-- nwt-chart: bytes-per-record-compressed -->

| Sample | CSV, Zstandard | NWT, Zstandard frames |
|---|---|---|
| `equity-quotes` | 19.6 | 14.8 |
| `equity-orders` | 23.5 | 20.4 |
| `equity-bars` | 25.3 | 30.1 |
| `option-best-quotes` | 27.6 | 22.8 |
| `statistics` | 23.3 | 21.2 |
| `corporate-actions-us` | 69.4 | 69.6 |

## Size at one million records

The larger file shows the same comparison for 1,000,000 records. After one instrument definition it holds `QUOTE` records of 96 bytes and `TRADE_QUOTE` records of 120 bytes. A file with raw frames is the records themselves, a 64-byte header for each frame, the manifest and the `INDEX`.

<!-- nwt-chart: size-by-encoding -->

| Encoding | Size, MB |
|---|---|
| CSV | 123 |
| JSON Lines | 410 |
| NWT, raw frames | 96 |

## Decode throughput

The `bench` command of each reference codec loads the file into memory and then walks the container. It checks the CRC-32C of every frame, decompresses Zstandard frames and decodes every record into typed values. No text is parsed: a field of a fixed-width record is read at a known offset. A file with Zstandard frames decodes more slowly than a file with raw frames, because each frame is decompressed first.

The codecs compute CRC-32C differently. The C++ and C# codecs use the CRC instruction of the processor, the Rust codec uses lookup tables, and the Python codec computes it in interpreted code.

<!-- nwt-chart: decode-throughput -->

| Codec | Frames | Records per second | MB per second |
|---|---|---|---|
| Python | Raw frames | 142,000 | 13.6 |
| Python | Zstandard frames | 136,000 | 13 |
| Rust | Raw frames | 5,360,000 | 514 |
| Rust | Zstandard frames | 5,810,000 | 557 |
| C# | Raw frames | 3,780,000 | 363 |
| C# | Zstandard frames | 3,610,000 | 346 |
| C++ | Raw frames | 11,000,000 | 1,060 |
| C++ | Zstandard frames | 7,400,000 | 710 |

## Encode throughput

Encoding writes the decoded values back to record bytes. The measurement covers records only: no frame is built, no checksum is computed and nothing is compressed. The C# codec keeps a fixed-width record as a struct with the layout of the record, so it encodes a record with one copy.

<!-- nwt-chart: encode-throughput -->

| Codec | Records per second | MB per second |
|---|---|---|
| Python | 4,710,000 | 452 |
| Rust | 12,500,000 | 1,200 |
| C# | 77,700,000 | 7,460 |
| C++ | 12,800,000 | 1,230 |

## Selective read

The store file made from the larger file has 97 `DATA` frames of 1,048,576 raw bytes. A query for 60 seconds of `ts_event` from the middle of the file reads the `INDEX`, the frame of `FRAME_SUMMARY` records and the one frame whose time range overlaps the window. That is 2 `DATA` frames out of 97, and the count is exact: it follows from the file and the query, not from the machine.

<!-- nwt-chart: selective-read -->

The second chart gives the time of the same query in the Python `nwt` tool, from opening the file to the last matching record. The whole-file read scans every frame and applies the same filter. Both return the same 181 records. [Store profile](STORE.md#how-a-reader-seeks-by-time-and-instrument) describes how a reader chooses the frames, and [The nwt command](TOOLS.md#query) describes the `query` command.

<!-- nwt-chart: selective-read-time -->

| Read | `DATA` frames read | Time, ms |
|---|---|---|
| Time-range query | 2 | 61.3 |
| Whole file | 97 | 7,880 |

## How to read these numbers

The reference codecs are written for clarity and for byte-exact agreement with each other, and the throughput figures are those of this code. Throughput depends on the processor, on memory and on the record mix: the figures above are for records of 96 and 120 bytes on the machine named on this page. Sizes and frame counts are properties of the files, and a rerun gives the same values on any machine.

[Store profile](STORE.md) · [Compression and integrity](SPECIFICATION.md#compression-and-integrity) · [Use NWT in practice](USE-CASES.md)
