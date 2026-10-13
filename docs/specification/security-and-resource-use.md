# Security and resource use

## Security

- NWT has no encryption, no digital signature, no entitlement enforcement and no tamper-resistant authentication.
- Use an authenticated, encrypted transport and access controls on stored objects.
- Where the authenticity of a stored object is required, sign or authenticate the complete immutable object externally.
- A CRC does not protect against intentional modification.
- A reader does not dereference URI metadata and does not load executable schema plug-ins automatically.

## Maximum sizes

| Item | Maximum |
|---|---|
| Metadata, `metadata_bytes` | 1,048,576 bytes |
| Frame payload, `stored_bytes` and `raw_bytes` | 16,777,216 bytes each |
| Record, `record_bytes` | 1,048,576 bytes |
| Zstandard window | 16,777,216 bytes |
| Levels on each side of the aggregate book, in `BOOK_SNAPSHOT` and in the book that `BOOK_DELTA` maintains | 1,024 |
| JSON nesting in `MANIFEST` and `PROVENANCE` | 16 levels |
| Entries in `publishers` and in `schemas` | 4,096 each |
| String property of `PROVENANCE` | 4,096 bytes |
| `text` of `SYSTEM` | 4,096 bytes |
| `details` of `CORPORATE_ACTION` | 65,535 bytes |
| Other texts and arrays | Stated with each field |

- These values are ceilings, not suggested allocation sizes.
- A reader can enforce lower, documented local maximums and return `RESOURCE_LIMIT`. It cannot drop data silently to stay within one.

## Unbounded quantities

The format does not bound the total length of a container or the number of frames, instruments, channels, live orders and corrections.

- A stateful consumer therefore needs configurable quotas, bounded buffering, disk-backed state or explicit resource failures.
- Never allocate from an unchecked product or sum.
- Enforce the window and output maximums of the decompressor before the output is materialized.

## Data quality

A valid CRC does not establish that the business data is correct. Negative prices, crossed books, stale timestamps and unusual but permitted values can be legitimate. A validator distinguishes a malformed encoding from a quality alert about the source.
