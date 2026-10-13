# Quotes and trading status

- `QUOTE` replaces the top of book of its instrument. A side is absent when its price is null; then its quantity and order count are 0. A present side has a quantity above 0.
- `BEST_QUOTE` keeps a state of its own. It names the publisher of each side in `bid_publisher_id` and `ask_publisher_id`, and it does not replace the `QUOTE` state.
- `STATUS` replaces the trading status of its instrument. It does not clear an order book.
- `OPTION_ANALYTICS` and `IMBALANCE` replace the latest record of their instrument.

A `GAP` on the channel invalidates the top of book, the best quote and the trading status of every instrument of that publisher and channel. Each is valid again when its next record arrives.
