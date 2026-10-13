# The `nwt` command

`tools/nwt.py` inspects, checks, filters, repacks and queries NWT containers. It is Python 3.13, standard library only, and it sits on the reference codec in `examples/python/nwt_example.py` and the state rules in `examples/python/market_state.py`. Zstd frames need the system `libzstd`; without it, raw files still work.

All commands are run from the kit root. The path to the kit has a space in it, so quote it:

```sh
cd "/Users/nickjavos/Documents/Symbol API /NWT-v1.1-Developer-Kit"
python3 tools/nwt.py --help
```

The examples below read the real files in `fixtures/real-reference/` (a US security master and US corporate actions), `fixtures/real/` (symbol listings) and `fixtures/real-market/` (one trading day of order, quote and bar data). Commands that write a file write it to `work/`; create the folder first with `mkdir -p work`.

| Command | Does |
|---|---|
| [`inspect FILE`](#inspect) | Header, manifest, frame table, record counts by type |
| [`validate FILE`](#validate) | Structure, semantic rules, summaries and the ordering claim |
| [`cat FILE`](#cat) | Every record as one JSON object per line |
| [`extract FILE OUT`](#extract) | Records that match a filter, as a new container |
| [`merge OUT FILE...`](#merge) | Several containers under a stated ordering policy |
| [`split FILE DIR`](#split) | One container per type, instrument or day |
| [`repack FILE OUT`](#repack) | Re-frame and recompress as a store file |
| [`query FILE`](#query) | Read only the frames that can match |
| [`resolve FILE SYMBOL`](#resolve) | Look up a symbol, ISIN, CUSIP or FIGI |
| [`stats FILE`](#stats) | Sizes, bytes per type, compression ratio |
| [`convert KIND SRC OUT`](#convert) | Source file to container |

## Rules that hold for every command

- **No command reorders records.** Byte order is delivery order (specification section 9). `repack` changes framing and compression only. `extract`, `merge` and `split` keep the order of the records they keep.
- **New containers get new identities.** `extract`, `merge` and `split` write a container with a new random stream ID and sequences renumbered from 1 for each (publisher, channel), as specification section 7 requires. `repack` also gets a new stream ID but keeps every sequence. Pass `--stream-id HEX` (32 hex digits) and `--created-ns N` to `extract`, `merge` or `repack` when you need reproducible output.
- **Manifests are exact.** An output declares only the types it contains. Containers that gained or lost records never claim an `ordering` unless the records really have it.
- **Output is written to `OUT.tmp` and renamed on success.** A failed command does not leave a half-written `OUT`. `OUT` must not be the input file.
- **Errors.** Every failure prints `NWT error: ...` on stderr and exits with status 1. A file that ends early, in the middle of a header, metadata, a frame or before END, makes `inspect`, `validate`, `cat`, `stats`, `query`, `resolve` and every writing command fail with a message that contains `incomplete`. A codec-1 frame without `libzstd` fails with `Zstd library not available`.
- **`cat` streams.** It prints each frame's records after that frame has passed all its checks. If a later frame is bad, the earlier records are already on stdout and the command then exits with status 1. Use the exit status, not the amount of output, to decide whether a read succeeded.

### Filters

`extract` and `query` take the same filters. All are optional, and together they mean "and".

| Option | Meaning |
|---|---|
| `--type 2,TRADE` | Record types, as numbers or names, comma separated |
| `--instrument 2001,3000-3999` | Instrument IDs and inclusive ranges |
| `--from TIME` | `ts_event >= TIME` |
| `--to TIME` | `ts_event < TIME` (half open, like every interval in NWT) |

`TIME` is nanoseconds since 1970 (`1758020700000000000`), a date (`2025-09-16`, midnight UTC) or a UTC timestamp (`2025-09-16T11:05:00Z`, up to nine fractional digits). A record whose `ts_event` is null never matches `--from` or `--to`. Reference records such as `LISTING` often have a null `ts_event`, so a time filter drops them; filter those by type or instrument instead.

## inspect

```sh
python3 tools/nwt.py inspect fixtures/real-reference/secmaster-us.nwt
```

Prints text lines: the file size; the container header (version, `minor`, stream ID, creation time); the manifest (dataset, producer, profile, clock, `ordering`); one line per publisher and per declared schema; the PROVENANCE object when there is one; a frame table with one row per frame (sequence, kind DATA/INDEX/END, codec, byte offset, stored and raw bytes, record count, first and last event time, `-` for a null time); the END totals and status; and the number of records of each type. It reads the whole file, so a damaged or cut file fails here.

On a day of market data the frame table is how you see the framing:

```sh
python3 tools/nwt.py inspect fixtures/real-market/equity-orders.nwt
```

## validate

```sh
python3 tools/nwt.py validate fixtures/real-reference/corporate-actions-us.nwt
```

Runs, in order: the full structural scan (CRCs, lengths, sequences, declared types and publishers, index agreement); the manifest rules (BOOK_DELTA is declared required, FRAME_SUMMARY is not, types 10-19 are refused under the `generic-events` profile); every record through the semantic rules in `market_state.py` (specification section 3 and base sections 8-9: definitions before market data, book replay for BOOK_DELTA, option and instrument agreement, statistics null rules, imbalance side and quantity, symbol-map overlaps, venue MICs, quote presence rules, sorted `details` in CORPORATE_ACTION, delisting not before listing); the `ordering` claim in the manifest against the records; and, when FRAME_SUMMARY frames are present, every summary value against a full scan of its frame.

On success it prints one line, `valid records=... data_frames=... summaries=... ordering=...`, and exits 0. On the first problem it prints `NWT error: <reason>` and exits 1. The reason names the rule, for example `FRAME_SUMMARY for frame 3 disagrees with the file: type_mask` or `the manifest declares ordering ts_event but the records are not in that order`.

A container whose END reports `aborted` is structurally readable but fails validation with `aborted container`.

## cat

```sh
python3 tools/nwt.py cat fixtures/real-reference/secmaster-us.nwt --pretty | head -n 3
```

One JSON object per record, in the format of `to-json` in the reference codec (specification section 5.2 of the 1.1 design): decimal strings, no spaces, texts escaped. `--pretty` writes prices and quantities with nine fractional digits and times as `YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ`. Closing the pipe early (`| head`) ends the command quietly with status 0.

## extract

```sh
python3 tools/nwt.py extract fixtures/real-reference/corporate-actions-us.nwt work/one-listing.nwt --instrument 17103508
```

Reads the whole input (so it is fully validated), keeps the records that match the filters, and writes a new container with a new stream ID, sequences renumbered from 1, and a manifest that declares only the types kept. The PROVENANCE of the input is carried over with three added strings: `derived_by`, `derived_note` and `source_stream_ids`. FRAME_SUMMARY records are dropped because they describe the old framing; `repack` writes new ones. An empty result is an error (`no record to write`).

Extracting a symbol's records does not copy the definitions that came before them. The output is a partial view, and `validate` may report a missing definition for market-data types.

## merge

```sh
python3 tools/nwt.py merge work/reference.nwt fixtures/real-reference/secmaster-us.nwt fixtures/real-reference/corporate-actions-us.nwt --order concat
```

Combines two or more containers. **`--order` is required; merge refuses to guess.**

- `--order concat`: the inputs one after another, in the order given. Each input keeps its own record order.
- `--order ts_event`: interleaves the inputs by `ts_event`. Every input must already be in `ts_event` order, otherwise the command fails and names the input; equal times keep input order. A record with a null `ts_event` stays right behind the record before it in its own input. Records are never sorted within an input.

The output has a new stream ID and renumbered sequences. Datasets and producers are joined with `+`. The inputs must agree about any publisher ID they share (same name and venue). The command checks the manifest and the framing, not the meaning: run `validate` on the result.

## split

```sh
python3 tools/nwt.py split fixtures/real-reference/corporate-actions-us.nwt work/by-type --by type
```

Writes one container per key into the folder (created if needed). `--by type` makes `NN-name.nwt` (for example `22-corporate_action.nwt`), `--by instrument` makes `instrument-ID.nwt`, and `--by day` makes `YYYY-MM-DD.nwt` from the UTC date of `ts_event`, with `no-time.nwt` for records whose `ts_event` is null. Each file has its own stream ID, renumbered sequences and an exact manifest. Definitions are not copied into later files: a file for one day may use an instrument that is defined in an earlier day's file. When there are more than 64 keys the input is read once per batch of 64, so that at most 64 files are open at a time. On success it prints `wrote N files to DIR` on stderr.

## repack

```sh
python3 tools/nwt.py repack fixtures/real-reference/corporate-actions-us.nwt work/corporate-actions-us.store.nwt
```

Rewrites a container as a store file ([STORE.md](STORE.md)): same records, same order, same sequences; new stream ID; DATA frames of 1 MiB raw; Zstd level 3 where it makes a frame smaller; a fresh INDEX; FRAME_SUMMARY frames after the data; `ordering` declared in the manifest only when the records really are ordered. When the input already declares an ordering that is false, repack refuses.

| Option | Default | Meaning |
|---|---|---|
| `--frame-bytes N` | 1048576 | Raw bytes per DATA frame, 48 to 16777216 |
| `--level N` | 3 | Zstd level, 1 to 22 |
| `--raw` | off | No compression |
| `--no-summary` | off | Do not write FRAME_SUMMARY frames |

When `libzstd` is missing, repack prints `NWT notice: Zstd library not available; writing raw frames` on stderr and writes raw frames. The container `minor` follows the manifest, so a repacked 1.0 file becomes `minor` 1 as soon as FRAME_SUMMARY is declared. Old FRAME_SUMMARY records in the input are dropped and rebuilt.

To see what repack changed, compare the two files:

```sh
python3 tools/nwt.py stats fixtures/real-market/equity-quotes.nwt
python3 tools/nwt.py repack fixtures/real-market/equity-quotes.nwt work/equity-quotes.store.nwt
python3 tools/nwt.py stats work/equity-quotes.store.nwt
```

## query

```sh
python3 tools/nwt.py query work/corporate-actions-us.store.nwt --type CORPORATE_ACTION --instrument 17103508
```

Prints the matching records as JSON Lines (`--pretty` as in `cat`). It does not scan the file. It reads END (the last 96 bytes), then INDEX, then the trailing FRAME_SUMMARY frames, picks the DATA frames whose time range, type mask and instrument range can contain a match, and reads only those. Details are in [STORE.md](STORE.md). Its first output is one line on **stderr**:

```
# partial: earlier definitions and book state are not included
```

The line is the label required by specification section 11: results of a seek lack earlier definitions and book state, so they are not a reconstructed book. On a file without FRAME_SUMMARY frames, `query` still skips frames by time using INDEX, and reads the rest. A file without an INDEX (a container with DATA frames but no INDEX) is refused.

A time-window query on a day of quotes:

```sh
python3 tools/nwt.py query work/equity-quotes.store.nwt --type QUOTE --from 2025-09-16T11:05:00Z --to 2025-09-16T11:06:00Z
```

`query` checks the frames it reads (envelope, CRC, every record it prints), not the rest of the file. Use `validate` for that.

## resolve

```sh
python3 tools/nwt.py resolve fixtures/real/listings-other.nwt A --at 2026-10-14
python3 tools/nwt.py resolve fixtures/real-reference/secmaster-us.nwt US78462F1030
```

Answers "which instrument is this?" from SYMBOL_MAP (type 17) and SECURITY_DEF (type 21) records. The first form looks `A` up in the symbol maps; the second finds an ISIN in the security master. It prints one JSON line per match and exits 1 with `no mapping found for ...` when there is none.

- A SYMBOL_MAP match prints `source`, `publisher_id`, `instrument_id`, `symbology` (1 native, 2 OSI, 3 ISIN, 4 FIGI, 5 root, 6 continuous), `valid_from_ns`, `valid_to_ns` (a null end prints as `18446744073709551615`) and `symbol`. Intervals are half open: with `--at T` a map matches when `valid_from <= T < valid_to`, so the end time itself is **outside**. Without `--at` every interval of the symbol is listed. Root symbols (symbology 5) can match several instruments.
- A SECURITY_DEF match is found by ISIN, CUSIP or FIGI (`composite_figi` or `figi`). It prints the instrument and the listing's identifiers. The latest SECURITY_DEF per (publisher, instrument) counts; with `--at T`, records whose `ts_event` is after T are ignored.

Options: `--symbology native|osi|isin|figi|root|continuous|cusip` limits the kind of symbol (`cusip` looks only in security definitions); `--publisher ID` limits the namespace.

Looking up a time before the first interval fails, which shows the interval rule:

```sh
python3 tools/nwt.py resolve fixtures/real/listings-other.nwt A --at 2026-10-01
```

This exits 1.

## stats

```sh
python3 tools/nwt.py stats fixtures/real-market/equity-orders.nwt
```

Prints `key value` lines: file bytes; header and metadata bytes; DATA frame count, how many are Zstd, and stored and raw payload bytes; the compression ratio (raw payload bytes divided by stored payload bytes, DATA frames only, three decimals, `-` when there is no data); INDEX and END bytes; the record total; and one line per record type with its record count and record bytes. The ratio is computed with integers.

## convert

```sh
python3 tools/nwt.py convert --help
```

`convert KIND SRC OUT [--option value]` turns a source file into a container. The command is registered by `tools/nwt_convert.py`; it exists only when that file is present. The kinds, their options and the rebuild recipes for the real fixtures are in [REAL-DATA.md](REAL-DATA.md). Unknown kinds list the known ones.

## From Python

`tools/nwt.py` can be imported (put `tools` and `examples/python` on `sys.path`). Two functions are meant for other code:

- `summaries(reader)` returns the FRAME_SUMMARY records of a store file as a list of dicts of ints with the record's field names (`data_frame_seq`, `data_frame_offset`, `stored_bytes`, `codec`, `summary_flags`, `type_mask`, `min_instrument_id`, `max_instrument_id`), found through END and INDEX only. It returns `[]` for a file without summaries.
- `select(reader, types=None, instruments=None, t0=None, t1=None)` yields the raw bytes of matching records in file order. `instruments` holds IDs or `(low, high)` pairs; `t0 <= ts_event < t1`. Its result equals a full scan filtered the same way; it only reads fewer frames.

`reader` is an `nwt_example.Reader`, which takes a `read_at(offset, n)` function. See [STORE.md](STORE.md) for an example that counts the bytes fetched.
