# resolve

Looks up the instrument that a symbol or an identifier names.

```bash
python3 tools/nwt.py resolve FILE SYMBOL [--at TIME] [--symbology KIND] [--publisher ID]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container with `SYMBOL_MAP` or `SECURITY_DEF` records and an `INDEX` |
| `SYMBOL` | Text to look up: a symbol, an ISIN, a CUSIP or a FIGI |
| `--at TIME` | Moment to look up, in one of the forms of [Filters](run-it.md#filters). The default is any time. |
| `--symbology KIND` | Kind of symbol to match: `native`, `osi`, `isin`, `figi`, `root`, `continuous` or `cusip`. The default is every kind. |
| `--publisher ID` | Publisher to search. The default is every publisher. |

The command prints one JSON line per match and exits with status 1 and `no mapping found for SYMBOL` when there is none.

- **`SYMBOL_MAP`.** A record matches when its symbol text equals `SYMBOL`. The line holds `source`, `publisher_id`, `instrument_id`, `symbology` (1 native, 2 OSI, 3 ISIN, 4 FIGI, 5 root, 6 continuous), `valid_from_ns`, `valid_to_ns` and `symbol`. The interval is half-open: with `--at T`, a record matches when `valid_from_ns` is at or before T and T is before `valid_to_ns`. An open end prints as `18446744073709551615`. Without `--at`, every interval of the symbol is printed.
- **`SECURITY_DEF`.** A record matches when `SYMBOL` equals its ISIN, its CUSIP, its composite FIGI or its FIGI. The line holds `source`, `publisher_id`, `instrument_id`, the kind of identifier that matched, and the symbol and identifiers of the listing. The latest record of each publisher and instrument counts; with `--at T`, records with a `ts_event` after T are ignored.
- `--symbology cusip` searches `SECURITY_DEF` records only.

A symbol from the sample [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt):

```bash
python3 tools/nwt.py resolve fixtures/real/listings-nasdaq.nwt AAPL
```

```text
{"source":"SYMBOL_MAP","publisher_id":"1","instrument_id":"4519135547670130507","symbology":"1","valid_from_ns":"1791907860000000000","valid_to_ns":"18446744073709551615","symbol":"AAPL"}
```

An ISIN from the sample [secmaster-us.nwt](files/samples/secmaster-us.nwt). Two listings carry it:

```bash
python3 tools/nwt.py resolve fixtures/real-reference/secmaster-us.nwt US78462F1030
```

```text
{"source":"SECURITY_DEF","publisher_id":"1","instrument_id":"1688030","identifier":"isin","symbol":"SPY","isin":"US78462F1030","cusip":"78462F103","composite_figi":"BBG000BDTBL9","figi":""}
{"source":"SECURITY_DEF","publisher_id":"1","instrument_id":"11756875","identifier":"isin","symbol":"SPY","isin":"US78462F1030","cusip":"78462F103","composite_figi":"BBG000BDTBL9","figi":"BBG000BDTF76"}
```
