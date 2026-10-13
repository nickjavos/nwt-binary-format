# NWT developer guide — Rust, Python, C#, C++

## What is included

This kit holds NWT 1.1 and four example programs that encode and decode **all 22 standard record types and every field**. There are 48 catalog scenarios, an individual binary and JSON file for each, a complete multi-frame container, a shared field-layout schema, and a Python tool for inspecting, checking, converting, repacking and querying files.

The examples take their numbers as **decimal strings** in a dictionary. This keeps the full signed and unsigned 64-bit range through JSON in every language. The wire output is compact binary integers, not JSON. The shared schema (`schemas/records.json`) gives field order, width and signedness. Each language performs the binary encoding and decoding in its own source. No language passes a price, quantity or timestamp through floating point.

These programs are teaching codecs. They are not optimised production libraries and they are not complete SDKs.

## Honest status

Read this before you rely on anything.

| Item | State |
|---|---|
| Python codec and tools | Written and run against the golden files. |
| C++ codec | Written and run against the golden files. |
| C# codec | Written. See the verification report for what was run. |
| Rust codec | **Written but not compiled or run.** The source follows the same contract. Build it and run it against the golden files before you trust it. |
| Zstd (codec 1) | Needs the system `libzstd` in Python, C# and C++ (loaded or linked at run time). In Rust it is the `zstd` crate, on by default. Without the library, raw files still work and codec 1 fails with a clear error. |
| Store features, converters, semantic checks | **Python only.** The `nwt` tool, the converters and `market_state.py` have no Rust, C# or C++ version. |
| Live sockets, reconnect service | Not included. |
| Performance | No measured figures are claimed. The `bench` command exists so you can measure on your own machine. |

The details of what was actually executed are in the [verification report](VERIFICATION.md).

## Quick start

Requirements: Python 3.10 or newer, Rust and Cargo, the .NET 10 SDK, a C++20 compiler, and the Zstd library if you want codec 1 (`libzstd`; on macOS `brew install zstd`, on Debian `apt install libzstd-dev`). Rust dependencies are pinned in `Cargo.lock`. C++ includes nlohmann/json 3.12.0 and its MIT licence, so no package manager is needed. Python and C# use their standard libraries.

Run these from the kit root:

```sh
mkdir -p work

# Python
python3 examples/python/nwt_example.py write-v11 work/python.nwt
python3 examples/python/nwt_example.py read work/python.nwt work/python-roundtrip.nwt

# Rust (not compiled or run in this release)
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example write-v11 work/rust.nwt
examples/rust/target/debug/nwt-example read work/rust.nwt work/rust-roundtrip.nwt

# C# / .NET
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll write-v11 work/csharp.nwt
dotnet work/csharp/NwtExample.dll read work/csharp.nwt work/csharp-roundtrip.nwt

# C++20 with Zstd (Clang or GCC)
c++ -std=c++20 -O2 -DNWT_ZSTD -I/opt/homebrew/include examples/cpp/main.cpp -o work/nwt-cpp -L/opt/homebrew/lib -lzstd
# C++20 without Zstd: leave out -DNWT_ZSTD and -lzstd
work/nwt-cpp write-v11 work/cpp.nwt
work/nwt-cpp read work/cpp.nwt work/cpp-roundtrip.nwt
```

Adjust the include and library paths for your system. `examples/cpp/CMakeLists.txt` finds Zstd by itself and builds without it when it is missing. In Rust, `cargo build --no-default-features` leaves Zstd out. On Windows, use the `.exe` suffix and Windows path separators. With MSVC, compile with `/std:c++20 /EHsc /utf-8`; this kit does not claim MSVC was tested.

Add `--zstd` to `write-v11` to write Zstd-compressed DATA frames.

## Commands supported by every example

| Command | Result |
|---|---|
| `write FILE` | Write the 1.0 conformance container (types 1–9, 49 scenarios, `minor` 0) |
| `write-v11 FILE [--zstd]` | Write the 22-type conformance container (`minor` 1); `--zstd` compresses DATA frames |
| `read FILE [REENCODED_FILE]` | Validate the container, print every field of every record, and optionally write the records again with the deterministic example framing |
| `record TYPE FILE` | Encode the first catalog example of the type as one standalone raw record |
| `decode-record FILE` | Decode one raw record and print all fields, texts and depth levels |
| `to-json FILE [--pretty]` | Print one JSON line per record; `--pretty` writes decimals and ISO-8601 times |
| `to-csv FILE TYPE [--pretty]` | Print the records of one type as CSV; type 5 is refused |
| `bench FILE` | Time reading a file and report records per second |

