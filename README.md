# NWT Binary Format — developer kit

**NWT 1.1, draft.1.** Specification, working examples and tools for a binary market-data format. The examples cover **Rust, Python, C# and C++**. NWT is an independent format with 22 standard record types. Types 1–9 are the 1.0 types and keep their meaning. Types 10–22 are new in 1.1.

## Start here

1. [Full specification](docs/SPECIFICATION.md): normative byte layouts and semantics.
2. [Field reference](docs/FIELD-REFERENCE.md): every field, width, offset, unit and null, for all 22 types.
3. [Feed cookbook](docs/FEED-COOKBOOK.md): one worked example and four-language commands for each type.
4. [Implementation guide](docs/IMPLEMENTATION-GUIDE.md): build and run commands, code walkthrough, and what each language covers.
5. [State and recovery](docs/STATE-AND-RECOVERY.md): order, snapshots, trade lifecycle, gaps, and the state added in 1.1.
6. [Tools](docs/TOOLS.md): the `nwt` command for inspecting, checking, converting, repacking and querying files.
7. [Store profile](docs/STORE.md): how to write a file that is fast to query.
8. [Real data](docs/REAL-DATA.md) and [real market data](docs/REAL-DATA-MARKET.md): the converters and the real fixtures.
9. [Verification report](docs/VERIFICATION.md): what was executed, and what was not.
10. [Change log](docs/CHANGELOG.md).

## Record types

| Type | Name | Purpose |
|---:|---|---|
| 1 | TRADE | Trade print with new, correct and cancel |
| 2 | QUOTE | Best bid and ask |
| 3 | BAR | Completed OHLCV bar |
| 4 | MBO | Order-level book changes |
| 5 | BOOK_SNAPSHOT | Ranked aggregate book |
| 6 | INSTRUMENT_DEF | Instrument definition |
| 7 | STATUS | Trading status |
| 8 | GAP | Source discontinuity |
| 9 | SYSTEM | Heartbeat and diagnostics |
| 10 | VENUE_DEF | Trading venue, by market identifier code |
| 11 | OPTION_DEF | Option contract terms |
| 12 | LISTING | Symbol directory row |
| 13 | STATISTICS | Open, high, low, close, settlement, VWAP, volume, open interest |
| 14 | OPTION_ANALYTICS | Implied volatility and Greeks |
| 15 | BOOK_DELTA | Price-level change to the aggregate book |
| 16 | IMBALANCE | Auction imbalance |
| 17 | SYMBOL_MAP | Symbol over a time interval |
| 18 | TRADE_QUOTE | Trade with the top of book before it |
| 19 | BEST_QUOTE | Best quote with the venue of each side |
| 20 | FRAME_SUMMARY | Per-frame summary for selective reads |
| 21 | SECURITY_DEF | Security master with identifiers and key dates |
| 22 | CORPORATE_ACTION | Corporate-action event |

The synthetic conformance vectors are in `fixtures/` (the 1.0 set) and `fixtures/v1.1/` (the 22-type set, 48 records). Real examples are in `fixtures/real/`, `fixtures/real-market/` and `fixtures/real-reference/` where the converters have produced them.

## What is new in 1.1

- Thirteen record types, 10 to 22.
- An optional manifest property `ordering`, a claim about the byte order of records.
- FRAME_SUMMARY records and a store profile for fast selective reads. The container is the same.
- The container header, frame envelope, record header and the CRC are unchanged. A 1.0 file is a valid 1.1 input.
- A `minor` of 1 in the container header exactly when the manifest declares a standard type 10–22.

## Limits

State these before you use the kit.

- **Rust is written but not compiled or run.** Treat it as unverified until you build it and run it against the golden files.
- **Zstd needs the system `libzstd`** (Python, C#, C++), or the `zstd` crate in Rust. Raw files need nothing.
- **The store features, the converters and the semantic checks are Python only.** The other languages encode and decode the wire format and check its structure.
- The examples are teaching codecs, not production libraries. They are not optimised and no performance figures are claimed.
- There is no live socket transport or reconnect service.

The implementation guide gives the exact boundaries.
