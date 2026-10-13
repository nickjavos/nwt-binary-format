# Top of book: QUOTE and TRADE_QUOTE

The kind `csv-mbp1` reads a top-of-book export. Every row becomes a `QUOTE` with the book columns of the row. A trade row (`action` `T`) also becomes a `TRADE_QUOTE`, written after its `QUOTE`. On a trade row the book columns are the top of book at the trade.

| Source column | NWT field | Rule |
|---|---|---|
| `bid_px_00`, `ask_px_00` | `bid_price`, `ask_price` | Exact decimal. Empty means that the side is absent. |
| `bid_sz_00`, `ask_sz_00` | `bid_quantity`, `ask_quantity` | A present side with size 0, or a size on a side with no price, stops the conversion. |
| `bid_ct_00`, `ask_ct_00` | `bid_order_count`, `ask_order_count` | A count of 0 on a present side is written as a null count and counted in the provenance. |
| `price` | `price` | `TRADE_QUOTE` only. The trade price. |
| `size` | `quantity` | `TRADE_QUOTE` only. The traded size. |
| `side` | `aggressor` | `TRADE_QUOTE` only. `B` is 1 (buyer), `A` is 2 (seller), `N` is 0 (unknown). |

- `quote_flags` is 0. In a `TRADE_QUOTE`, `trade_id` is 0, because the export has no trade identifier, and `conditions` is 0.
- A trade row with no price or with size 0 gives its `QUOTE` and no `TRADE_QUOTE`. The provenance counts it.
- `TRADE` records from an order-level export and `TRADE_QUOTE` records from a top-of-book export describe the same trades. The converter writes them to different files.

The first `TRADE_QUOTE` of the `equity-quotes.nwt` sample is the same trade as in [Fills and cancels](order-level-book-mbo-and-trade.md#fills-and-cancels):

<!-- nwt-file: fixtures/real-market/equity-quotes.jsonl lines=10-10 -->
