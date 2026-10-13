# Extend the schema

The schema file `schemas/records.json` is the single description of the record layouts. It has three parts: `header`, the ten fields of the 48-byte record header; `level`, the fields of one depth level; and `schemas`, one entry per record type. An entry gives the type number, the name, the schema version, the fixed size, the fields in wire order with width and signedness, the names of the texts, and the rules the codecs enforce: `enums`, `masks`, `text_limits` and `text_exact`. This is the entry for `BOOK_DELTA`:

<!-- nwt-file: schemas/records.json lines=1232-1300 -->

The catalogs are the example records the codecs write. `fixtures/catalog-golden.json` with `fixtures/manifest-golden.json` is the source of the conformance files, and `fixtures/catalog.json` with `fixtures/manifest.json` is the source of the container that `write` produces.

The four codecs take these files in two ways:

- Rust includes them at compile time with `include_str!`, and C# embeds them as resources through `NwtExample.csproj`.
- Python and C++ use generated copies, `examples/python/example_data.py` and `examples/cpp/example_data.hpp`, so that each runs from its own folder.

To change a layout or add a record:

1. Edit `schemas/records.json`, and add or change the catalog entries that use the layout.
2. Regenerate the embedded copies:

   ```bash
   python3 tools/sync_embedded_data.py
   ```
3. Rebuild the Rust, C# and C++ codecs as in [Build and run](build-and-run.md).
4. Regenerate the files under `fixtures/`. This step needs `libzstd`.

   ```bash
   python3 tools/generate_fixtures.py
   ```
5. Compare the four codecs again as in [Check a codec against the conformance files](check-a-codec-against-the-conformance-files.md).

Rules that hold across records, such as the order book transitions, belong to `examples/python/market_state.py`, which reads the decoded records.

A layout that is in use never changes. The [Specification](../SPECIFICATION.md) fixes the layout of every pair of record type and schema version: a new field needs a new schema version, and a private record type takes a number from 32,768 to 65,534 and its own `spec_uri` in the manifest.
