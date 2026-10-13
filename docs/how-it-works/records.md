# Records

Every record starts with the same 48-byte header: its length and type, its publisher, channel and instrument, two timestamps in nanoseconds and a sequence number. The fixed fields of the record type follow. Some record types end with a variable part: texts or order book levels. The fixed fields give its size, so a reader never scans for a terminator. Prices and quantities are 64-bit integers scaled by 10⁹.

![A record is a 48-byte header, the fixed fields of its record type, an optional variable part and zero padding; TRADE, BOOK_SNAPSHOT and INSTRUMENT_DEF show the three shapes](../diagrams/record-anatomy.svg "A record: the common header, the fixed fields, the variable part and the padding")

[Specification: Record header](../specification/record-header.md) · [Field reference](../FIELD-REFERENCE.md) · [Record types](../records/INDEX.md)
