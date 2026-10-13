# Convert a CSV export

**Goal.** Turn a top-of-book export in CSV into an NWT file and prove that the conversion kept every value.

**Input.** `fixtures/real-market/source/xnas-itch_mbp-1_equities.csv` from the [kit](files/nwt-binary-format-kit.zip): 2,000 top-of-book rows of one equity. The result equals the sample [equity-quotes.nwt](files/samples/equity-quotes.nwt). The first line of the source names the columns, and each further line is one book event with decimal prices and UTC timestamps:

<!-- nwt-file: fixtures/real-market/source/xnas-itch_mbp-1_equities.csv lines=1-3 -->

**Steps.**

1. Convert the file. `csv-mbp1` is the converter kind for a top-of-book export, and `--definitions` names the export that holds the definition of the instrument:

   ```bash
   python3 tools/nwt.py convert csv-mbp1 fixtures/real-market/source/xnas-itch_mbp-1_equities.csv work/equity-quotes.nwt --dataset REAL.XNAS.ITCH --definitions fixtures/real-market/source/xnas-itch_definition_equities.csv --currency USD --quantity-unit share > work/equity-quotes.provenance.json
   ```

   The command writes the container and prints a summary of the conversion as JSON, which the redirection saves. The same summary is stored in the `PROVENANCE` of the container.
2. Read the record counts and the rounding count from the summary:

   ```bash
   grep -A 4 records_written work/equity-quotes.provenance.json
   grep values_rounded work/equity-quotes.provenance.json
   ```

   ```text
     "records_written": {
       "INSTRUMENT_DEF": 1,
       "QUOTE": 2000,
       "TRADE_QUOTE": 476
     },
     "values_rounded": 0
   ```

   Every row became a `QUOTE`, and each of the 476 trade rows also became a `TRADE_QUOTE`. No value was rounded: the converter parses decimals with integer arithmetic and stops at a value it cannot store exactly.
3. Check the result. `cmp` prints nothing when two files are byte-identical, and `validate` confirms the structure and the state rules:

   ```bash
   cmp work/equity-quotes.nwt fixtures/real-market/equity-quotes.nwt
   python3 tools/nwt.py validate work/equity-quotes.nwt
   ```

   ```text
   valid records=2477 data_frames=1 summaries=0 ordering=none
   ```
4. Compare one source row with its record. The second line of the export has an ask of 186 for 100 shares and no bid:

   ```bash
   python3 tools/nwt.py cat work/equity-quotes.nwt --pretty | sed -n 2p
   ```

   ```text
   {"type_name":"QUOTE","record_bytes":"96","record_type":"2","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:00:00.015298471Z","ts_recv":"2025-09-16T08:00:00.015462508Z","sequence":"2","bid_price":null,"ask_price":"186.000000000","bid_quantity":"0.000000000","ask_quantity":"100.000000000","bid_order_count":"0","ask_order_count":"1","quote_flags":"0"}
   ```

**Result.** You have an NWT file that is byte-identical to the published sample, with the instrument definition in front of the quotes and the conversion rules recorded inside the file. [Market data samples](../REAL-DATA-MARKET.md#converter-kinds) lists the converter kinds for order-level books, depth, bars, definitions and statistics, and [Reference data samples](../REAL-DATA.md#converter-kinds) lists the kinds for venues, listings, securities and corporate actions.
