# Change log

## 1.1-draft.1 — 13 October 2026

A backward-compatible extension of 1.0-draft.2. Types 1–9, the container header, the TLV encoding, the frame envelope, the record header, the INDEX and END frames, the checksums, and every byte of a 1.0 file are unchanged. A 1.0 file is a valid 1.1 input.

- Added thirteen standard record types: VENUE_DEF (10), OPTION_DEF (11), LISTING (12), STATISTICS (13), OPTION_ANALYTICS (14), BOOK_DELTA (15), IMBALANCE (16), SYMBOL_MAP (17), TRADE_QUOTE (18), BEST_QUOTE (19), FRAME_SUMMARY (20), SECURITY_DEF (21) and CORPORATE_ACTION (22).
- Types 1–9 keep the `spec_uri` `urn:nwt:spec:1.0`. Types 10–22 use `urn:nwt:spec:1.1`.
- The container `minor` is 1 exactly when the manifest declares a standard type 10–22. Private types do not count.
- Added the optional manifest property `ordering`: `none`, `ts_event`, or `instrument,ts_event`. It is a claim about byte order. A validator checks it against a full scan.
- Added FRAME_SUMMARY records, a richer INDEX use, and the store profile: 1 MiB frames, Zstd, INDEX, FRAME_SUMMARY and `ordering`. Records are never reordered.
- Added a record-type registry, new enum and mask rules, new text limits, and a section of conformance tests for the new types.
- Removed every comparison to other formats. The specification describes NWT on its own, and its conversion section is general guidance.
- Added a 22-type conformance set in `fixtures/v1.1/`: 48 catalog records, a multi-frame container, Zstd variants, JSON and CSV exports, and malformed files that every reader must reject.
- Added codec support for Zstd (codec 1) in all four examples, plus the `write-v11`, `to-json`, `to-csv` and `bench` commands.
- Added the Python `nwt` tool: inspect, validate, cat, extract, merge, split, repack, query, resolve, stats and convert.
- Added converters for market data and reference data, and real fixtures built from them.
- Rewrote the documents for 22 types. The field-reference tables for all types are generated from `schemas/records.json`, so they cannot drift from it.
- Added a single-file HTML build (`tools/build_html.py`) and a static documentation site (`tools/build_site.py`).

Not done in this release: the Rust codec is written but not compiled or run; the store features, converters and semantic checks exist in Python only; no live transport.

## 1.0-draft.2 — 23 September 2026

No wire-layout, type-ID, field-scale, or schema-version changes.

- Added a complete reference covering every common header, payload, text, depth-level, container, metadata, frame, index, and END field.
- Added executable Rust, Python, C#, and C++ examples for all nine schemas.
- Expanded the two-record vector to 49 scenarios, 17 DATA frames, one INDEX frame, and one END frame.
- Added per-record binary/JSON examples, all-language standalone-record commands, and field reports.
- Added trade lifecycle, MBO snapshot/recovery, status, and gap walkthroughs, plus a Python semantic replay example.
- Added four-language interoperability, integer boundary, malformed-wire, and semantic negative tests.
- Clarified educational example limitations, deterministic fixture identities, and structural versus semantic validation.
- Retained draft.1's original fixture unchanged under fixtures/legacy.
