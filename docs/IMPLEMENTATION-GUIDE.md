# Implementation guide

This guide shows how to build and run the four reference codecs (Python, Rust, C#, C++), how their code is organised, and how to check your own reader or writer against the conformance files. It is for engineers who implement NWT Binary Format in a program of their own. Every reference codec reads and writes all 22 record types, raw and Zstandard frames, and the four produce byte-identical output for the conformance files.

## Requirements

Each reference codec is one program. Build the ones you need.

| Codec | Source | Toolchain | Libraries |
|---|---|---|---|
| Python | `examples/python/nwt_example.py` | Python 3.10 or later | Standard library only |
| Rust | `examples/rust/src/main.rs` | [Rust](https://github.com/rust-lang/rust) with [Cargo](https://github.com/rust-lang/cargo), edition 2021 | [serde](https://github.com/serde-rs/serde), [serde_json](https://github.com/serde-rs/json) and [zstd](https://github.com/gyscos/zstd-rs), pinned in `Cargo.lock` |
| C# | `examples/csharp/Program.cs` | [.NET SDK](https://github.com/dotnet/sdk) 10 | Base class library only |
| C++ | `examples/cpp/main.cpp` | A C++20 compiler: Clang or GCC | [nlohmann/json](https://github.com/nlohmann/json) 3.12.0, bundled in `examples/cpp/vendor/` |

Zstandard frames need the system [libzstd](https://github.com/facebook/zstd) (Python, C#, C++) or the [zstd](https://github.com/gyscos/zstd-rs) crate (Rust). Raw frames need no library.

- Install `libzstd` with your package manager: `brew install zstd` with Homebrew, `apt install libzstd-dev` on Debian and Ubuntu.
- Python and C# load `libzstd` at run time. Python looks for it with `ctypes.util.find_library("zstd")`; set the environment variable `NWT_ZSTD_LIB` to the path of the library to choose one yourself.
- C++ links `libzstd` at build time when you compile with `-DNWT_ZSTD`.
- Rust builds the `zstd` crate by default. `cargo build --no-default-features` builds the codec without it.

A codec that runs without the library reads and writes raw frames and rejects a Zstandard frame with the error `Zstd library not available`.

The licenses of the bundled and linked libraries are listed in [Licenses](https://github.com/nickjavos/nwt-binary-format/blob/main/THIRD-PARTY-NOTICES.md).

## Build and run

Run the commands from the kit root. Each tab builds one codec, writes the conformance file, reads it back and compares the result with [all-records.nwt](files/samples/all-records.nwt), which the kit keeps in `fixtures/golden/`.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
mkdir -p work
python3 examples/python/nwt_example.py write-golden work/python.nwt
python3 examples/python/nwt_example.py read work/python.nwt work/python-again.nwt > work/python-fields.txt
cmp work/python.nwt fixtures/golden/all-records.nwt
cmp work/python-again.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: Rust -->
```bash
mkdir -p work
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example write-golden work/rust.nwt
examples/rust/target/debug/nwt-example read work/rust.nwt work/rust-again.nwt > work/rust-fields.txt
cmp work/rust.nwt fixtures/golden/all-records.nwt
cmp work/rust-again.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: C# -->
```bash
mkdir -p work
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll write-golden work/csharp.nwt
dotnet work/csharp/NwtExample.dll read work/csharp.nwt work/csharp-again.nwt > work/csharp-fields.txt
cmp work/csharp.nwt fixtures/golden/all-records.nwt
cmp work/csharp-again.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: C++ -->
```bash
mkdir -p work
c++ -std=c++20 -O2 -DNWT_ZSTD examples/cpp/main.cpp -o work/nwt-cpp -lzstd
work/nwt-cpp write-golden work/cpp.nwt
work/nwt-cpp read work/cpp.nwt work/cpp-again.nwt > work/cpp-fields.txt
cmp work/cpp.nwt fixtures/golden/all-records.nwt
cmp work/cpp-again.nwt fixtures/golden/all-records.nwt
```
<!-- /nwt-tabs -->

`cmp` prints nothing and exits with status 0 when the two files are byte-identical. That is the expected result in every tab.

Notes on the C++ build:

- When `libzstd` is outside the default search path of the compiler, add its include and library folders. With Homebrew on Apple silicon these are `-I/opt/homebrew/include -L/opt/homebrew/lib`.
- To build without Zstandard, leave out `-DNWT_ZSTD` and `-lzstd`.
- `examples/cpp/CMakeLists.txt` builds the same program with [CMake](https://github.com/Kitware/CMake) 3.16 or later. It links `libzstd` when it finds the library and builds a raw-only codec when it does not.

<!-- nwt-file: examples/cpp/CMakeLists.txt -->

```bash
cmake -S examples/cpp -B work/cpp-build
cmake --build work/cpp-build
```

## Commands of the reference codecs

The four programs accept the same commands. For the same input, `read`, `decode-record`, `to-json` and `to-csv` print the same text in every language. `EX` stands for the program: `python3 examples/python/nwt_example.py`, `examples/rust/target/debug/nwt-example`, `dotnet work/csharp/NwtExample.dll` or `work/nwt-cpp`.

| Command | What it does |
|---|---|
| `EX write FILE` | Writes the container of record types 1–9 from `fixtures/catalog.json`: 49 records, `minor` 0. |
| `EX write-golden FILE [--zstd]` | Writes the conformance file from `fixtures/catalog-golden.json`: 47 records of 21 record types (every type except `FRAME_SUMMARY`) in 16 `DATA` frames, `minor` 1. With `--zstd` the `DATA` frames are compressed with Zstandard level 3. |
| `EX read FILE [REENCODED_FILE]` | Validates the whole container and prints every field of every record. With a second path, also writes the records again as raw frames of 3 records each, keeping the stream ID, the creation time and the metadata bytes of the input. |
| `EX record TYPE FILE` | Encodes the first catalog entry of record type number `TYPE` as one bare record, without a container. |
| `EX decode-record FILE` | Decodes one bare record and prints its fields, texts and depth levels. |
| `EX to-json FILE [--pretty]` | Prints one JSON object per record. With `--pretty`, prices and quantities are decimals with nine fractional digits, times are ISO 8601 UTC, and a null value is JSON `null`. |
| `EX to-csv FILE TYPE [--pretty]` | Prints a header line and one CSV line per record of type number `TYPE`. `BOOK_SNAPSHOT` (type 5) has depth levels and is refused; use `to-json` for it. |
| `EX bench FILE` | Decodes and re-encodes every record of the file and prints two lines, `decode` and `encode`, with the record count, the elapsed seconds and the rates. |

Every command starts by checking that the CRC-32C of the ASCII text `123456789` is `0xE3069283`. A failure prints `NWT error: <reason>` on standard error and exits with status 1.

`read` prints one line per field: `record_number.field=value`, then `record_number.levels.index.field=value` for depth levels and `record_number.text_name=text` for texts. Values are the stored integers in decimal.

```bash
head -n 12 work/python-fields.txt
```

```text
1.record_bytes=136
1.record_type=6
1.schema_version=1
1.flags=0
1.publisher_id=1
1.channel_id=0
1.instrument_id=2001
1.ts_event=1760000000000000000
1.ts_recv=1760000000000000100
1.sequence=1
1.price_increment=10000000
1.quantity_increment=1000000000
```

`to-csv` prints the stored integers, or readable values with `--pretty`:

```bash
python3 examples/python/nwt_example.py to-csv fixtures/golden/all-records.nwt 1 --pretty
```

```text
record_bytes,record_type,schema_version,flags,publisher_id,channel_id,instrument_id,ts_event,ts_recv,sequence,price,quantity,trade_id,original_sequence,action,aggressor,conditions
88,1,1,0,1,0,2001,2025-10-09T08:53:21.000000000Z,2025-10-09T08:53:21.000000100Z,15,149.250000000,100.000000000,1,0,1,1,0
```

[The nwt command](TOOLS.md) prints the same JSON Lines as `to-json` and adds inspection, validation, filtering and store files. It is written in Python, as are the state rules in `examples/python/market_state.py` and the converters.

## How a codec is organised

All four codecs have the same parts under the same names, so you can read one and find your way in the others. Nothing in a codec is written per record type: field order, widths, signedness, enumerations, flag masks and text length bounds come from the schema file [records.json](files/records.json).

A decoded record is a dictionary of decimal strings in Python, Rust and C#, and a vector of 64-bit integers in C++. Prices, quantities and timestamps stay integers from the wire to the output. Every integer is converted with explicit little-endian operations, and a byte buffer is never reinterpreted as a native structure.

Read the code in this order:

| Part | Python | Rust | C# | C++ |
|---|---|---|---|---|
| Fields to bytes and back | `encode_fields`, `decode_fields` | `enc_fields`, `dec_fields` | `EncFields`, `DecFields` | `wr`, `ldv` |
| Schema rules of a record | `check_schema` | `check_schema` | `CheckSchema` | `check_schema` |
| One record | `encode_record`, `decode_record` | `encode_record`, `decode_record` | `EncodeRecord`, `DecodeRecord` | `encode_record`, `decode_record` |
| Frame header and checksums | `frame`, `Reader.frame_info` | `frame`, `Reader::next` | `FrameBytes`, `Reader.Scan` | `frame`, `Reader::scan` |
| Metadata and `MANIFEST` | `tlv`, `parse_metadata`, `parse_manifest` | `tlv`, `parse_metadata`, `parse_manifest` | `Tlv`, `ParseMetadata`, `ParseManifest` | `tlv`, `parse_metadata`, `parse_manifest` |
| Zstandard frame check | `zstd_check`, `zstd_decompress` | `zstd_check`, `zstd_decompress` | `ZstdCheck`, `ZstdDecompress` | `zstd_check`, `zstd_decompress` |
| Container writer | `Writer` | `Writer` | `Writer` | `Writer` |
| Container reader | `Reader` | `Reader` | `Reader` | `Reader` |

The field codec is the smallest part. It walks the field list of the schema and converts each value with the width and signedness the schema gives:

<!-- nwt-file: examples/python/nwt_example.py lines=81-102 -->

The record decoder reads the 48-byte record header with the same field codec, selects the schema by `record_type`, reads the body fields, the depth levels and the texts, and then checks that the padded length equals `record_bytes` and that the padding is zero:

<!-- nwt-file: examples/python/nwt_example.py lines=145-170 -->

The frame header parser checks the header CRC-32C first, then the magic, the envelope version, the codec and the reserved bytes, and returns the sizes, the count and the time bounds of the frame:

<!-- nwt-file: examples/python/nwt_example.py lines=666-679 -->

The Python `Reader` has two paths. `scan` validates a container from the first byte to `END`. `index` and `read_frame` start from `END` and `INDEX` and read single frames; the [Store profile](STORE.md) and the `query` command use them. The layouts these parts implement are defined in the [Specification](SPECIFICATION.md), and every field is described in the [Field reference](FIELD-REFERENCE.md).

## Read a file

A reader validates a container in this order. `Reader.scan` in the Python codec follows the same steps.

![A reader checks the container header and the metadata, then loops over frames: frame header, payload, and a branch by kind into records, index or end](diagrams/read-path.svg "Reading a whole file, frame by frame")

1. Read the 64-byte container header. Check the magic `NWTBIN\r\n`, `major` 1, `minor` 0 or 1, the header length 64, the header CRC-32C, the reserved bytes and a stream ID that is not all zero.
2. Read the metadata. Check its length and its CRC-32C, split it into TLV elements and validate the `MANIFEST`. `minor` is 1 exactly when the manifest declares any record type 10–22.
3. Read each 64-byte frame header. Check its CRC-32C, the magic `NWF1`, the kind (`DATA`, `INDEX` or `END`), the codec, both sizes against the 16,777,216-byte maximum, and that `frame_seq` counts up from 0 without a hole.
4. Read the stored payload and its padding. For a Zstandard frame, check the Zstandard frame header and decompress to exactly `raw_bytes`. Check the payload CRC-32C over the raw payload.
5. For a `DATA` frame, split the payload by `record_bytes`. Check the record count, the sequence of each record within its publisher and channel, that the manifest declares the type and the publisher of each record, and that the time bounds of the frame equal the lowest and the highest non-null `ts_event`. Decode the records.
6. For `INDEX` frames, check that the entries equal the ones you computed from the `DATA` frames. For `END`, check the totals, the index offset and the status, and that nothing follows `END`.
7. Report a file that ends before `END` as incomplete, and a container whose `END` status is 1 as aborted.

The result is the decoded records in file order. A record is returned only after its frame has passed every check.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```python
import sys
sys.path.insert(0, "examples/python")
import nwt_example as nwt

with open("fixtures/real-market/equity-quotes.nwt", "rb") as f:
    reader = nwt.open_reader(f)                  # header, metadata and manifest are checked here
    trades = 0
    for record in nwt.complete_records(reader):  # a frame is checked before its records are returned
        if record["type"] == 18:                 # TRADE_QUOTE
            trades += 1
    print(trades, "TRADE_QUOTE records;", reader.end["total_records"], "records in all")
```
<!-- nwt-title: Rust -->
```rust
let ss: Schemas = serde_json::from_str(SCHEMA)?;
let mut reader = Reader::new(BufReader::new(File::open("work/python.nwt")?), &ss)?;
let mut trades = 0u64;
complete_records(&mut reader, &ss, |r| {
    if r.r#type == 1 {
        trades += 1;
    }
    Ok(())
})?;
println!("{trades} TRADE records");
```
<!-- nwt-title: C# -->
```csharp
using var input = OpenRead("work/python.nwt");
int trades = 0;
foreach (var r in Records(OpenReader(input)))
    if (r.type == 1)
        trades++;
Console.WriteLine($"{trades} TRADE records");
```
<!-- nwt-title: C++ -->
```cpp
Reader rd;
rd.open_file("work/python.nwt");
std::size_t trades = 0;
rd.scan(true, [&](const FrameInfo &, const std::vector<View> &, std::vector<Rec> &recs) {
  for (const auto &r : recs)
    if (r.type == 1)
      trades++;
});
need(rd.end.status == 0, "aborted container");
std::cout << trades << " TRADE records\n";
```
<!-- /nwt-tabs -->

The Python fragment is a complete program that imports the codec as a module. It reads the sample [equity-quotes.nwt](files/samples/equity-quotes.nwt) and prints:

```text
476 TRADE_QUOTE records; 2477 records in all
```

The Rust, C# and C++ codecs are single-source programs. Their fragments use the functions of that source and go inside it, for example as a new command next to `read`. On `work/python.nwt` each prints `1 TRADE records`.

## Write a file

![Five steps of a writer: open the container, check each record, fill a frame, seal the frame, close the container, with the bytes each step writes](diagrams/write-path.svg "The steps of a writer and the bytes each step writes")

1. Build the manifest: the dataset name, the producer, the profile, the clock `posix-ns`, the publishers and one schema entry for every record type you write. Declare `BOOK_DELTA` with `required` set to `true` and `FRAME_SUMMARY` with `required` set to `false`.
2. Choose a stream ID of 16 random bytes that are not all zero, and the creation time in nanoseconds.
3. Write the container header and the metadata: the `MANIFEST` element and, when you have one, the `PROVENANCE` element.
4. Give every record the next sequence of its publisher and channel, starting at 1, and encode it. Collect records into a frame until the frame is full, then write the `DATA` frame with its record count, its time bounds and the CRC-32C of the raw payload. Store the Zstandard form only when it is smaller than the raw payload.
5. Close the container: write the last `DATA` frame, the `INDEX` frames with one 40-byte entry per `DATA` frame, and `END` with the index offset, the totals and the status.

The result is a container that [validate](tools/validate.md) accepts.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```python
import os, sys, time
sys.path.insert(0, "examples/python")
import nwt_example as nwt

publisher = {"id": 1, "name": "Example Feed", "venue": "XNAS"}
manifest = nwt.build_manifest("EXAMPLE.TRADES", "my-writer/1", [publisher], types=[1, 6])
next_sequence = nwt.Sequencer()
now = time.time_ns()

definition = nwt.make_record(
    6, instrument_id=1001, ts_event=now, sequence=next_sequence.next(1, 0),
    price_increment=10_000_000, quantity_increment=1_000_000_000, contract_multiplier=nwt.NULL_I64,
    expiration_ns=nwt.NULL, underlying_instrument_id=0, strike=nwt.NULL_I64, asset_class=1,
    texts={"symbol": "NWTX", "venue": "XNAS", "currency": "USD", "quantity_unit": "share"},
)
trade = nwt.make_record(
    1, instrument_id=1001, ts_event=now, sequence=next_sequence.next(1, 0),
    price=124_250_000_000, quantity=2_500_000_000, trade_id=1, original_sequence=0,
    action=1, aggressor=1, conditions=0,
)

with open("work/trades.nwt", "wb") as out:
    writer = nwt.Writer(out, manifest, os.urandom(16), created_ns=now)
    writer.write(definition)
    writer.write(trade)
    writer.close()
```
<!-- nwt-title: Rust -->
```rust
fn write_container(
    path: &str,
    records: &[Record],
    manifest: &str,
    stream_id: [u8; 16],
    created_ns: u64,
    ss: &Schemas,
) -> R<()> {
    let metadata = tlv(1, 1, manifest.trim().as_bytes());
    let out = BufWriter::new(File::create(path)?);
    let mut w = Writer::new(out, metadata, stream_id, created_ns, 1 << 20, None, None, ss)?;
    for r in records {
        w.write(r, ss)?;
    }
    w.close(0)?.flush()?;
    Ok(())
}
```
<!-- nwt-title: C# -->
```csharp
static void WriteContainer(string path, IEnumerable<Record> records, string manifest, byte[] streamId, ulong createdNs)
{
    using var output = new FileStream(path, FileMode.Create, FileAccess.Write);
    var w = new Writer(output, Tlv(1, 1, Utf8.GetBytes(manifest.Trim())), streamId, createdNs);
    foreach (var r in records)
        w.Write(r);
    w.Close();
}
```
<!-- nwt-title: C++ -->
```cpp
void write_container(const std::string &path, const std::vector<Rec> &records, const std::string &manifest,
                     const std::array<std::uint8_t, 16> &stream_id, U created_ns) {
  std::ofstream out(path, std::ios::binary);
  need(bool(out), "open output");
  Writer w(out, tlv(1, 1, bytes(manifest)), stream_id, created_ns);
  for (const auto &r : records)
    w.write(r);
  w.close(0);
  out.close();
  need(bool(out), "write output");
}
```
<!-- /nwt-tabs -->

The writers take the frame size and the Zstandard level as further arguments: `frame_bytes` and `zstd_level` in Python, the arguments after `created_ns` in Rust and C++, `frameBytes` and `level` in C#. By default a frame holds up to 1,048,576 bytes of raw payload and is stored raw.

Check the Python result:

```bash
python3 tools/nwt.py validate work/trades.nwt
```

```text
valid records=2 data_frames=1 summaries=0 ordering=none
```

> **Important:** `write` and `write-golden` use a fixed stream ID and a fixed creation time so that their output is reproducible. A file with different bytes gets a new random stream ID. Keep a stream ID only for a byte-identical copy of the same container.

## Encode one record

1. Fill the ten header fields and the body fields of the record type.
2. Derive the lengths: the byte length of every text, the level count, and `record_bytes`, which is the fixed size of the type plus 48 bytes per depth level plus the text bytes, rounded up to a multiple of 8.
3. Check the schema rules: enumeration values, flag masks, text length bounds, and reserved fields equal to zero.
4. Write the 48-byte record header, the body fields in schema order as little-endian integers, the depth levels, the texts in the order of their length fields, and zero bytes up to `record_bytes`.

The `record` command writes one encoded record from the catalog, and `decode-record` reads it back:

```bash
python3 examples/python/nwt_example.py record 1 work/trade.bin
python3 examples/python/nwt_example.py decode-record work/trade.bin
```

```text
1.record_bytes=88
1.record_type=1
1.schema_version=1
1.flags=0
1.publisher_id=1
1.channel_id=0
1.instrument_id=1001
1.ts_event=1700000000000001000
1.ts_recv=1700000000000001100
1.sequence=2
1.price=123450000000
1.quantity=10000000000
1.trade_id=42
1.original_sequence=0
1.action=1
1.aggressor=1
1.conditions=0
1.reserved=0
```

In code, take a record, change its fields and encode it. The fragments set the price of that trade to 124.25 and its quantity to 2.5:

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```python
import sys
from copy import deepcopy
sys.path.insert(0, "examples/python")
import nwt_example as nwt

trade = deepcopy(next(r for r in nwt.CATALOG if r["type"] == 1))
trade["fields"]["price"] = "124250000000"      # 124.25
trade["fields"]["quantity"] = "2500000000"     # 2.5
wire = nwt.encode_record(trade)
assert len(wire) == 88
assert nwt.decode_record(wire)["fields"]["quantity"] == "2500000000"
print(wire.hex())
```
<!-- nwt-title: Rust -->
```rust
let records: Vec<Record> = serde_json::from_str(CATALOG)?;
let mut trade = records.iter().find(|r| r.r#type == 1).ok_or("no trade")?.clone();
trade.fields.insert("price".into(), "124250000000".into());    // 124.25
trade.fields.insert("quantity".into(), "2500000000".into());   // 2.5
let wire = encode_record(&trade, &ss)?;
let back = decode_record(&wire, &ss)?;
assert_eq!(wire.len(), 88);
assert_eq!(back.fields["quantity"], "2500000000");
```
<!-- nwt-title: C# -->
```csharp
var trade = Catalog("catalog").First(r => r.type == 1);
trade.fields["price"] = "124250000000";      // 124.25
trade.fields["quantity"] = "2500000000";     // 2.5
byte[] wire = EncodeRecord(trade);
Need(wire.Length == 88, "record size");
Need(DecodeRecord(wire).fields["quantity"] == "2500000000", "round trip");
```
<!-- nwt-title: C++ -->
```cpp
J catalog = J::parse(catalog_json);
J trade = *std::find_if(catalog.begin(), catalog.end(),
                        [](const J &r) { return r.at("type").get<U>() == 1; });
trade["fields"]["price"] = "124250000000";    // 124.25
trade["fields"]["quantity"] = "2500000000";   // 2.5
Bytes wire = encode_record(rec_from_json(trade));
need(wire.size() == 88, "record size");
need(encode_record(decode_record(wire)) == wire, "round trip");
```
<!-- /nwt-tabs -->

All four produce the same 88 bytes:

```hex
58000000 01000100 01000000 00000000 e9030000 00000000 e8032a36 fe9c9717
4c042a36 fe9c9717 02000000 00000000 808ae0ed 1c000000 00f90295 00000000
2a000000 00000000 00000000 00000000 01010000 00000000
```

A record that belongs to a lifecycle depends on other records: a `TRADE` correction names the sequence of its original, and an `MBO` change names an order that the order book holds. After you change such a record, check the stream with the state rules described in [State and recovery](STATE-AND-RECOVERY.md). The pages of [Record types](records/INDEX.md) show the fields of every record type.

## Check a codec against the conformance files

The conformance files are [all-records.nwt](files/samples/all-records.nwt) and [all-records.zst.nwt](files/samples/all-records.zst.nwt). Both hold the same 47 records, one or more of every record type except `FRAME_SUMMARY`: the first with raw frames, the second with Zstandard frames. In the kit they are in `fixtures/golden/`, with the single records in `fixtures/golden/records/` and the invalid containers in `fixtures/golden/malformed/`. The steps below use `EX` for a reference codec and `YOURS` for the program under test.

1. **Read the raw file.** Print every field in the format of `read` and compare with the reference output. The two reports are identical.

   ```bash
   EX read fixtures/golden/all-records.nwt > work/reference-fields.txt
   YOURS read fixtures/golden/all-records.nwt > work/your-fields.txt
   cmp work/reference-fields.txt work/your-fields.txt
   ```
2. **Read the Zstandard file.** It decodes to the same report.

   ```bash
   YOURS read fixtures/golden/all-records.zst.nwt > work/your-zstd-fields.txt
   cmp work/reference-fields.txt work/your-zstd-fields.txt
   ```
3. **Write the raw file.** Re-encode the records you read: the same metadata bytes, stream ID and creation time, raw `DATA` frames of 3 records each, then `INDEX` and `END`. The output is byte-identical to the conformance file.

   ```bash
   YOURS read fixtures/golden/all-records.zst.nwt work/your-again.nwt > /dev/null
   cmp work/your-again.nwt fixtures/golden/all-records.nwt
   ```
4. **Write Zstandard frames.** Compare decoded content, not compressed bytes: the compressed bytes depend on the version of the Zstandard library.

   ```bash
   YOURS write-golden work/your-zstd.nwt --zstd
   EX read work/your-zstd.nwt | cmp - work/reference-fields.txt
   ```
5. **Encode single records.** Each `fixtures/golden/records/NNN-label.bin` is one encoded record, and the `.json` file beside it holds its field values. Encode the values and compare the bytes; decode the bytes and compare the values.

   ```bash
   EX decode-record fixtures/golden/records/001-def-equity.bin
   ```
6. **Reject invalid input.** Every file in `fixtures/golden/malformed/` has one defect and is valid in every other respect, so a reader that skips that one check accepts it. A conforming reader exits with a non-zero status on each of them.

   ```bash
   for f in fixtures/golden/malformed/*.nwt; do EX read "$f" > /dev/null 2>&1 && echo "accepted: $f"; done
   ```

   The loop prints nothing when every file is rejected.
7. **Validate what you write.** Run [validate](tools/validate.md) on containers your writer produces. It applies the structural checks and the state rules to every record.

## Extend the schema

The schema file `schemas/records.json` is the single description of the record layouts. It has three parts: `header`, the ten fields of the 48-byte record header; `level`, the fields of one depth level; and `schemas`, one entry per record type. An entry gives the type number, the name, the schema version, the fixed size, the fields in wire order with width and signedness, the names of the texts, and the rules the codecs enforce: `enums`, `masks`, `text_limits` and `text_exact`. This is the entry for `BOOK_DELTA`:

<!-- nwt-file: schemas/records.json lines=1232-1300 -->

The catalogs are the example records the codecs write. `fixtures/catalog-golden.json` with `fixtures/manifest-golden.json` is the source of the conformance files, and `fixtures/catalog.json` with `fixtures/manifest.json` is the source of the container that `write` produces.

The four codecs take these files in two ways:

- Rust includes them at compile time with `include_str!`, and C# embeds them as resources through `NwtExample.csproj`.
- Python and C++ use generated copies, `examples/python/example_data.py` and `examples/cpp/example_data.hpp`, so that each runs from its own folder.

To change a layout or add a record:

1. Edit `schemas/records.json`, and add or change the catalog entries that use the layout.
2. Regenerate the embedded copies:

   ```bash
   python3 tools/sync_embedded_data.py
   ```
3. Rebuild the Rust, C# and C++ codecs as in [Build and run](#build-and-run).
4. Regenerate the files under `fixtures/`. This step needs `libzstd`.

   ```bash
   python3 tools/generate_fixtures.py
   ```
5. Compare the four codecs again as in [Check a codec against the conformance files](#check-a-codec-against-the-conformance-files).

Rules that hold across records, such as the order book transitions, belong to `examples/python/market_state.py`, which reads the decoded records.

A layout that is in use never changes. The [Specification](SPECIFICATION.md) fixes the layout of every pair of record type and schema version: a new field needs a new schema version, and a private record type takes a number from 32,768 to 65,534 and its own `spec_uri` in the manifest.
