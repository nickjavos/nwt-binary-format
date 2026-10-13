# Inspect and validate a file

**Goal.** Find out what an NWT file holds and whether it is complete and consistent, without knowing anything about it in advance.

**Input.** [depth-10.nwt](files/samples/depth-10.nwt), a sample of book snapshots for options on futures.

**Steps.**

1. Print what the file declares about itself. [inspect](../tools/inspect.md) reads the container header and the `MANIFEST`:

   ```bash
   python3 tools/nwt.py inspect fixtures/real-market/depth-10.nwt | grep -E '^(container|profile|publisher|schema)'
   ```

   ```text
   container major=1 minor=1 stream_id=c62bb6aea2cce2e4bb7ca4d0c7d2e6ad created_ns=1791849600000000000
   profile market-data clock=posix-ns ordering=none
   publisher 97 publisher-97 venue=
   schema 5 v1 BOOK_SNAPSHOT required=true
   schema 6 v1 INSTRUMENT_DEF required=true
   schema 11 v1 OPTION_DEF required=false
   ```

   The file declares one publisher and three record types. `inspect` also prints the dataset, the producer and the `PROVENANCE` object; the filter leaves those lines out.
2. Print the frames and the record counts, which are the last eight lines of the same output:

   ```bash
   python3 tools/nwt.py inspect fixtures/real-market/depth-10.nwt | tail -n 8
   ```

   ```text
   frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns
   0 DATA 0 1896 122920 122920 886 1743984000000000000 1744011000192310000
   1 INDEX 0 124880 40 40 0 - -
   2 END 0 124984 32 32 0 - -
   end data_frames=1 records=886 status=normal
   records BOOK_SNAPSHOT 500
   records INSTRUMENT_DEF 199
   records OPTION_DEF 187
   ```

   One raw `DATA` frame holds all 886 records. The `INDEX` and the `END` frame close the file, and `status=normal` says that the producer completed it.
3. Check the whole file. [validate](../tools/validate.md) verifies every checksum, length and sequence, and then applies the state rules to every record:

   ```bash
   python3 tools/nwt.py validate fixtures/real-market/depth-10.nwt
   ```

   ```text
   valid records=886 data_frames=1 summaries=0 ordering=none
   ```
4. See how a cut file and a damaged file are reported. The first copy loses its end, and the second has one changed byte in the middle of the payload:

   ```bash
   head -c 100000 fixtures/real-market/depth-10.nwt > work/cut.nwt
   python3 tools/nwt.py validate work/cut.nwt
   ```

   ```text
   NWT error: incomplete: file ends inside frame payload
   ```

   ```bash
   cp fixtures/real-market/depth-10.nwt work/damaged.nwt
   printf '\377' | dd of=work/damaged.nwt bs=1 seek=50000 conv=notrunc 2> /dev/null
   python3 tools/nwt.py validate work/damaged.nwt
   ```

   ```text
   NWT error: payload CRC
   ```

   Both commands exit with status 1.

**Result.** You know the publisher, the record types and the record counts of the file, you know that it is complete and passes the state rules, and you have seen the two messages that a broken copy produces.
