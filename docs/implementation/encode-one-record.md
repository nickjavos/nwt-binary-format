# Encode one record

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

A record that belongs to a lifecycle depends on other records: a `TRADE` correction names the sequence of its original, and an `MBO` change names an order that the order book holds. After you change such a record, check the stream with the state rules described in [State and recovery](../STATE-AND-RECOVERY.md). The pages of [Record types](../records/INDEX.md) show the fields of every record type.
