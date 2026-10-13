# Converter kinds

The first argument selects the source format.

| Kind | Source | Records written |
|---|---|---|
| `mic` | ISO 10383 market identifier code list, CSV | One `VENUE_DEF` per row |
| `nasdaqlisted` | Nasdaq-listed symbol directory, pipe-separated text | One `LISTING` and one `SYMBOL_MAP` per row |
| `otherlisted` | Symbol directory of the other US exchanges, pipe-separated text | One `LISTING` and one `SYMBOL_MAP` per row |
| `options` | Option series directory, pipe-separated text | One `OPTION_DEF` per row |
| `csv-secmaster` | Security-master export, CSV | One `SECURITY_DEF` per row |
| `csv-corporate-actions` | Corporate-actions export, CSV | One `CORPORATE_ACTION` per row, preceded by a `SECURITY_DEF` when the listing is new or its facts changed |

Two options follow the output file:

| Option | Meaning |
|---|---|
| `--dataset NAME` | The dataset name in the manifest. The defaults are `REAL.ISO10383.MIC`, `REAL.SYMDIR.NASDAQLISTED`, `REAL.SYMDIR.OTHERLISTED`, `REAL.SYMDIR.OPTIONS`, `REAL.SECMASTER` and `REAL.CORPACT`. |
| `--retrieved YYYY-MM-DD` | The date on which the source file was retrieved. It is stored in the provenance. |

The four public sources are published at these addresses:

| Kind | Published file |
|---|---|
| `mic` | `https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv` |
| `nasdaqlisted` | `https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt` |
| `otherlisted` | `https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt` |
| `options` | `https://www.nasdaqtrader.com/dynamic/SymDir/options.txt` |

To convert a whole public file, download it and pass it as the source file. A row with the wrong number of fields stops the conversion, so cut a partial download at the end of a line.
