# Reader and writer requirements

## Incremental decoding

A reader that receives bytes incrementally follows this state machine.

```text
READ_HEADER        validate header CRC, version, size maximums
READ_METADATA      validate metadata CRC, TLV elements, manifest
READ_FRAME_HEADER  validate header CRC, kind, order, size maximums
READ_PAYLOAD       obtain exactly stored_bytes plus outer padding
DECOMPRESS         bounded decode for the codec
VALIDATE_PAYLOAD   CRC, records or index or end, semantic prerequisites
COMMIT_FRAME       expose validated records, advance expected sequences
                   repeat from READ_FRAME_HEADER until END
DONE               reject trailing bytes
```

- A temporary lack of bytes returns `NEED_MORE`. It is not corruption.
- End of input while more bytes are expected returns `TRUNCATED`.
- A record is not presented as verified before the CRC and the structural validation of its frame succeed.
- We recommend that a semantic consumer validate changes against temporary state and commit them only after the whole frame passes the semantic checks.
- A snapshot that spans several frames stays private until `SNAPSHOT_END`.

## Record iteration

```text
offset = 0; parsed = 0
while offset < raw_bytes:
    require raw_bytes - offset >= 48
    n = read_u32_le(payload, offset)
    require 48 <= n <= 1048576 and n % 8 == 0
    require n <= raw_bytes - offset
    validate_common_header(payload[offset:offset+n])
    validate_declared_schema_or_skip_optional(...)
    offset += n; parsed += 1
require offset == raw_bytes and parsed == record_count
```

The loop shows record framing only. CRCs, scopes, size maximums, reserved fields, timestamps and state rules apply in addition.

## Error categories

We recommend that implementations expose stable machine-readable error categories.

| Category | Condition |
|---|---|
| `BAD_MAGIC` | The container magic or a frame magic does not match |
| `UNSUPPORTED_VERSION` | A version value that the reader does not support |
| `UNSUPPORTED_CODEC` | A codec that the reader does not support |
| `UNSUPPORTED_REQUIRED_SCHEMA` | A required schema that the reader does not know |
| `INVALID_METADATA` | The metadata is not valid: its CRC, a TLV element, the manifest or the provenance |
| `BAD_HEADER_CRC` | The CRC of a container header or a frame header does not match |
| `BAD_PAYLOAD_CRC` | The CRC of a frame payload does not match |
| `INVALID_LENGTH` | A length is too short, too long, misaligned or inconsistent |
| `NONZERO_RESERVED` | A reserved field or a padding byte is not zero |
| `INVALID_RECORD` | A record breaks the layout rules of its schema |
| `SEQUENCE_ERROR` | A frame sequence or a record sequence is not the expected one |
| `SEMANTIC_ERROR` | A record breaks a state rule, such as a delta against an invalid book |
| `DECOMPRESSION_ERROR` | A compressed payload cannot be decoded under the rules of the codec |
| `RESOURCE_LIMIT` | A local maximum of the reader is exceeded |
| `TRUNCATED` | The input ends while more bytes are expected |
| `ABORTED` | The `END` frame reports that the producer aborted |
| `TRAILING_BYTES` | Bytes follow the `END` frame |

- We also recommend that an error include the byte offset, the frame sequence, the record position and the schema, when they are known.
- Logs never treat untrusted text as a format string or as a command.
- A reader can offer raw inspection of data whose rules it does not support. It marks that mode and what it does not check.

## Writer obligations

A writer does all of the following:

- validates the constraints of a schema before it emits a record;
- uses checked integer arithmetic;
- sets all reserved bytes to zero;
- computes exact counts and timestamp bounds;
- computes the CRC of the raw payload before optional compression, and the header CRC last;
- emits definitions and state initialization before the data that depends on them.

A writer cannot change the manifest after it has been sent. A new publisher or schema needs a new container.

We recommend three practices for a writer:

- Deterministic serialization, so that repeated conversion runs give the same records. Fresh stream IDs and creation times still differ.
- An aborted `END` from a writer that cannot finish, when it can still emit one. Without it, readers classify the prefix as incomplete.
- A published file that is written to a temporary path, completed, flushed and then renamed atomically, within the guarantees of the file system.
