# Samples

Each sample is an `.nwt` file. Where a `.jsonl` file is listed, it is the JSON Lines view of the same sample: one JSON object per record, in file order. In every sample, the definition of an instrument precedes its first record.

| File | Record types | Contents |
|---|---|---|
| [equity-definitions.nwt](files/samples/equity-definitions.nwt)<br>[equity-definitions.jsonl](files/samples/equity-definitions.jsonl) | `INSTRUMENT_DEF` | 200 instrument definitions of one equities venue |
| [equity-orders.nwt](files/samples/equity-orders.nwt)<br>[equity-orders.jsonl](files/samples/equity-orders.jsonl) | `INSTRUMENT_DEF`, `MBO`, `TRADE` | The first 2,000 order-level rows of one equity on 16 September 2025: 1,818 `MBO` records (1 CLEAR, 1,420 ADD, 39 MODIFY, 358 DELETE) and 123 `TRADE` records |
| [equity-deltas.nwt](files/samples/equity-deltas.nwt)<br>[equity-deltas.jsonl](files/samples/equity-deltas.jsonl) | `INSTRUMENT_DEF`, `BOOK_DELTA` | Price-level changes derived from the same 2,000 rows: 1,818 `BOOK_DELTA` records (1 CLEAR, 1,599 SET, 218 DELETE) |
| [equity-quotes.nwt](files/samples/equity-quotes.nwt)<br>[equity-quotes.jsonl](files/samples/equity-quotes.jsonl) | `INSTRUMENT_DEF`, `QUOTE`, `TRADE_QUOTE` | The first 2,000 top-of-book rows of the same equity and day: 2,000 `QUOTE` and 476 `TRADE_QUOTE` records |
| [equity-bars.nwt](files/samples/equity-bars.nwt)<br>[equity-bars.jsonl](files/samples/equity-bars.jsonl) | `INSTRUMENT_DEF`, `BAR` | The 921 one-minute bars of the same equity and day |
| [futures-orders.nwt](files/samples/futures-orders.nwt)<br>[futures-orders.jsonl](files/samples/futures-orders.jsonl) | `INSTRUMENT_DEF`, `MBO` | The order book of one futures contract at the start of a session: 2,000 `MBO` records (1 CLEAR, 1,999 ADD) |
| [option-definitions.nwt](files/samples/option-definitions.nwt)<br>[option-definitions.jsonl](files/samples/option-definitions.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF` | 500 definitions from a consolidated options feed: 130 underlying equities and 370 options, each option with an `OPTION_DEF` |
| [option-best-quotes.nwt](files/samples/option-best-quotes.nwt)<br>[option-best-quotes.jsonl](files/samples/option-best-quotes.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF`, `BEST_QUOTE` | 2,000 consolidated best quotes of options, with the venue of each side, and 641 `INSTRUMENT_DEF` and 641 `OPTION_DEF` records |
| [depth-10.nwt](files/samples/depth-10.nwt)<br>[depth-10.jsonl](files/samples/depth-10.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF`, `BOOK_SNAPSHOT` | 500 book snapshots of 1 to 10 levels for options on futures, with 199 `INSTRUMENT_DEF` and 187 `OPTION_DEF` records |
| [statistics.nwt](files/samples/statistics.nwt)<br>[statistics.jsonl](files/samples/statistics.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF`, `STATISTICS` | 1,831 statistics of one derivatives venue: 1,809 opening prices and 22 preliminary settlement prices |

The first three records of `equity-quotes.jsonl` are the `INSTRUMENT_DEF`, a `QUOTE` with an absent bid side, and a `QUOTE` with both sides. Every integer is written as a decimal string. Prices and quantities are scaled by 10⁹, `-9223372036854775808` is the null price, and `18446744073709551615` is the null timestamp or quantity.

<!-- nwt-file: fixtures/real-market/equity-quotes.jsonl lines=1-3 -->
