# split

Writes one container for each record type, instrument or day of the input.

```bash
python3 tools/nwt.py split FILE DIR --by KEY
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `DIR` | Folder for the output files. It is created when it does not exist. |
| `--by type` | One file per record type, named `NN-name.nwt`, for example `22-corporate_action.nwt` |
| `--by instrument` | One file per instrument ID, named `instrument-ID.nwt` |
| `--by day` | One file per UTC date of `ts_event`, named `YYYY-MM-DD.nwt`. Records with a null `ts_event` go to `no-time.nwt`. |

Each output file has its own stream ID, renumbered sequences and an exact manifest. A record goes to exactly one file, and definitions are not repeated: the file of one day can use an instrument that is defined in the file of an earlier day. On success the command prints the number of files on standard error.

```bash
python3 tools/nwt.py split fixtures/real-market/equity-bars.nwt work/by-day --by day
ls work/by-day
```

```text
wrote 2 files to work/by-day
2025-09-16.nwt
2025-09-17.nwt
```
