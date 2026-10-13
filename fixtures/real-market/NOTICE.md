# Notice: licensed market data

The samples in this folder are converted from licensed market-data exports. The data is not public.

- Receiving the kit does not give you a license to this data. Check the license under which the data was obtained before you redistribute these files or anything converted from them.
- The samples are small: the first few hundred or few thousand rows of a source file, and the one-minute bars of one symbol for one day. The source rows are in `source/`, bytes unchanged.
- The samples are for learning the format. Do not use them for trading, pricing or any other decision.

`SHA256SUMS` lists the SHA-256 of every source file and every sample. `rebuild.sh` rebuilds the samples from `source/`. The Market data samples document describes each sample and the conversion rules.
