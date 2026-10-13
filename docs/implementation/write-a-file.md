# Write a file

![Five steps of a writer: open the container, check each record, fill a frame, seal the frame, close the container, with the bytes each step writes](../diagrams/write-path.svg "The steps of a writer and the bytes each step writes")

1. Build the manifest: the dataset name, the producer, the profile, the clock `posix-ns`, the publishers and one schema entry for every record type you write. Declare `BOOK_DELTA` with `required` set to `true` and `FRAME_SUMMARY` with `required` set to `false`.
2. Choose a stream ID of 16 random bytes that are not all zero, and the creation time in nanoseconds.
3. Write the container header and the metadata: the `MANIFEST` element and, when you have one, the `PROVENANCE` element.
4. Give every record the next sequence of its publisher and channel, starting at 1, and encode it. Collect records into a frame until the frame is full, then write the `DATA` frame with its record count, its time bounds and the CRC-32C of the raw payload. Store the Zstandard form only when it is smaller than the raw payload.
5. Close the container: write the last `DATA` frame, the `INDEX` frames with one 40-byte entry per `DATA` frame, and `END` with the index offset, the totals and the status.

The result is a container that [validate](../tools/validate.md) accepts.

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
