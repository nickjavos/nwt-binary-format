# Conversion from other formats

Data in another format needs an explicit converter. Broad concepts such as instrument identity, event time, receive time, prices and message types can be mapped. Sizes, type IDs, flags, sequence meanings, metadata and framing cannot be copied by assumption. The author of a converter reads the definition of the source format for every field they map.

| Input concept | NWT treatment |
|---|---|
| Publisher and instrument identity | Allocate stable IDs. Keep the mapping in converter metadata or in reference data. Where the source has numeric IDs, keep their numbers |
| Event and receive timestamps | Convert the clock semantics. Map source nulls to NWT nulls |
| Fixed-point or decimal price | Parse with integer arithmetic. Rescale with checked arithmetic and exactness checks |
| Integer or fractional size | Convert to a quantity × 10⁹ in an explicitly defined unit |
| Sequence of the exchange | Do not copy it into the NWT output sequence. Keep it in a private schema or in `details` if it is needed |
| Feed action and flags | Map only when the meaning matches. Otherwise reject, or count the loss in `PROVENANCE` |
| Order-level feed | Track each order and emit `ADD`, `MODIFY` or `DELETE` with the remaining size |
| Book update with several levels | Rebuild an aggregate snapshot, or emit [`BOOK_DELTA`](../records/BOOK_DELTA.md) |
| Instrument definition of the source | Fill the available fields. Keep other necessary fields in a private schema |
| Symbol directory or security master | Use `LISTING`, `SYMBOL_MAP`, `SECURITY_DEF` and `VENUE_DEF`. Do not guess a field that the source lacks |
| Late correction outside the export range | Include the original lifecycle context, or reject the conversion to standard `TRADE` records |

A converter follows these rules:

- It claims a lossless conversion only when it retains every required source field and every semantic distinction.
- It fails on an unknown source code. It does not guess.
- It fails on a text that exceeds a maximum length. It does not truncate.
- It never reorders records.
- It parses and prints decimals with integer arithmetic. No floating-point value enters a conversion.
- When it rounds, it reports the loss to the caller and records the policy and the count in `PROVENANCE`. Recording the policy does not make a lossy conversion lossless.
- Source codes that it keeps as text, such as status and action letters, stay text codes. A schema does not turn them into enums until the code set is defined.
- Facts that the source does not have stay "unknown". They are not filled in from other fields.

**Text exports.**

- In CSV and JSON exports, the recommended rendering is an integer decimal string or an unambiguous time string for a timestamp, and an exact decimal string for a price or a quantity.
- JavaScript numbers cannot represent every `u64` and `i64` value exactly. We recommend `BigInt` or a lossless integer library.
- A reverse converter validates ranges and nulls. It never rounds through floating-point intermediates.
- A text rendering of records, including the decimal strings that the reference codecs print, is a view. It is not an alternative wire format, and it does not change the number rules of `MANIFEST`.
