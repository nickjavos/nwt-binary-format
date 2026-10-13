# Convert a file

The converter, `tools/nwt_convert_reference.py`, is a Python script that uses only the standard library. This procedure builds the `venues.nwt` sample from the saved rows of the ISO 10383 list.

1. Open a terminal in the kit root.
2. Run the converter with a kind, a source file and an output file:

   ```bash
   python3 tools/nwt_convert_reference.py mic fixtures/real/source/ISO10383_MIC.csv venues.nwt --retrieved 2026-10-13
   ```

   The converter writes `venues.nwt` and prints the provenance it stored in the file, as JSON. The record counts are under `records`:

   ```text
     "records": {
       "VENUE_DEF": 100
     },
     "retrieved": "2026-10-13",
   ```
3. Check the file with the `nwt` command:

   ```bash
   python3 tools/nwt.py inspect venues.nwt
   ```

   The last lines of the output confirm a complete file with 100 records:

   ```text
   end data_frames=1 records=100 status=normal
   records VENUE_DEF 100
   ```
4. Print the records as JSON Lines. Add `--pretty` for decimal prices and ISO 8601 timestamps.

   ```bash
   python3 examples/python/nwt_example.py to-json venues.nwt
   ```

The same converter runs through two other entry points, which take the same arguments:

```bash
python3 tools/nwt_convert.py mic fixtures/real/source/ISO10383_MIC.csv venues.nwt --retrieved 2026-10-13
```

```bash
python3 tools/nwt.py convert mic fixtures/real/source/ISO10383_MIC.csv venues.nwt --retrieved 2026-10-13
```

The other commands of `tools/nwt.py` are described in [The nwt command](../TOOLS.md).
