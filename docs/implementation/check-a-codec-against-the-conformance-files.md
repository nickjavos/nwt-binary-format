# Check a codec against the conformance files

The conformance files are [all-records.nwt](files/samples/all-records.nwt) and [all-records.zst.nwt](files/samples/all-records.zst.nwt). Both hold the same 47 records, one or more of every record type except `FRAME_SUMMARY`: the first with raw frames, the second with Zstandard frames. In the kit they are in `fixtures/golden/`, with the single records in `fixtures/golden/records/` and the invalid containers in `fixtures/golden/malformed/`. The steps below use `EX` for a reference codec and `YOURS` for the program under test.

1. **Read the raw file.** Print every field in the format of `read` and compare with the reference output. The two reports are identical.

   ```bash
   EX read fixtures/golden/all-records.nwt > work/reference-fields.txt
   YOURS read fixtures/golden/all-records.nwt > work/your-fields.txt
   cmp work/reference-fields.txt work/your-fields.txt
   ```
2. **Read the Zstandard file.** It decodes to the same report.

   ```bash
   YOURS read fixtures/golden/all-records.zst.nwt > work/your-zstd-fields.txt
   cmp work/reference-fields.txt work/your-zstd-fields.txt
   ```
3. **Write the raw file.** Re-encode the records you read: the same metadata bytes, stream ID and creation time, raw `DATA` frames of 3 records each, then `INDEX` and `END`. The output is byte-identical to the conformance file.

   ```bash
   YOURS read fixtures/golden/all-records.zst.nwt work/your-again.nwt > /dev/null
   cmp work/your-again.nwt fixtures/golden/all-records.nwt
   ```
4. **Write Zstandard frames.** Compare decoded content, not compressed bytes: the compressed bytes depend on the version of the Zstandard library.

   ```bash
   YOURS write-golden work/your-zstd.nwt --zstd
   EX read work/your-zstd.nwt | cmp - work/reference-fields.txt
   ```
5. **Encode single records.** Each `fixtures/golden/records/NNN-label.bin` is one encoded record, and the `.json` file beside it holds its field values. Encode the values and compare the bytes; decode the bytes and compare the values.

   ```bash
   EX decode-record fixtures/golden/records/001-def-equity.bin
   ```
6. **Reject invalid input.** Every file in `fixtures/golden/malformed/` has one defect and is valid in every other respect, so a reader that skips that one check accepts it. A conforming reader exits with a non-zero status on each of them.

   ```bash
   for f in fixtures/golden/malformed/*.nwt; do EX read "$f" > /dev/null 2>&1 && echo "accepted: $f"; done
   ```

   The loop prints nothing when every file is rejected.
7. **Validate what you write.** Run [validate](../tools/validate.md) on containers your writer produces. It applies the structural checks and the state rules to every record.
