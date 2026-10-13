# Read and write a file from your code

**Goal.** Read an NWT file in a program, compute with its values, and write a new NWT file.

**Input.** [equity-quotes.nwt](files/samples/equity-quotes.nwt): 2,000 `QUOTE` and 476 `TRADE_QUOTE` records of one equity. The codec is `examples/python/nwt_example.py`. Its `Reader` needs one thing from a source, a function that returns `n` bytes at an offset, and `open_reader` builds that function for an open file:

<!-- nwt-file: examples/python/nwt_example.py lines=866-871 -->

**Steps.**

1. Save this program as `work/my_trades.py`. It reads the sample, keeps the definition and the trades, computes the traded volume and the volume-weighted average price with integers, and writes the kept records to a new container:

   ```python
   import os, sys, time
   sys.path.insert(0, "examples/python")
   import nwt_example as codec

   # Read: the container header, the manifest and every frame are checked on the way.
   with open("fixtures/real-market/equity-quotes.nwt", "rb") as f:
       reader = codec.open_reader(f)
       publishers = reader.manifest["publishers"]
       kept = [r for r in codec.complete_records(reader) if r["type"] in (6, 18)]   # INSTRUMENT_DEF, TRADE_QUOTE

   # Compute with the stored integers: prices and quantities are scaled by 10^9.
   trades = [r["fields"] for r in kept if r["type"] == 18]
   volume = sum(int(t["quantity"]) for t in trades)
   turnover = sum(int(t["price"]) * int(t["quantity"]) for t in trades)
   print(len(trades), "trades, volume", codec.pretty_decimal(volume),
         "average price", codec.pretty_decimal(turnover // volume))

   # Write: a new container with its own manifest, stream ID and sequences.
   manifest = codec.build_manifest("EXAMPLE.TRADES", "my-app", publishers, types=[6, 18])
   sequencer = codec.Sequencer()
   with open("work/my-trades.nwt", "wb") as out:
       writer = codec.Writer(out, manifest, os.urandom(16), created_ns=time.time_ns())
       for record in kept:
           fields = record["fields"]
           fields["sequence"] = str(sequencer.next(int(fields["publisher_id"]), int(fields["channel_id"])))
           writer.write(record)
       writer.close()
   ```

   ```bash
   python3 work/my_trades.py
   python3 tools/nwt.py validate work/my-trades.nwt
   ```

   ```text
   476 trades, volume 24421.000000000 average price 177.373739404
   valid records=477 data_frames=1 summaries=0 ordering=none
   ```

   A decoded record is a dictionary with `type`, `fields`, `texts` and `levels`, and every field is the stored integer as a decimal string. The average is the sum of price times quantity divided by the sum of quantity, rounded down to nine decimals. `Writer.close` writes the last `DATA` frame, the `INDEX` and `END`.
2. Read the new file with each reference codec. The four programs have the same commands. Each tab below builds one codec and prints the first trades of the file as CSV.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- nwt-title: Rust -->
```bash
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- nwt-title: C# -->
```bash
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- nwt-title: C++ -->
```bash
c++ -std=c++20 -O2 -DNWT_ZSTD examples/cpp/main.cpp -o work/nwt-cpp -lzstd
work/nwt-cpp to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- /nwt-tabs -->

After the messages of the build, every tab prints the same three lines:

```text
record_bytes,record_type,schema_version,flags,publisher_id,channel_id,instrument_id,ts_event,ts_recv,sequence,price,quantity,trade_id,bid_price,ask_price,bid_quantity,ask_quantity,bid_order_count,ask_order_count,aggressor,conditions
120,18,1,0,2,0,11667,2025-09-16T08:00:00.256830296Z,2025-09-16T08:00:00.256994090Z,2,177.030000000,180.000000000,0,177.030000000,183.000000000,200.000000000,200.000000000,1,1,2,0
120,18,1,0,2,0,11667,2025-09-16T08:00:00.283911761Z,2025-09-16T08:00:00.284075365Z,3,177.180000000,100.000000000,0,177.180000000,183.000000000,100.000000000,200.000000000,1,1,2,0
```

**Result.** You have a program that reads, computes and writes NWT with the Python reference codec, and a file that all four reference codecs read identically. The [Implementation guide](../IMPLEMENTATION-GUIDE.md#build-and-run) lists the toolchains and the build options, and shows the same reading and writing in Rust, C# and C++ under [Read a file](../IMPLEMENTATION-GUIDE.md#read-a-file) and [Write a file](../IMPLEMENTATION-GUIDE.md#write-a-file).
