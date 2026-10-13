# Consolidated top of book: BEST_QUOTE

The kind `csv-cmbp1` reads a consolidated top-of-book export, in which each side of the best quote names the venue that set it. Every row becomes one `BEST_QUOTE`.

| Source column | NWT field | Rule |
|---|---|---|
| `bid_px_00`, `ask_px_00` | `bid_price`, `ask_price` | As for `QUOTE`. |
| `bid_sz_00`, `ask_sz_00` | `bid_quantity`, `ask_quantity` | As for `QUOTE`. |
| `bid_pb_00`, `ask_pb_00` | `bid_publisher_id`, `ask_publisher_id` | The venue ID of each side. 0 on an absent side. |

- Every venue ID that appears is declared in the manifest as a publisher.
- The export has no order counts: a present side has a null order count.
- `interval_ns` is 0, which marks an event-driven quote. `quote_flags` is 0.
- A trade row carries the publisher of the venue where the trade happened and restates the best quote under that publisher. The converter writes its `BEST_QUOTE` and counts the row in the provenance. The trade itself is not carried by this kind.

A `BEST_QUOTE` from the `option-best-quotes.nwt` sample:

<!-- nwt-file: fixtures/real-market/option-best-quotes.jsonl lines=3-3 -->
