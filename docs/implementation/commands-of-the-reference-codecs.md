# Commands of the reference codecs

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

[The nwt command](../TOOLS.md) prints the same JSON Lines as `to-json` and adds inspection, validation, filtering and store files. It is written in Python, as are the state rules in `examples/python/market_state.py` and the converters.
