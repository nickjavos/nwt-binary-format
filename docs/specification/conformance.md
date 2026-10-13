# Conformance

## How rules are stated

This specification uses no special requirement keywords. It states each rule as a fact about the format, in the present tense, and a rule has no exceptions. A conforming writer produces only containers in which every rule holds, and a conforming reader checks the rules of the capabilities it claims and reports an error for input that breaks one. A recommendation is introduced by "we recommend", and an implementation can depart from it for a documented operational reason.

## Scope

NWT is a container of framed, checksummed records. It carries normalized market data and reference data, and it has private record types for other event data. The same bytes serve a live byte stream and a file.

The format provides deterministic decoding, bounded memory use, several record types in one container, incremental streaming, nanosecond timestamps, exact decimal values and corruption detection.

The format does not define:

- datagram delivery;
- a socket handshake, subscription negotiation or authentication messages;
- distributed consensus or exactly-once application processing;
- arbitrary-precision decimals, or a decimal scale other than 10⁻⁹;
- encryption, signatures or authenticated containers;
- dictionary compression;
- a source cursor for replay;
- an index of definitions or of book state;
- corrections that span containers;
- metadata that changes inside a container.

`OPTION_DEF`, `SECURITY_DEF` and `CORPORATE_ACTION` carry the option, security-master and corporate-action fields listed on their record pages. Data beyond those fields, such as full terms and conditions or entitlement data, needs a private schema.

## Capabilities

A conformance claim names the capabilities it covers.

| Capability | Requirement |
|---|---|
| Core reader | Container, metadata, codec 0, frame integrity, record headers, `INDEX` and `END` |
| Core writer | Emits fully valid containers and the schemas it advertises |
| Zstandard reader or writer | Codec 1. Optional, and advertised explicitly |
| Store reader or writer | The [store profile](store-profile.md): `INDEX`, `FRAME_SUMMARY`, the optional `ordering` property and selective frame reads |
| Market-data reader | The rules of every standard schema in its supported subset |
| Lossless relay | Preserves all record bytes, including optional records it does not know |
| Semantic consumer | Refuses required schemas it does not support and reports the optional data it skips |

- A core reader can inspect records without interpreting their payloads.
- Successful framing is not market-data conformance. A reader that checks only the binary shape does not enforce the trade and book rules, the definition rules or the state rules.
- A reader that supports only codec 0 is conformant, but it cannot read every NWT file.
