# convert

Converts a source file, such as a CSV export or a public symbol directory, to a container.

```bash
python3 tools/nwt.py convert KIND SRC OUT [--name value]... [--flag]...
```

| Argument | Meaning |
|---|---|
| `KIND` | Format of the source. An unknown kind fails with the list of the known kinds. |
| `SRC` | Source file |
| `OUT` | Container to write |
| `--name value` | Option of the converter, passed through as text. `--name=value` is equivalent. |
| `--flag` | Option of the converter without a value |

The converters are Python modules beside the tool. The kinds for reference data are `mic`, `nasdaqlisted`, `otherlisted`, `options`, `csv-secmaster` and `csv-corporate-actions`; their options are in [Reference data samples](../REAL-DATA.md). The kinds for market data are `csv-definition`, `csv-mbo`, `csv-mbp1`, `csv-mbp10`, `csv-cmbp1`, `csv-ohlcv` and `csv-statistics`; their options are in [Market data samples](../REAL-DATA-MARKET.md).

On success the command prints a summary of the conversion as JSON on standard output: the policy it applied, the checksum of the source and the number of records of each type. The output carries the same facts in its `PROVENANCE`.

This example converts the ISO 10383 list of market identifier codes and reproduces the sample [venues.nwt](files/samples/venues.nwt) byte for byte:

```bash
python3 tools/nwt.py convert mic fixtures/real/source/ISO10383_MIC.csv work/venues.nwt --retrieved 2026-10-13 > work/venues.provenance.json
cmp work/venues.nwt fixtures/real/venues.nwt
python3 tools/nwt.py validate work/venues.nwt
```

```text
valid records=100 data_frames=1 summaries=0 ordering=none
```
