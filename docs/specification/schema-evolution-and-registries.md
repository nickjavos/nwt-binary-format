# Schema evolution and registries

## Container version

- A reader rejects an unknown `major` value. A change of `major` permits incompatible changes to the container header and the frame header.
- A change of `minor` can add TLV types or record schemas. It preserves the 64-byte headers and every existing meaning.
- A reader that implements a subset of the record types can read a container when every header field has a value it supports and it understands every required TLV element and every required schema. It skips optional records it does not know.
- A reader that does not implement `BOOK_DELTA` therefore refuses a container that declares it, because `BOOK_DELTA` is always declared as required.
- A strict reader can reject a `minor` value it does not know with a clear unsupported-version error.

## Schema versions

- The layout and the meaning of an existing `(record_type, schema_version)` are immutable.
- A new field needs a new schema version. A changed meaning needs a new schema version or a new record type.
- A schema version is a complete contract. It does not promise that a later version keeps the same prefix. A reader cannot assume that an unknown version has the layout of a known one.
- An extension of an enum needs a new schema version where it affects meaning.

## Type registries

| Range | Record types | TLV types |
|---|---|---|
| 0 | Invalid | Invalid |
| 1–32,767 | Standard. Types 1–22 are assigned | Standard. Types 1 and 2 are assigned |
| 32,768–65,534 | Private | Private |
| 65,535 | Invalid | Invalid |

- A private record type is scoped by its exact `spec_uri` in the manifest. Applications that exchange it need to agree on both the URI and the layout.
- A container cannot bind one `(type, version)` to more than one schema.

## Unknown records

- A reader skips an unknown optional record type or version by `record_bytes`, after it has validated the frame and the manifest.
- An unknown required schema stops semantic decoding before any `DATA` frame is consumed.
- Skipped records still count toward sequence checking, frame counts and timestamp bounds. A lossless relay preserves their bytes.
- An optional schema cannot redefine existing units, change standard books or otherwise be a prerequisite for the interpretation of standard records. A schema with such a dependency is declared with `required` true.
