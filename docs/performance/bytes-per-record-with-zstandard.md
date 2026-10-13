# Bytes per record with Zstandard

NWT compresses each `DATA` frame separately. The chart compares the store file that `nwt repack` writes with the CSV files compressed whole, both with Zstandard level 3. Zstandard removes most of the redundancy of decimal text, so the two results are close: NWT is smaller for four samples and CSV for two. The NWT figure includes the manifest, the `INDEX` and the `FRAME_SUMMARY` records, a fixed part that weighs more in a smaller file.

The two forms are read differently. A reader of a store file decompresses only the frames it needs, and a compressed CSV file is decompressed from its first byte.

<!-- nwt-chart: bytes-per-record-compressed -->

| Sample | CSV, Zstandard | NWT, Zstandard frames |
|---|---|---|
| `equity-quotes` | 19.6 | 14.8 |
| `equity-orders` | 23.5 | 20.4 |
| `equity-bars` | 25.3 | 30.1 |
| `option-best-quotes` | 27.6 | 22.8 |
| `statistics` | 23.3 | 21.2 |
| `corporate-actions-us` | 69.4 | 69.6 |
