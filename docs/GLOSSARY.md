# Glossary

This page defines the terms of the NWT Binary Format documentation, each with the meaning it has in NWT and a link to the section that defines it.

## Container and frames

| Term | Meaning |
|---|---|
| container | One complete NWT byte sequence: a container header, metadata, a series of frames and one `END` frame. One file or one stream holds one container. See [File structure](specification/file-structure.md). |
| container header | The first 64 bytes of a container: the magic `NWTBIN\r\n`, `major` and `minor`, the size and CRC-32C of the metadata, the stream ID and the creation time. See [Container header](specification/container-header.md). |
| stream ID | The 16-byte identifier of one immutable container, stored in the container header. A file with different bytes, such as a filtered or recompressed copy, has a new stream ID. |
| metadata | The TLV elements between the container header and the first frame. They do not change inside a container. See [Metadata](specification/metadata.md). |
| TLV | A metadata element in type, length, value form: an 8-byte header with the element type, flags and the size of the value, then the value and zero padding to a multiple of 8 bytes. See [TLV encoding](specification/metadata.md#tlv-encoding). |
| `MANIFEST` | The required metadata element: a JSON object that names the dataset, the producer, the profile, the clock, the publishers and the record types of the container. Its content is the manifest. See [MANIFEST](specification/metadata.md#manifest). |
| `PROVENANCE` | The optional metadata element: a JSON object that describes the source of the data and the rules of its conversion. It is descriptive and changes no wire rule. See [PROVENANCE](specification/metadata.md#provenance). |
| publisher | A source of records, declared in the manifest with an ID, a name and a venue. Every record names its publisher in `publisher_id`; 0 is the scope of the container. |
| producer | The party that creates a container: it captures or converts source data and runs the writer. The manifest names it in `producer`. A producer is not a publisher. |
| writer | A program that writes a container: it emits the container header and the metadata, packs whole records into frames and closes the container with the `END` frame. See [Write a file](IMPLEMENTATION-GUIDE.md#write-a-file). |
| reader | A program that reads a container: it checks the container header, the metadata and every frame, and decodes the records. See [Read a file](IMPLEMENTATION-GUIDE.md#read-a-file). |
| frame | A checksummed unit of a container: a 64-byte frame header, a payload and zero padding. Its kind is `DATA`, `INDEX` or `END`. See [Frames](specification/frames.md). |
| frame header | The 64 bytes at the start of every frame: the kind, the codec, the stored and raw payload sizes, the record count, `frame_seq`, the lowest and highest `ts_event`, and two CRC-32C values. See [Frame header](specification/frames.md#frame-header). |
| `DATA` | The frame kind that carries records. A `DATA` frame holds one or more whole records, and a record never crosses a frame boundary. See [DATA frames](specification/frames.md#data-frames). |
| `INDEX` | The optional frame kind that lists every `DATA` frame in a 40-byte entry: its offset, its time range, its raw size and its record count. See [INDEX frames](specification/frames.md#index-frames). |
| `END` | The frame that closes a container. It is 96 bytes and gives the totals, the completion status and the offset of the first `INDEX` frame. A file without it is incomplete. See [END frame](specification/frames.md#end-frame). |
| CRC-32C | The 32-bit checksum, Castagnoli polynomial, that protects the container header, the metadata, every frame header and every raw frame payload. See [CRC-32C](specification/compression-and-integrity.md#crc-32c). |
| Zstandard | The optional compression of a `DATA` frame: codec 1 stores the payload as one [Zstandard](https://github.com/facebook/zstd) frame, and codec 0 stores it raw. Each frame is compressed on its own. See [Zstandard](specification/compression-and-integrity.md#zstandard). |
| store profile | A set of writer choices for files that are queried: large frames, Zstandard compression, an `INDEX`, `FRAME_SUMMARY` records and a declared `ordering`. A store file is an ordinary container. See [Store profile](STORE.md). |
| `ordering` | The optional manifest property that states the order of the records: `ts_event`, `instrument,ts_event` or `none`. A producer declares it only when it holds. See [MANIFEST](specification/metadata.md#manifest). |
| selective read | A read that uses the `INDEX` and the `FRAME_SUMMARY` records to fetch only the frames that can hold a match. Its result is partial: definitions and book state from the skipped frames are not included. See [How a reader seeks by time and instrument](STORE.md#how-a-reader-seeks-by-time-and-instrument). |

## Records and fields

| Term | Meaning |
|---|---|
| record | One message of one record type inside a `DATA` frame: a 48-byte record header, a body and zero padding to a multiple of 8 bytes. See [Record header](specification/record-header.md). |
| record header | The first 48 bytes of every record: `record_bytes`, `record_type`, `schema_version`, `flags`, `publisher_id`, `channel_id`, `instrument_id`, `ts_event`, `ts_recv` and `sequence`. See [Record header](specification/record-header.md). |
| record type | The number in `record_type` that selects the layout of the record body. The format defines 22 standard record types, from `TRADE` (1) to `CORPORATE_ACTION` (22). See [Record types](specification/record-types.md). |
| schema | A record type together with a schema version: one wire layout and its rules. The manifest declares every schema that the container uses. |
| fixed portion | The fields of a record at fixed offsets: the record header and the body fields of the record type. The Specification calls it the fixed part, and the schema file gives its size as `fixed_bytes`. |
| variable text | A UTF-8 text of a record, such as a symbol or a name. Its length is a field of the fixed portion, and the texts follow the fixed portion in the order of their length fields, with no terminator. See [Common rules](specification/record-types.md#common-rules). |
| fixed-point value | A decimal stored as an integer: the value multiplied by 10⁹. A price is a signed 64-bit integer, and a quantity is an unsigned one. See [Decimal values and null values](specification/data-types-and-conventions.md#decimal-values-and-null-values). |
| scale | The factor between a stored integer and its decimal value. NWT has one scale, 10⁹: the price 123.45 is stored as `123450000000`. |
| null sentinel | The reserved integer that marks a value as absent: `INT64_MIN` for a price, `UINT64_MAX` for a quantity or a timestamp, `UINT32_MAX` for a count. Zero is a value, not a null. See [Decimal values and null values](specification/data-types-and-conventions.md#decimal-values-and-null-values). |
| timestamp | An unsigned 64-bit count of nanoseconds since 1970-01-01T00:00:00 UTC. `ts_event` is the event time at the source, and `ts_recv` is the capture time at the producer. See [Time](specification/data-types-and-conventions.md#time). |
| `instrument_id` | The 64-bit identifier of an instrument in the namespace of its publisher, carried in every record header. It is 0 in records that belong to no instrument. See [Identifiers](specification/data-types-and-conventions.md#identifiers). |
| channel | A logical partition of the records of one publisher, defined by the producer and carried in `channel_id`. 0 is a valid channel. |
| sequence number | The value of `sequence` in the record header: the output position of a record within its publisher and channel, counted from 1 without holes. It is not a sequence number of an exchange. See [Sequence numbers and ordering](STATE-AND-RECOVERY.md#sequence-numbers-and-ordering). |
| `frame_seq` | The counter in the frame header that numbers the frames of a container from 0. A hole means a transfer failure. |
| `FRAME_SUMMARY` | Record type 20. One record describes one `DATA` frame: its offset, its stored size, its codec, a mask of the record types it holds and its range of instrument IDs. See [FRAME_SUMMARY](records/FRAME_SUMMARY.md). |

## Market data

| Term | Meaning |
|---|---|
| trade | An execution reported by a venue. `TRADE`, type 1, carries one step of the lifecycle of a trade: new, corrected or canceled. See [TRADE](records/TRADE.md). |
| quote | The best bid and the best ask of one order book. `QUOTE`, type 2, replaces both sides with their price, quantity and order count. See [QUOTE](records/QUOTE.md). |
| top of book | The best bid and the best ask of an order book, with the quantity and the number of orders at each price. `QUOTE` and `TRADE_QUOTE` carry it. |
| best bid and offer | The best bid and the best ask across venues. `BEST_QUOTE`, type 19, carries both sides and names the publisher that set each of them. See [BEST_QUOTE](records/BEST_QUOTE.md). |
| trade with quote | `TRADE_QUOTE`, type 18: one trade print together with the top of book immediately before it. See [TRADE_QUOTE](records/TRADE_QUOTE.md). |
| bar (OHLCV) | A completed time bucket built from trades. `BAR`, type 3, carries the open, high, low and close prices, the volume and the trade count of one interval. See [BAR](records/BAR.md). |
| order book | The resting buy and sell orders of one instrument at one publisher and channel. NWT describes it at two levels: the order-level book of single orders and the aggregate book of price levels. |
| market by order | The order-level view of a book. `MBO`, type 4, reports a change of one order (`ADD`, `MODIFY`, `DELETE`), a `CLEAR` or a snapshot marker. See [MBO](records/MBO.md). |
| book snapshot | The whole aggregate book in one record. `BOOK_SNAPSHOT`, type 5, replaces the book with at most 1,024 ranked levels on each side. See [BOOK_SNAPSHOT](records/BOOK_SNAPSHOT.md). |
| book delta | A change of the aggregate book. `BOOK_DELTA`, type 15, sets or deletes one price level, or clears a side. Levels are keyed by price. See [BOOK_DELTA](records/BOOK_DELTA.md). |
| depth level | One rank of a `BOOK_SNAPSHOT`: 48 bytes with the bid and the ask price, quantity and order count at that rank. |
| imbalance | The quantity of buy or sell orders that an auction cannot match. `IMBALANCE`, type 16, carries the reference price, the paired quantity, and the quantity and side of the imbalance. See [IMBALANCE](records/IMBALANCE.md). |
| trading status | The state of trading in an instrument: pre-open, open, halted, closed or auction. `STATUS`, type 7, replaces it. See [STATUS](records/STATUS.md). |
| statistics | Values that a venue publishes for a session or a date: open, high, low, close, settlement, VWAP, volume and open interest. `STATISTICS`, type 13, sets or withdraws one value. See [STATISTICS](records/STATISTICS.md). |
| open interest | The number of open contracts of a derivative. It is a quantity statistic: `stat_type` 8 of a `STATISTICS` record. |
| implied volatility and Greeks | The model values of an option: implied volatility, delta, gamma, theta, vega and rho. `OPTION_ANALYTICS`, type 14, carries them as fixed-point values, each nullable on its own. See [OPTION_ANALYTICS](records/OPTION_ANALYTICS.md). |

## Reference data

| Term | Meaning |
|---|---|
| instrument definition | `INSTRUMENT_DEF`, type 6: the symbol, venue, currency, quantity unit, increments and asset class of one instrument. It precedes every market record of that instrument in the container. See [INSTRUMENT_DEF](records/INSTRUMENT_DEF.md). |
| option definition | `OPTION_DEF`, type 11: the terms of an option contract, with the underlying, the expiration, the strike, call or put, the exercise style and the settlement. See [OPTION_DEF](records/OPTION_DEF.md). |
| listing | `LISTING`, type 12: one entry of a symbol directory, with the symbol, the name, the listing venue and the round lot of an instrument. See [LISTING](records/LISTING.md). |
| venue and MIC | A venue is a trading venue or a market segment. A MIC is its four-character market identifier code under ISO 10383. `VENUE_DEF`, type 10, describes one venue by its MIC. See [VENUE_DEF](records/VENUE_DEF.md). |
| symbol map | `SYMBOL_MAP`, type 17: a statement that a symbol names an instrument from `valid_from_ns` up to, but not including, `valid_to_ns`. See [SYMBOL_MAP](records/SYMBOL_MAP.md). |
| security master | The reference record of a security. `SECURITY_DEF`, type 21, describes one listing of one security with its identifiers, such as ISIN, CUSIP and FIGI, and its key dates. See [SECURITY_DEF](records/SECURITY_DEF.md). |
| corporate action | An event of an issuer that affects a security, such as a dividend or a split. `CORPORATE_ACTION`, type 22, carries one event for one listing, with its dates, ratios and details. See [CORPORATE_ACTION](records/CORPORATE_ACTION.md). |

## State and recovery

| Term | Meaning |
|---|---|
| consumer | A program that applies the records of a container in delivery order to keep state, such as order books, quotes and trades. |
| state | What a consumer keeps while it reads records: definitions, order books, the top of book, the trading status, trade lifecycles and reference records. Each record creates, replaces or ends one piece of it. See [State a consumer keeps](STATE-AND-RECOVERY.md#state-a-consumer-keeps). |
| delivery order | The order of the bytes in the container. A consumer applies records in this order; timestamps can move backward. See [Delivery order](specification/ordering-gaps-snapshots-and-replay.md#delivery-order). |
| gap | A loss of data at the source that the producer reports with a `GAP` record, type 8. It makes the order books, the top of book and the trading status of its publisher and channel unknown. See [GAP](records/GAP.md). |
| snapshot | A complete replacement of a book. The aggregate book takes it from one `BOOK_SNAPSHOT`; the order-level book takes it from the `MBO` records between `SNAPSHOT_BEGIN` and `SNAPSHOT_END`. See [MBO snapshot transaction](specification/ordering-gaps-snapshots-and-replay.md#mbo-snapshot-transaction). |
| recovery | The return to valid state after a loss. After a gap, each piece of state is valid again when its own record arrives; after a transfer failure, the consumer reads again from the last verified frame. See [Gaps and recovery](STATE-AND-RECOVERY.md#gaps-and-recovery). |
| replay | Reading stored records in delivery order to rebuild state. A book replay starts at a `CLEAR` or a completed snapshot and applies every record after it. The record header flag `REPLAY` marks a record as historical or replayed. |
| transfer failure | Damaged or missing bytes of a container: a checksum that does not match, a hole in `frame_seq` or `sequence`, or the end of input before `END`. It is not a gap. See [Transfer failure versus source failure](STATE-AND-RECOVERY.md#transfer-failure-versus-source-failure). |

## Kit and conformance

| Term | Meaning |
|---|---|
| kit | The package that holds this documentation, the schema file, the four reference codecs, the tools and the fixtures: [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip). |
| reference codec | One of the four programs of the kit, in Python, Rust, C# and C++, that read and write every record type. See [Implementation guide](IMPLEMENTATION-GUIDE.md). |
| conformance file | A file in `fixtures/golden/` that holds 47 records of 21 record types (every type except `FRAME_SUMMARY`): [all-records.nwt](files/samples/all-records.nwt) with raw frames and [all-records.zst.nwt](files/samples/all-records.zst.nwt) with Zstandard frames. The four reference codecs produce byte-identical output for the conformance files. See [Conformance files](specification/conformance-files-and-examples.md#conformance-files). |
| conformance vector | One record of `fixtures/catalog-golden.json`, listed with its field values and kept as a single encoded record in `fixtures/golden/records/`. The 48 conformance vectors cover all 22 record types, and 47 of them make up the conformance files. |
| sample | An NWT file in `fixtures/real/`, `fixtures/real-reference/` or `fixtures/real-market/`, converted from public exchange and registry files or from exchange market-data exports. See [Reference data samples](REAL-DATA.md) and [Market data samples](REAL-DATA-MARKET.md). |
| minimal example file | `fixtures/basic/example.nwt`: one container of 920 bytes with an `INSTRUMENT_DEF` and a `TRADE`. See [Minimal example file](specification/conformance-files-and-examples.md#minimal-example-file). |
| schema file | [records.json](files/records.json), the machine-readable description of the record header, the depth level and all 22 record types. The reference codecs take every layout from it. |
| `nwt` command | The command-line tool `tools/nwt.py`: it inspects, validates, prints, filters, merges, splits, repacks, queries and converts containers. See [The nwt command](TOOLS.md). |
