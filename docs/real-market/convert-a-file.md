# Convert a file

The converter, `tools/nwt_convert_market.py`, is a Python script that uses only the standard library. This procedure builds the `equity-orders.nwt` and `equity-deltas.nwt` samples from the saved rows of an order-level export.

1. Open a terminal in the kit root.
2. Run the converter with a kind, a source file, an output file and the options:

   ```bash
   python3 tools/nwt_convert_market.py csv-mbo fixtures/real-market/source/xnas-itch_mbo_equities.csv equity-orders.nwt \
       --dataset REAL.XNAS.ITCH --definitions fixtures/real-market/source/xnas-itch_definition_equities.csv \
       --currency USD --quantity-unit share --emit-deltas equity-deltas.nwt
   ```

   The converter writes both files and prints the provenance it stored in `equity-orders.nwt`, as JSON. The record counts are under `records_written`, and the provenance of `equity-deltas.nwt` is under `deltas`:

   ```text
     "records_written": {
       "INSTRUMENT_DEF": 1,
       "MBO": 1818,
       "TRADE": 123
     },
   ```
3. Check the file with the `nwt` command:

   ```bash
   python3 tools/nwt.py inspect equity-orders.nwt
   ```

   The last lines of the output confirm a complete file with 1,942 records:

   ```text
   end data_frames=1 records=1942 status=normal
   records TRADE 123
   records MBO 1818
   records INSTRUMENT_DEF 1
   ```
4. Print the records as JSON Lines. Add `--pretty` for decimal prices and ISO 8601 timestamps.

   ```bash
   python3 examples/python/nwt_example.py to-json equity-orders.nwt
   ```

The same converter runs through two other entry points, which take the same arguments:

```bash
python3 tools/nwt_convert.py KIND SRC OUT --dataset NAME [--option value | --flag] ...
```

```bash
python3 tools/nwt.py convert KIND SRC OUT --dataset NAME [--option value | --flag] ...
```

The other commands of `tools/nwt.py` are described in [The nwt command](../TOOLS.md).
