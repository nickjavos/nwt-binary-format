# From a value to bytes

This section follows one trade from the sample [equity-orders.nwt](files/samples/equity-orders.nwt) from its values to its bytes and back. The trade is the record with sequence 18: 180 shares at 177.03, with the seller as the aggressor.

The JSON Lines view of the sample shows the values. Every number is the stored integer, written as a decimal string:

<!-- nwt-file: fixtures/real-market/equity-orders.jsonl lines=18-18 -->

The first ten fields are the record header. The price 177.03 is stored as 177030000000 and the quantity 180 as 180000000000, because both are scaled by 10⁹. The timestamps count nanoseconds since 1970-01-01 UTC, so 1758009600256830296 is 2025-09-16 08:00:00.256830296.

This program takes the same record out of the sample and prints every field with its offset and its bytes. Run it from the kit root:

```bash
mkdir -p work
```

```python
import sys
sys.path.insert(0, "examples/python")
import nwt_example as nwt

with open("fixtures/real-market/equity-orders.nwt", "rb") as f:
    frames = nwt.open_reader(f).frames()
    # record_type is the 2-byte field at offset 4 of every record; 1 is TRADE
    raw = next(r for _, records in frames for r in records if nwt.get(r, 4, 2) == 1)

record = nwt.decode_record(raw)
offset = 0
for field in nwt.SCHEMA["header"] + nwt.S[1]["fields"]:
    width = field["bytes"]
    name = field["name"]
    print(f"{offset:2}  {raw[offset:offset + width].hex():16}  {name} = {record['fields'][name]}")
    offset += width

assert nwt.encode_record(record) == raw
open("work/trade.bin", "wb").write(raw)
```

```text
 0  58000000          record_bytes = 88
 4  0100              record_type = 1
 6  01                schema_version = 1
 7  00                flags = 0
 8  02000000          publisher_id = 2
12  00000000          channel_id = 0
16  932d000000000000  instrument_id = 11667
24  58eb08c76ab46518  ts_event = 1758009600256830296
32  2a6b0bc76ab46518  ts_recv = 1758009600256994090
40  1200000000000000  sequence = 18
48  806dcf3729000000  price = 177030000000
56  0008d6e829000000  quantity = 180000000000
64  0100000000000000  trade_id = 1
72  0000000000000000  original_sequence = 0
80  01                action = 1
81  02                aggressor = 2
82  0000              conditions = 0
84  00000000          reserved = 0
```

The record is 88 bytes: 48 bytes of header and 40 bytes of trade fields. Every integer is little-endian, so its lowest byte comes first: `58000000` is 0x58, which is 88. The program finds the trade by looking at offset 4 of each record, without decoding anything else.

The function of the Python reference codec that packs these fields is short. It walks the field list of the schema and writes each value with the width and the sign that the schema gives:

<!-- nwt-file: examples/python/nwt_example.py lines=81-89 -->

The program saved the 88 bytes as `work/trade.bin`. The `decode-record` command of the reference codec reads them back:

```bash
python3 examples/python/nwt_example.py decode-record work/trade.bin
```

```text
1.record_bytes=88
1.record_type=1
1.schema_version=1
1.flags=0
1.publisher_id=2
1.channel_id=0
1.instrument_id=11667
1.ts_event=1758009600256830296
1.ts_recv=1758009600256994090
1.sequence=18
1.price=177030000000
1.quantity=180000000000
1.trade_id=1
1.original_sequence=0
1.action=1
1.aggressor=2
1.conditions=0
1.reserved=0
```

[Field reference](../FIELD-REFERENCE.md) · [Implementation guide: Encode one record](../implementation/encode-one-record.md) · [Market data samples](../REAL-DATA-MARKET.md)
