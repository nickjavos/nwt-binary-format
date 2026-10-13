# SECURITY_DEF

A `SECURITY_DEF` record (type 21, 216 bytes plus text) is the security-master record of one listing of one security: identifiers such as ISIN, CUSIP, FIGI, LEI and CFI, classification codes, countries, currencies, shares outstanding and key dates, in 30 texts and a block of numeric fields. The instrument in the record header is the listing, and `ts_event` is the time the facts became effective. A producer of reference data emits it when the facts of a listing are published or change. It is a reference record.

## Fields

<!-- nwt-fields: SECURITY_DEF -->

The length field of a text is named after the text with the suffix `_bytes`, for example `issuer_name_bytes`.

## Rules

- The identity is `(publisher, instrument)`. A later record replaces the earlier one.
- `security_type`, `structure`, `listing_status` and `voting` are short codes defined by the producer, like `currency` in `INSTRUMENT_DEF`. Systems that exchange them need the same agreement on the code set.
- `shares_outstanding` is a whole count because the share counts of large issuers exceed the range of a quantity scaled by 10⁻⁹.

## Example

<!-- nwt-example: 21 -->

## Write and decode

`record 21` writes the `security-def-full` vector (440 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 21 work/type-21-python.bin
python3 examples/python/nwt_example.py decode-record work/type-21-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 21 work/type-21-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-21-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 21 work/type-21-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-21-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 21 work/type-21-cpp.bin
work/nwt-cpp decode-record work/type-21-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `security-def-full` | `fixtures/golden/records/043-security-def-full.bin` | All 30 texts filled, with identifiers, dates, share count, lot size and par value; main listing, multi-currency flag, null `delisting_ns`. |
| `security-def-minimal` | `fixtures/golden/records/044-security-def-minimal.bin` | The smallest valid record: every text empty, every nullable field null, every producer identifier 0. |
