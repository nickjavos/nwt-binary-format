# merge

Combines two or more containers into one, in an order you state.

```bash
python3 tools/nwt.py merge OUT FILE FILE... --order POLICY [--stream-id HEX] [--created-ns NS]
```

| Argument | Meaning |
|---|---|
| `OUT` | Container to write |
| `FILE` | Two or more input containers |
| `--order concat` | Writes the inputs one after another, in the order given. Each input keeps its record order. |
| `--order ts_event` | Interleaves the inputs by `ts_event`. The command accepts only inputs that are in `ts_event` order. Records with equal times come in input order. A record with a null `ts_event` stays directly behind the record before it in its input. |
| `--stream-id HEX`, `--created-ns NS` | Same as for [extract](extract.md) |

`--order` is required: the tool does not choose an order for you.

- The output has a new stream ID and renumbered sequences. The dataset names and the producers of the inputs are joined with `+`.
- Inputs that share a publisher ID give it the same name and venue. Otherwise the command fails with `publisher N differs between the inputs`.
- With `--order ts_event`, an input that is out of order makes the command fail with `input N is not in ts_event order; use --order concat`.
- `merge` checks the framing and the manifests. Run `validate` on the result to check the state rules of the combined stream.

```bash
python3 tools/nwt.py merge work/quotes-and-orders.nwt fixtures/real-market/equity-quotes.nwt fixtures/real-market/equity-orders.nwt --order ts_event
python3 tools/nwt.py validate work/quotes-and-orders.nwt
```

```text
valid records=4419 data_frames=1 summaries=0 ordering=ts_event
```
