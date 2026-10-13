# Print records as JSON Lines or CSV

**Goal.** Read the records of a file as text, with the stored integers for a program or with readable values for a person.

**Input.** [equity-bars.nwt](files/samples/equity-bars.nwt): 921 one-minute bars of one equity.

**Steps.**

1. Print the records as JSON Lines. [cat](../tools/cat.md) writes one JSON object per record, and every value is the stored integer as a decimal string. The second record of the file is the first bar:

   ```bash
   python3 tools/nwt.py cat fixtures/real-market/equity-bars.nwt | sed -n 2p
   ```

   ```text
   {"type_name":"BAR","record_bytes":"112","record_type":"3","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"1758009660000000000","ts_recv":"18446744073709551615","sequence":"2","interval_start_ns":"1758009600000000000","interval_end_ns":"1758009660000000000","open":"177030000000","high":"177280000000","low":"177030000000","close":"177280000000","volume":"3300000000000","trade_count":"51","bar_flags":"0"}
   ```

   `open` is 177.03 scaled by 10⁹, and `ts_recv` holds the null sentinel, `18446744073709551615`.
2. Add `--pretty` for readable values: decimals with nine fractional digits, ISO 8601 times in UTC, and JSON `null` for a null value:

   ```bash
   python3 tools/nwt.py cat fixtures/real-market/equity-bars.nwt --pretty | sed -n 2p
   ```

   ```text
   {"type_name":"BAR","record_bytes":"112","record_type":"3","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:01:00.000000000Z","ts_recv":null,"sequence":"2","interval_start_ns":"2025-09-16T08:00:00.000000000Z","interval_end_ns":"2025-09-16T08:01:00.000000000Z","open":"177.030000000","high":"177.280000000","low":"177.030000000","close":"177.280000000","volume":"3300.000000000","trade_count":"51","bar_flags":"0"}
   ```
3. Print one record type as CSV with the Python reference codec. `to-csv` takes the file and the number of the record type; `BAR` is type 3. The command prints a header line and 921 bars; the first three lines are shown, and 919 more follow:

   ```bash
   python3 examples/python/nwt_example.py to-csv fixtures/real-market/equity-bars.nwt 3 --pretty | head -n 3
   ```

   ```text
   record_bytes,record_type,schema_version,flags,publisher_id,channel_id,instrument_id,ts_event,ts_recv,sequence,interval_start_ns,interval_end_ns,open,high,low,close,volume,trade_count,bar_flags
   112,3,1,0,2,0,11667,2025-09-16T08:01:00.000000000Z,,2,2025-09-16T08:00:00.000000000Z,2025-09-16T08:01:00.000000000Z,177.030000000,177.280000000,177.030000000,177.280000000,3300.000000000,51,0
   112,3,1,0,2,0,11667,2025-09-16T08:02:00.000000000Z,,3,2025-09-16T08:01:00.000000000Z,2025-09-16T08:02:00.000000000Z,177.220000000,177.280000000,177.210000000,177.240000000,1694.000000000,24,0
   ```

   A null value is an empty CSV field. Without `--pretty`, `to-csv` prints the stored integers.
4. Pass the text to other tools. This pipeline finds the bar with the highest volume and prints its start time, its four prices, its volume and its trade count:

   ```bash
   python3 examples/python/nwt_example.py to-csv fixtures/real-market/equity-bars.nwt 3 --pretty | tail -n +2 | sort -t, -k17,17 -n -r | head -n 1 | cut -d, -f11,13-18
   ```

   ```text
   2025-09-16T20:00:00.000000000Z,174.870000000,174.990000000,174.850000000,174.900000000,11263305.000000000,164
   ```

**Result.** You can turn any NWT file into JSON Lines, and any record type into CSV, in the raw or the readable form, and feed the text to a shell pipeline, a spreadsheet or a database loader. All four reference codecs have the `to-json` and `to-csv` commands and print the same text.
