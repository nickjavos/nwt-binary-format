# Notice: public reference files

The samples in this folder are converted from files that their publishers make available to the public. The terms of use of each publisher apply.

| Sample | Source file | Address |
|---|---|---|
| `venues` | ISO 10383 list of market identifier codes | `https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv` |
| `listings-nasdaq` | Symbol directory, Nasdaq-listed securities | `https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt` |
| `listings-other` | Symbol directory, securities listed on other exchanges | `https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt` |
| `options` | Symbol directory, option series | `https://www.nasdaqtrader.com/dynamic/SymDir/options.txt` |

Each sample holds the first 100 rows of its source file. The source rows are in `source/`, bytes unchanged, and `source/SHA256SUMS` lists their SHA-256. `rebuild.sh` rebuilds the samples from `source/`.

The samples are for learning the format. Do not use them for trading, pricing or any other decision.

The Reference data samples document describes each sample and the conversion rules.
