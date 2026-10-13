# Samples

Each sample is an `.nwt` file. Where a `.jsonl` file is listed, it is the JSON Lines view of the same sample: one JSON object per record, in file order.

| File | Record types | Contents |
|---|---|---|
| [venues.nwt](files/samples/venues.nwt)<br>[venues.jsonl](files/samples/venues.jsonl) | `VENUE_DEF` | 100 venues from the ISO 10383 market identifier code list: operating venues and market segments, active and expired |
| [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt)<br>[listings-nasdaq.jsonl](files/samples/listings-nasdaq.jsonl) | `LISTING`, `SYMBOL_MAP` | 100 securities from the Nasdaq-listed symbol directory, each as one `LISTING` followed by one `SYMBOL_MAP` |
| [listings-other.nwt](files/samples/listings-other.nwt)<br>[listings-other.jsonl](files/samples/listings-other.jsonl) | `LISTING`, `SYMBOL_MAP` | 100 securities from the symbol directory of the other US exchanges, each as one `LISTING` followed by one `SYMBOL_MAP` |
| [options.nwt](files/samples/options.nwt)<br>[options.jsonl](files/samples/options.jsonl) | `OPTION_DEF` | 100 option series from the option series directory |
| [secmaster-us.nwt](files/samples/secmaster-us.nwt)<br>[secmaster-us.jsonl](files/samples/secmaster-us.jsonl) | `SECURITY_DEF` | 28 US listings from a security-master export |
| [secmaster-global.nwt](files/samples/secmaster-global.nwt)<br>[secmaster-global.jsonl](files/samples/secmaster-global.jsonl) | `SECURITY_DEF` | 195 listings in 25 countries from a security-master export |
| [corporate-actions-us.nwt](files/samples/corporate-actions-us.nwt)<br>[corporate-actions-us.jsonl](files/samples/corporate-actions-us.jsonl) | `SECURITY_DEF`, `CORPORATE_ACTION` | 864 corporate-action events from a US export and the 777 `SECURITY_DEF` records that describe their listings |
| [corporate-actions-global.nwt](files/samples/corporate-actions-global.nwt)<br>[corporate-actions-global.jsonl](files/samples/corporate-actions-global.jsonl) | `SECURITY_DEF`, `CORPORATE_ACTION` | 500 corporate-action events from a global export and the 442 `SECURITY_DEF` records that describe their listings |

The first two records of `venues.jsonl` are shown below. Every integer is written as a decimal string, so 64-bit values survive any JSON parser. `18446744073709551615` is the null timestamp.

<!-- nwt-file: fixtures/real/venues.jsonl lines=1-2 -->