`record` does not emit a container. Its header sequence is preserved from the full scenario, so a standalone record can depend on earlier records. This is deliberate, for field-level testing. The exact formats of `to-json` and `to-csv` are in `fixtures/v1.1/FORMAT-NOTES.md`.

The report of `read` is an inspection format, not an interchange format: `record_number.field=decimal_value`, and `record_number.levels.index.field=value` for depth levels. UTF-8 text is printed as it is, so text that contains a newline spans several lines. Compare binary data or decoded values for arbitrary input, not report lines.

## Read the code in this order

1. `encode_fields` and its equivalents: exact widths, signedness, little-endian conversion.
2. `encode_record`: fixed payload, variable text and levels, derived lengths, padding.
3. `decode_record`: bounds, exact record sizes, UTF-8, reserved fields, padding, the enum, mask and text-limit rules.
4. `frame`: DATA, INDEX and END headers and checksums.
5. `write_container`: metadata, batching, index entries, totals.
6. `read_container`: framing, checksums, sequences, timestamp ranges, index verification, the `minor` rule.
7. The Zstd step: the frame header check of `fixtures/v1.1/FORMAT-NOTES.md` §7, then decompression.
8. Python `market_state.py`: trade lifecycle, book mutations, snapshots, gaps, definitions, and the semantic rules of the new types.

The Rust version uses fallible results and explicit little-endian conversion. The C++ version uses bounded byte spans and `std::bit_cast` only to read signed integers; it never casts a network buffer to a native struct. C# uses `BinaryPrimitives` and strict UTF-8. Python uses explicit integer byte order.

## The Python tools

The `nwt` tool lives in `tools/nwt.py`. It needs only the Python standard library, plus `libzstd` for Zstd files. It is the only place the store features exist.

```sh
python3 tools/nwt.py inspect FILE      # header, manifest, frame table, record counts
python3 tools/nwt.py validate FILE     # structure, semantic rules, summaries, ordering claim
python3 tools/nwt.py cat FILE          # records as JSON Lines
python3 tools/nwt.py query FILE ...    # read only the frames that can match
python3 tools/nwt.py repack IN OUT     # rewrite as a store file
python3 tools/nwt.py convert KIND SRC OUT
```

See [TOOLS.md](TOOLS.md) for every command and option, [STORE.md](STORE.md) for the store profile, and [REAL-DATA.md](REAL-DATA.md) and [REAL-DATA-MARKET.md](REAL-DATA-MARKET.md) for the converters and the real fixtures.

## Editing a field and producing a raw record

The fragments go inside the corresponding example, where its codec functions and schema data are available. They edit a sample trade without inventing a new serialisation layout.

### Python

```python
from copy import deepcopy
trade = deepcopy(next(r for r in CATALOG if r['type'] == 1))
trade['fields']['price'] = '124250000000'     # 124.25
trade['fields']['quantity'] = '2500000000'   # 2.5
wire = encode_record(trade)
assert decode_record(wire)['fields']['quantity'] == '2500000000'
```

### Rust

```rust
let mut trade = records.iter().find(|r| r.r#type == 1).unwrap().clone();
trade.fields.insert("price".into(), "124250000000".into());
trade.fields.insert("quantity".into(), "2500000000".into());
let wire = encode_record(&trade, &ss)?;
let restored = decode_record(&wire, &ss)?;
assert_eq!(restored.fields["quantity"], "2500000000");
```

### C#

```csharp
var trade = records.First(r => r.type == 1);
trade.fields["price"] = "124250000000";
trade.fields["quantity"] = "2500000000";
byte[] wire = EncodeRecord(trade);
Need(DecodeRecord(wire).fields["quantity"] == "2500000000", "round trip");
```

### C++

```cpp
J trade = *std::find_if(records.begin(), records.end(),
    [](const auto& r) { return r.at("type") == 1; });
trade["fields"]["price"] = "124250000000";
trade["fields"]["quantity"] = "2500000000";
Bytes wire = encode_record(trade);
need(decode_record(wire).at("fields").at("quantity") == "2500000000",
     "round trip");
```

These fragments are written against the current source layout and have not been compiled as separate snippets. The [feed cookbook](FEED-COOKBOOK.md) gives the fields and commands for every other type. Editing a lifecycle record can require matching changes to the record it refers to. Run the semantic check before you treat edited data as a valid market stream.

