# Size at one million records

The larger file shows the same comparison for 1,000,000 records. After one instrument definition it holds `QUOTE` records of 96 bytes and `TRADE_QUOTE` records of 120 bytes. A file with raw frames is the records themselves, a 64-byte header for each frame, the manifest and the `INDEX`.

<!-- nwt-chart: size-by-encoding -->

| Encoding | Size, MB |
|---|---|
| CSV | 123 |
| JSON Lines | 410 |
| NWT, raw frames | 96 |
