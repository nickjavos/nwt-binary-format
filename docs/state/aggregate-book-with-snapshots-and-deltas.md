# Aggregate book with snapshots and deltas

The aggregate book holds price levels, not orders: for each side, a quantity and an order count per price. `BOOK_SNAPSHOT` and `BOOK_DELTA` work on the same book.

- `BOOK_SNAPSHOT` replaces the whole book with at most 1,024 levels per side. It is complete in one record. A snapshot with 0 levels is an empty book.
- `BOOK_DELTA` changes one price level, or clears a side. Levels are keyed by price, not by rank.
- The book is valid after a `BOOK_SNAPSHOT`, or after a `BOOK_DELTA` with action `CLEAR` and `side` 0. A `GAP` on the channel invalidates it. Any other delta on a book that is not valid is the error `BOOK_DELTA needs a valid book`.

| Action | Fields | Effect |
|---|---|---|
| `SET` | Non-null price, quantity above 0, `side` 1 or 2 | Adds the level, or replaces its quantity and order count. |
| `DELETE` | Non-null price, quantity 0, null order count | Removes the level. The level is in the book, unless the book is depth-limited. |
| `CLEAR` | Null price, quantity 0, null order count | Empties one side, or the whole book when `side` is 0. |

- The flag `LAST_IN_EVENT` in `delta_flags` marks the last delta of one event of the source. A consumer that publishes the book to others does so after that delta.
- A snapshot with the depth-limited flag in `book_flags` reports the top ranks only. The book stays depth-limited until the next snapshot without the flag, and a `DELETE` for a price that the book does not hold is valid in that time.
- A side never holds more than 1,024 levels, so the book can always be sent again as one `BOOK_SNAPSHOT`.
- A book whose best bid is above its best ask is not an error.
- A `BOOK_SNAPSHOT` does not restore the order-level book, and an `MBO` record does not change the aggregate book.

The delta rules in the reference implementation:

<!-- nwt-file: examples/python/market_state.py lines=340-364 -->

The Specification defines these rules in [BOOK_SNAPSHOT](../records/BOOK_SNAPSHOT.md) and [BOOK_DELTA](../records/BOOK_DELTA.md).
