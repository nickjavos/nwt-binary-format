# Why the format looks like this

Four choices explain most of the format.

- **Fields have a fixed width and a fixed place.** The price of a trade is always the 8 bytes at offset 48 of its record. A reader goes straight to a value and never searches for a separator.
- **Numbers are integers scaled by 10⁹.** A price of 177.03 is stored as the integer 177,030,000,000. Decimal fractions stay exact, which binary floating point does not promise.
- **Records are packed into frames.** A frame is checked, compressed and skipped as one piece. A damaged part of a file does not spoil the rest, and a reader passes over the frames it does not need.
- **A file can carry an index.** The index lists every frame with its position and its time range, so a query opens only the frames that can hold an answer.

The second choice is easy to see in any Python prompt. The first line adds two prices as binary floating point, the second adds the same prices as scaled integers:

```python
print(0.1 + 0.2)
print(100_000_000 + 200_000_000)
```

```text
0.30000000000000004
300000000
```

The integer result is exactly 0.3 × 10⁹. The sections below show the other three choices at work: a record byte by byte, a frame, and a query that reads part of a file.

[Specification: Design principles](../specification/file-structure.md#design-principles) · [Use NWT in practice](../USE-CASES.md)
