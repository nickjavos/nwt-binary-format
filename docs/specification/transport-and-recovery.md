# Transport and recovery

## Reliable byte streams

Over TCP, TLS or a reliable QUIC stream, the sender transmits one container header, the metadata and then the frames.

- The byte stream provides no message boundaries. One read can contain one byte, part of a header, several records or many frames. A reader supports arbitrary fragmentation and coalescing.
- Connection setup, credentials, the requested datasets and schemas, and the agreement on codecs take place in the control plane of the hosting service, before the NWT bytes begin.
- An API that serves NWT documents its authentication, request syntax, quotas, retry policy and allowed codecs separately.
- A producer cannot send a codec that the agreed capability set excludes.
- In an HTTP response, the NWT object is the body, with the private media type where appropriate.
- When byte offsets or range access matter, we recommend the frame compression of NWT without an additional HTTP compression wrapper.
- Object storage holds the same byte representation.

## Backpressure and heartbeat

- We recommend that producers bound their queues and flush a frame on a configured batch size or on a latency threshold.
- A heartbeat is an ordinary `SYSTEM` record in a `DATA` frame. It consumes a record sequence and a frame sequence.
- The heartbeat interval and timeout are policies of the service. They are not derived from NWT.
- A producer that loses source data through overflow reports a `GAP` before it resumes the affected records, or it terminates abnormally. It cannot hide dropped events behind contiguous output sequences.
- When backpressure blocks transmission, a heartbeat can be delayed too. Missing heartbeats alone do not show the cause.

## Resume and byte ranges

- Exact resume is allowed only against an immutable container with the same stream ID and a verified header and metadata.
- A client records the byte offset and the frame sequence after the last fully verified frame. The service can resume at that frame boundary, with the original bytes and sequences.
- The resumed suffix continues a transport. It is not a standalone NWT object, and it needs the context that the client has already validated.
- A standalone export that starts at a later logical time is a new container: a new stream ID, a new manifest, sequences that start at their initial values, and the definitions, snapshots and lifecycle context that its records need.
- An API that offers semantic resume defines its source cursor and its gap policy separately.
- Retransmission alone does not give exactly-once side effects in an application. An application must coordinate its processed positions durably with its own state or transactions.

## Damaged archives

- A strict reader stops at corruption.
- A separate salvage mode can scan forward for the frame magic, validate candidate headers, bounds, decompression, checksums and record structure, and recover later raw records. A match of the magic alone is insufficient.
- Salvage output uses a new stream ID and describes the omitted regions. It restores the semantic prerequisites or stays explicitly partial.
- A frame with a valid CRC cannot rebuild state that was lost before it.
