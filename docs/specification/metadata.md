# Metadata

## TLV encoding

The metadata is a sequence of TLV elements. Each element has an 8-byte header, a value and zero padding.

| Offset | Field | Type | Bytes | Meaning |
|---:|---|---|---:|---|
| 0 | `type` | u16 | 2 | Element type |
| 2 | `flags` | u16 | 2 | Bit 0 is `REQUIRED`; other bits are zero |
| 4 | `value_bytes` | u32 | 4 | Size of the value, without header and padding |
| 8 | value | bytes | `value_bytes` | The value, then zero padding to a multiple of 8 |

- The padding is `align8(8 + value_bytes) - (8 + value_bytes)` zero bytes.
- The elements fill `metadata_bytes` exactly. Nothing follows the last element.
- A reader rejects an unknown element whose `REQUIRED` bit is set. It can skip an unknown optional element after it validates the bounds and padding of that element.
- Types 0 and 65,535 are invalid. Types 1–32,767 are standard. Types 32,768–65,534 are private.
- Every type appears at most once. A duplicate type is invalid, including a duplicate of an unknown type.

| Type | Name | Requirement |
|---:|---|---|
| 1 | `MANIFEST` | Exactly one. The `REQUIRED` bit is set |
| 2 | `PROVENANCE` | Optional JSON object. The `REQUIRED` bit is clear |
| 32,768–65,534 | Private extension | Defined outside this specification. The `REQUIRED` bit states whether a reader needs to support it |

## MANIFEST

The value is a UTF-8 JSON object without a byte order mark.

- A reader rejects duplicate object keys, NaN, infinity, malformed Unicode and JSON nested deeper than 16 levels.
- The size of the manifest is bounded by the maximum metadata size.
- A JSON number in the manifest is an exact integer from 0 through 4,294,967,295. A value that needs more range is a string with a syntax that the schema defines.
- A reader can ignore an unknown object property. An unknown property does not change the interpretation of existing fields.

Required top-level fields:

| Field | Type | Rules |
|---|---|---|
| `dataset` | string | 1–255 UTF-8 bytes. A stable namespace |
| `producer` | string | 1–255 bytes. Name and version of the producer |
| `profile` | string | Exactly `market-data` or `generic-events` |
| `publishers` | array | Up to 4,096 entries with unique IDs |
| `schemas` | array | 1–4,096 entries with unique `(type, version)` pairs |
| `clock` | string | Exactly `posix-ns` |

Optional top-level field:

| Field | Type | Rules |
|---|---|---|
| `ordering` | string | `none`, `ts_event` or `instrument,ts_event`. Absent means `none` |

**Ordering.** `ordering` is a claim of the producer about the order of records in the container.

- `ts_event`: the non-null `ts_event` values are non-decreasing in byte order across the whole container. Records with a null `ts_event` are exempt.
- `instrument,ts_event`: the `instrument_id` values are non-decreasing in byte order, and within one `instrument_id` the non-null `ts_event` values are non-decreasing.
- A producer declares an ordering only when it holds. A validator checks the claim against a full scan. A false claim is an error.
- The property changes no wire meaning. A reader that does not use it ignores it.
- Binary search by time is valid only when a validated `ts_event` ordering is declared. See [`INDEX` frames](frames.md#index-frames).

**Publishers.** Each publisher object contains `id` (1–4,294,967,295), `name` (1–255 bytes) and `venue` (0–255 bytes).

- The publisher list can be empty only when every record uses the system scope.
- A venue is a name that the producer defines. It need not be a market identifier code.
- Every nonzero publisher in a record is declared.

**Schemas.** Each schema object contains `type` (1–65,534), `version` (1–255), `required` (boolean), `name` (1–255 bytes) and `spec_uri` (1–2,048 bytes).

- A standard schema uses version 1 and its name from [Record types](record-types.md).
- `spec_uri` is `urn:nwt:spec:1.0` for record types 1–9 and `urn:nwt:spec:1.1` for record types 10–22.
- A private schema provides a stable URI that identifies its exact external specification. A URI is an identifier. It is not an instruction to fetch or execute code.
- The schema list is a declaration. It is not an embedded schema language.
- Every `(type, version)` that the container emits is declared, including optional ones. Declarations that no record uses are permitted.
- The value of `required` for each standard record type is given in [Scope and required schemas](record-types.md#scope-and-required-schemas).

**Profiles.**

- `market-data` requires instrument definitions before use and the rules in [Record types](record-types.md) and [Ordering, gaps, snapshots and replay](ordering-gaps-snapshots-and-replay.md).
- `generic-events` permits system and private event schemas. The standard record types 1–7 and 10–19 are not allowed in it. It does not relax framing or sequencing.
- `GAP`, `SYSTEM`, `FRAME_SUMMARY`, `SECURITY_DEF` and `CORPORATE_ACTION` are permitted in either profile.

<!-- nwt-title: Example manifest -->
```json
{
  "dataset": "EXAMPLE.MARKET",
  "producer": "example-writer/3",
  "profile": "market-data",
  "clock": "posix-ns",
  "ordering": "ts_event",
  "publishers": [{"id": 1, "name": "Example Feed", "venue": "EXAMPLE"}],
  "schemas": [
    {"type": 1, "version": 1, "required": true, "name": "TRADE", "spec_uri": "urn:nwt:spec:1.0"},
    {"type": 6, "version": 1, "required": true, "name": "INSTRUMENT_DEF", "spec_uri": "urn:nwt:spec:1.0"},
    {"type": 15, "version": 1, "required": true, "name": "BOOK_DELTA", "spec_uri": "urn:nwt:spec:1.1"}
  ]
}
```

This manifest declares record type 15, so the container header has `minor` = 1.

## PROVENANCE

The value is a JSON object under the same text and nesting rules as `MANIFEST`.

- Recommended optional string properties: `source_format`, `source_version`, `converter`, `conversion_policy`, `clock_policy` and `license_reference`. Each string is at most 4,096 bytes.
- Credentials are not allowed in it.
- It is descriptive and cannot override the wire rules of this specification.
