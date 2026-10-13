# Ten-level depth: BOOK_SNAPSHOT

The kind `csv-mbp10` reads a depth export. Every row becomes one `BOOK_SNAPSHOT` with `book_flags` 1 (depth-limited).

| Source column | NWT field | Rule |
|---|---|---|
| `bid_px_NN`, `ask_px_NN` | `bid_price`, `ask_price` of level NN | Exact decimal. Empty means that the side is absent at this level. |
| `bid_sz_NN`, `ask_sz_NN` | `bid_quantity`, `ask_quantity` | As for `QUOTE`. |
| `bid_ct_NN`, `ask_ct_NN` | `bid_count`, `ask_count` | As for `QUOTE`. |

- `NN` runs from `00`, the best level, to `09`. Each level pairs one bid and one ask.
- Trailing levels that are empty on both sides are dropped. A book with three bid levels and five ask levels gives five levels, with the bid absent in the last two.
- An empty level above a filled one stops the conversion. So do bid prices that do not strictly fall and ask prices that do not strictly rise.
- A trade row restates the book. The converter writes its snapshot and counts the row in the provenance. The trade itself is carried by `csv-mbo` and `csv-mbp1`.

A snapshot from the `depth-10.nwt` sample:

<!-- nwt-file: fixtures/real-market/depth-10.jsonl lines=3-3 -->
