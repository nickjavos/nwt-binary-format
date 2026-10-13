# Join market data to reference data

**Goal.** Give a market event its symbol, venue, currency and unit, and give an instrument of a feed its listing name from a symbol directory.

**Input.** [equity-quotes.nwt](files/samples/equity-quotes.nwt), [equity-definitions.nwt](files/samples/equity-definitions.nwt), [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt), [listings-other.nwt](files/samples/listings-other.nwt) and [secmaster-us.nwt](files/samples/secmaster-us.nwt). A symbol directory keeps two records per symbol, a `LISTING` and a `SYMBOL_MAP`:

<!-- nwt-file: fixtures/real/listings-nasdaq.jsonl lines=45-46 -->

**Steps.**

1. Join an event to its definition inside one file. A market record carries a publisher ID and an instrument ID, and the `INSTRUMENT_DEF` with the same pair comes earlier in the same file. Save this program as `work/label_trades.py`. It prints the first three trades with the texts of their definition:

   ```python
   import sys
   sys.path.insert(0, "examples/python")
   import nwt_example as codec

   definitions = {}                                   # (publisher_id, instrument_id) -> texts of the definition
   shown = 0
   with open("fixtures/real-market/equity-quotes.nwt", "rb") as f:
       for record in codec.complete_records(codec.open_reader(f)):
           fields = record["fields"]
           key = (fields["publisher_id"], fields["instrument_id"])
           if record["type"] == 6:                    # INSTRUMENT_DEF
               definitions[key] = record["texts"]
           elif record["type"] == 18 and shown < 3:   # TRADE_QUOTE
               d = definitions[key]                   # the definition always comes first
               print(codec.pretty_time(int(fields["ts_event"])), d["symbol"], d["venue"],
                     codec.pretty_decimal(int(fields["price"])), d["currency"],
                     codec.pretty_decimal(int(fields["quantity"])), d["quantity_unit"])
               shown += 1
   ```

   ```bash
   python3 work/label_trades.py
   ```

   ```text
   2025-09-16T08:00:00.256830296Z NVDA XNAS 177.030000000 USD 180.000000000 share
   2025-09-16T08:00:00.283911761Z NVDA XNAS 177.180000000 USD 100.000000000 share
   2025-09-16T08:00:00.312811923Z NVDA XNAS 177.100000000 USD 31.000000000 share
   ```
2. Join across files by symbol and market identifier code. Each producer numbers instruments in its own namespace, so an instrument ID of the feed does not appear in the symbol directory. The texts do: the `symbol` and `venue` of an `INSTRUMENT_DEF` equal the `symbol` and `listing_mic` of a `LISTING`. Save this program as `work/join_listings.py`. It indexes the listings of the two directory samples and looks up each of the 200 definitions of the feed:

   ```python
   import sys
   sys.path.insert(0, "examples/python")
   import nwt_example as codec

   def records(path, record_type):
       with open(path, "rb") as f:
           for record in codec.complete_records(codec.open_reader(f)):
               if record["type"] == record_type:
                   yield record

   listings = {}                                      # (symbol, listing MIC) -> LISTING
   for path in ("fixtures/real/listings-nasdaq.nwt", "fixtures/real/listings-other.nwt"):
       for listing in records(path, 12):
           texts = listing["texts"]
           listings[(texts["symbol"], texts["listing_mic"])] = listing

   matched = 0
   for definition in records("fixtures/real-market/equity-definitions.nwt", 6):
       texts = definition["texts"]
       listing = listings.get((texts["symbol"], texts["venue"]))
       if listing is None:
           continue
       matched += 1
       if matched <= 4:
           print(definition["fields"]["instrument_id"], texts["symbol"], texts["venue"],
                 "round lot", listing["fields"]["round_lot"], "|", listing["texts"]["name"].strip())
   print(matched, "of 200 definitions have a listing")
   ```

   ```bash
   python3 work/join_listings.py
   ```

   ```text
   1 A XNYS round lot 100 | Agilent Technologies, Inc. Common Stock
   2 AA XNYS round lot 100 | Alcoa Corporation Common Stock
   3 AAA ARCX round lot 100 | Alternative Access First Priority CLO Bond ETF
   21201 AAAA BATS round lot 100 | Amplius Aggressive Asset Allocation ETF
   126 of 200 definitions have a listing
   ```

   Each directory sample holds the first 100 entries of its source, so 74 definitions find no listing here.
3. Look up a single symbol or identifier with [resolve](../tools/resolve.md). `--at` selects the mapping that is valid at a moment, and an ISIN, a CUSIP or a FIGI finds the security master record:

   ```bash
   python3 tools/nwt.py resolve fixtures/real/listings-nasdaq.nwt AAPL --at 2026-11-01
   python3 tools/nwt.py resolve fixtures/real-reference/secmaster-us.nwt US22160K1051
   ```

   ```text
   {"source":"SYMBOL_MAP","publisher_id":"1","instrument_id":"4519135547670130507","symbology":"1","valid_from_ns":"1791907860000000000","valid_to_ns":"18446744073709551615","symbol":"AAPL"}
   {"source":"SECURITY_DEF","publisher_id":"1","instrument_id":"137786","identifier":"isin","symbol":"COST","isin":"US22160K1051","cusip":"22160K105","composite_figi":"BBG000F6H8W8","figi":"BBG000F6HLL1"}
   ```

**Result.** You can label any market record with the texts of its definition, match the instruments of a feed to a symbol directory, and find an instrument by symbol, ISIN, CUSIP or FIGI. [Reference data samples](../REAL-DATA.md#instrument-identifiers) explains how the directory samples derive their instrument IDs, and [Reference data and statistics](../STATE-AND-RECOVERY.md#reference-data-and-statistics) gives the key of every reference record type.
