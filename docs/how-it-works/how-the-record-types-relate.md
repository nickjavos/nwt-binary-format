# How the record types relate

The 22 record types form three groups. `INSTRUMENT_DEF` and the six reference record types describe instruments and venues. The twelve market record types say what happened to one instrument, and each needs an `INSTRUMENT_DEF` for that instrument earlier in the file. The three stream record types describe the stream itself. Above all of them stands the `MANIFEST`, which declares the publishers and the record types before the first record.

![The MANIFEST, then three groups of record types: instruments and venues, market records and stream records, with the key of each group](../diagrams/data-model.svg "The manifest and the three groups of record types")

Records about the same instrument share the pair `publisher_id` and `instrument_id`. The pair joins a market record to the definition of its instrument, and the definition to the option terms, the listing, the symbols, the security record and the corporate actions of that instrument. A `VENUE_DEF` is keyed by its market identifier code.

![Market records, INSTRUMENT_DEF, OPTION_DEF, SYMBOL_MAP, CORPORATE_ACTION, SECURITY_DEF and LISTING attach to one key, publisher_id with instrument_id; VENUE_DEF is keyed by mic](../diagrams/data-model-keys.svg "The keys that join the records of one instrument")

[Specification: Record types](../specification/record-types.md) · [Field reference](../FIELD-REFERENCE.md) · [Glossary](../GLOSSARY.md)
