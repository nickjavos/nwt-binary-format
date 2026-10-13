# VENUE_DEF

A `VENUE_DEF` record (type 10, 96 bytes plus text) describes a trading venue or one of its segments, identified by a market identifier code (MIC). A producer emits it once per venue, and again when the venue record changes. It is a reference record: publisher is nonzero, instrument is 0, and it needs no `INSTRUMENT_DEF`.

## Fields

<!-- nwt-fields: VENUE_DEF -->

## Rules

- The identity is `(publisher, mic)`. A later record replaces the earlier one.
- `kind` = 1 requires `mic` equal to `operating_mic`.
- `mic` and `country` consist of upper-case ASCII letters or digits.
- Dates are midnight UTC of the source date.

## Example

<!-- nwt-example: 10 -->

## Write and decode

`record 10` writes the `venue-operating` vector (192 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 10 work/type-10-python.bin
python3 examples/python/nwt_example.py decode-record work/type-10-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 10 work/type-10-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-10-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 10 work/type-10-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-10-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 10 work/type-10-cpp.bin
work/nwt-cpp decode-record work/type-10-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `venue-operating` | `fixtures/golden/records/003-venue-operating.bin` | Operating venue (`kind` 1, `mic` equal to `operating_mic`), active, with all nine texts filled. |
| `venue-segment-unicode` | `fixtures/golden/records/004-venue-segment-unicode.bin` | Market segment (`kind` 2) of that venue, status updated. `name` is 128 characters and exactly 255 bytes of UTF-8, the maximum; the optional texts are empty. |
| `venue-expired` | `fixtures/golden/records/005-venue-expired.bin` | Expired venue (`status` 3) with an expiry date, a null `created_ns`, and empty `legal_entity` and `lei`. |
