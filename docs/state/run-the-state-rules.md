# Run the state rules

`examples/python/market_state.py` reads a container, applies every record to a `MarketState` and prints a summary of the final state:

```bash
python3 examples/python/market_state.py fixtures/golden/all-records.nwt
```

```text
{
  "definitions": 2,
  "trade_ids": 1,
  "bars": 1,
  "valid_mbo_books": 0,
  "gap_events": 1
}
```

For the container of the second table:

```bash
python3 examples/python/nwt_example.py write work/types-1-9.nwt
python3 examples/python/market_state.py work/types-1-9.nwt
```

```text
{
  "definitions": 8,
  "trade_ids": 2,
  "bars": 2,
  "valid_mbo_books": 1,
  "gap_events": 4
}
```

[validate](../tools/validate.md) runs the same rules on any container and names the record that breaks one. A container that holds order records without the definition of their instrument fails on its first record:

```bash
python3 tools/nwt.py extract fixtures/real-market/equity-orders.nwt work/orders-only.nwt --type MBO
python3 tools/nwt.py validate work/orders-only.nwt
```

```text
NWT error: record 1 (MBO, sequence 1): definition must precede data
```

From Python, pass decoded records to `market_state.validate`, or call `MarketState.apply` for each record and `MarketState.finish` at the end of the container:

```python
import sys
sys.path.insert(0, "examples/python")
import market_state
import nwt_example as nwt

with open("fixtures/golden/all-records.nwt", "rb") as f:
    reader = nwt.open_reader(f)
    publishers = {p["id"] for p in reader.manifest["publishers"]}
    state = market_state.MarketState(publishers)
    for record in nwt.complete_records(reader):
        state.apply(record)             # raises ValueError with the name of the broken rule
    print(state.finish())               # also checks that no snapshot is open
```

```text
{'definitions': 2, 'trade_ids': 1, 'bars': 1, 'valid_mbo_books': 0, 'gap_events': 1}
```
