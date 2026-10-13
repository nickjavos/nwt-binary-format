# Rebuild the samples

The kit keeps the source rows of every sample, so a rebuild needs no network. `fixtures/real/source/` holds the header line and the first 100 data rows of each public file, byte for byte; the two listed-securities files also keep the last row, which holds the file creation time. `fixtures/real-reference/source/` holds the rows of the security-master and corporate-actions exports. Each folder has a `SHA256SUMS` file.

1. Check the source rows. Every line of the output ends in `OK`.

   ```bash
   (cd fixtures/real/source && shasum -a 256 -c SHA256SUMS)
   (cd fixtures/real-reference/source && shasum -a 256 -c SHA256SUMS)
   ```
2. Convert the public files:

   ```bash
   python3 tools/nwt_convert_reference.py mic          fixtures/real/source/ISO10383_MIC.csv fixtures/real/venues.nwt          --retrieved 2026-10-13
   python3 tools/nwt_convert_reference.py nasdaqlisted fixtures/real/source/nasdaqlisted.txt fixtures/real/listings-nasdaq.nwt --retrieved 2026-10-13
   python3 tools/nwt_convert_reference.py otherlisted  fixtures/real/source/otherlisted.txt  fixtures/real/listings-other.nwt  --retrieved 2026-10-13
   python3 tools/nwt_convert_reference.py options      fixtures/real/source/options.txt      fixtures/real/options.nwt         --retrieved 2026-10-13
   ```
3. Convert the security-master and corporate-actions exports. Each command prints its provenance, and the rebuilt files are byte-identical to the samples.

   ```bash
   R=fixtures/real-reference
   python3 tools/nwt_convert_reference.py csv-secmaster         $R/source/secmaster-us.csv             $R/secmaster-us.nwt             --dataset REAL.SECMASTER.US
   python3 tools/nwt_convert_reference.py csv-secmaster         $R/source/secmaster-global.csv         $R/secmaster-global.nwt         --dataset REAL.SECMASTER.GLOBAL
   python3 tools/nwt_convert_reference.py csv-corporate-actions $R/source/corporate-actions-us.csv     $R/corporate-actions-us.nwt     --dataset REAL.CORPACT.US
   python3 tools/nwt_convert_reference.py csv-corporate-actions $R/source/corporate-actions-global.csv $R/corporate-actions-global.nwt --dataset REAL.CORPACT.GLOBAL
   ```
4. Write the JSON Lines view of a sample with the Python reference codec:

   ```bash
   python3 examples/python/nwt_example.py to-json fixtures/real/venues.nwt > fixtures/real/venues.jsonl
   ```