## State reconstruction and recovery

```sh
python3 examples/python/market_state.py fixtures/v1.1/all-records.nwt
python3 examples/python/market_state.py fixtures/all-records.nwt
```

The second command replays the 1.0 vector. Its final state has eight definitions, two trade IDs, two bar intervals, one valid MBO book and four GAP events. One trade is canceled and stays in the lifecycle history. A snapshot is built privately and committed only at SNAPSHOT_END. A GAP discards both the current and the working state of its channel. Quote, aggregate depth, MBO and status recover separately.

The state example changes in-memory state as it checks each record. If a call fails, **discard that state instance**. It has no transactional rollback, no durable storage, no global source-gap completeness check and no production state limits. A production consumer should stage a whole frame before it exposes the changes, and use durable checkpoints that suit its application. See [state and recovery](STATE-AND-RECOVERY.md).

## Coverage and deliberate boundaries

| Feature | Python | Rust | C# | C++ |
|---|---|---|---|---|
| All 22 standard types and all fields | Yes | Written, not run | Yes | Yes |
| Variable UTF-8, depth levels, signed and unsigned extremes | Yes | Written, not run | Yes | Yes |
| Raw DATA, INDEX, END and CRC32C | Yes | Written, not run | Yes | Yes |
| Zstd codec (needs the system library) | Yes | Written, not run | Yes | Yes |
| `to-json`, `to-csv`, `bench` | Yes | Written, not run | Yes | Yes |
| Sequence, count, time-range and index validation | Yes | Written, not run | Yes | Yes |
| Semantic rules and market state | Yes | No | No | No |
| `nwt` tool: validate, query, repack, convert | Yes | No | No | No |
| Store profile writer (INDEX and FRAME_SUMMARY) | Yes | No | No | No |
| Live sockets, reconnect service | No | No | No | No |

The example readers are built for the files in this kit. They read whole files into memory, are not streaming readers, and have no capability negotiation beyond the checks in the source. These limits belong to the example programs, not to the NWT wire format. They are **not production SDKs and not complete core-reader implementations**.

The example writers use a fixed stream ID and creation time to reproduce a golden vector. Do not use that identity for changed data or for production files. Generate a new random nonzero stream ID whenever the bytes differ. Keep a stream ID only for a byte-identical retransmission.

A structural check does not replace every enum and business rule. In this kit the Python tools and `market_state.py` carry the semantic rules. The other three languages decode the numeric fields faithfully but do not rebuild or check a market state.

## Re-run the cross-language comparison

After the builds above:

```sh
python3 tests/interop.py --rust examples/rust/target/debug/nwt-example --cpp work/nwt-cpp --csharp dotnet work/csharp/NwtExample.dll --output work/test-results
python3 tests/test_contract.py
```

The comparison writes every container with every language, reads it with every language, requires byte-identical raw re-encoding, compares the field reports record by record, exercises each type's standalone writer, and checks the malformed files in `fixtures/v1.1/malformed/`. Zstd output is compared by decoded content, not by compressed bytes, because the bytes depend on the library version. The saved [verification report](VERIFICATION.md) records what was actually run.

## Changing the shared catalog

`fixtures/catalog.json` (types 1–9) and `fixtures/catalog-v1.1.json` (types 10–22) are the human-readable record sources. `schemas/records.json` is the layout source. Rust and C# embed these files at compile time. Python and C++ keep embedded copies so they run alone. After an intentional change, run `python3 tools/sync_embedded_data.py`, rebuild, run `python3 tools/generate_fixtures.py`, and run the checks. Editing a descriptor does not change the normative NWT schema. A wire-layout change needs a new, explicit specification version.

## References

- [Python integer byte conversion](https://docs.python.org/3/library/stdtypes.html#int.to_bytes).
- [Rust u64 byte conversion](https://doc.rust-lang.org/std/primitive.u64.html#method.from_le_bytes).
- [C# BinaryPrimitives](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.binary.binaryprimitives).
- [C++ serialisation guidance](https://isocpp.org/wiki/faq/serialization).
- [nlohmann/json 3.12.0 release and checksum](https://github.com/nlohmann/json/releases/tag/v3.12.0).
- [Zstandard](https://facebook.github.io/zstd/) and [RFC 8878](https://www.rfc-editor.org/rfc/rfc8878).
