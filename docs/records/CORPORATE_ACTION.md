# CORPORATE_ACTION

A `CORPORATE_ACTION` record (type 22, 184 bytes plus text) is one corporate-action event for one listing: dates, ratios, identifiers, short codes, and a `details` text that holds the event-specific terms as one JSON object with sorted keys. The instrument in the record header is the listing, and `ts_event` is the event date. A producer of reference data emits it when an event is announced or its record changes. It is a reference record.

## Fields

<!-- nwt-fields: CORPORATE_ACTION -->

The length field of a text is named after the text with the suffix `_bytes`, for example `event_bytes`.

## Rules

- The identity is `(publisher, unique_id)`. A later record with the same `unique_id` replaces the earlier one.
- `event`, `subtype`, `action`, `status`, `participation`, `payment_type` and `fraction` are short codes defined by the producer.
- `details` is empty or one UTF-8 JSON object with sorted keys. It carries event-specific terms that have no fixed field: extra dates, rates, tender bounds, further outturn identifiers. A reader interprets the fixed fields without `details`.
- Listing facts such as the issuer name, the symbols and the ISIN are not repeated here. A `SECURITY_DEF` for the same instrument carries them.

## Example

<!-- nwt-example: 22 -->

## Write and decode

`record 22` writes the `corporate-action-dividend` vector (288 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 22 work/type-22-python.bin
python3 examples/python/nwt_example.py decode-record work/type-22-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 22 work/type-22-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-22-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 22 work/type-22-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-22-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 22 work/type-22-cpp.bin
work/nwt-cpp decode-record work/type-22-cpp.bin
```
<!-- /nwt-tabs -->

## Conformance vectors

| Scenario | File | Exercises |
|---|---|---|
| `corporate-action-dividend` | `fixtures/golden/records/045-corporate-action-dividend.bin` | Cash dividend with ex, record and payment dates, null ratios, the default-option flag and a `details` JSON object with sorted keys. |
| `corporate-action-split` | `fixtures/golden/records/046-corporate-action-split.bin` | 4-for-1 split: `ratio_old` 1, `ratio_new` 4, an outturn security with its ISIN, a related event and an empty `details`. |
| `corporate-action-minimal` | `fixtures/golden/records/047-corporate-action-minimal.bin` | Only the required texts `event`, `event_id` and `unique_id`. Every date and ratio is null; `option_id` and `serial_id` are unknown (`UINT32_MAX`). |
