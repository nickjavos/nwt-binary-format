# Order-level book: MBO and TRADE

The kind `csv-mbo` reads an order-level export, in which every row is one event of one order. An `MBO` record carries the remaining size of an order, and the export carries size changes, so the converter tracks every live order of every book. A book is the set of orders of one publisher, channel and instrument.

| Source `action` | Records written | Rule |
|---|---|---|
| `R` | `MBO` CLEAR | Empties the book. |
| `A` | `MBO` ADD | The price and size of the row. An add for an order that is already in the book stops the conversion. |
| `C` | `MBO` MODIFY or DELETE | MODIFY with the remaining size, or DELETE when nothing remains. A cancel for an unknown order, or for more than the remaining size, stops the conversion. |
| `M` | `MBO` MODIFY | The price and size of the row. A change of side is written as DELETE and then ADD. A modify for an order that is not in the book is written as ADD and counted. |
| `T` | `TRADE` NEW | The price and size of the row. A trade row with no price or with size 0 is skipped and counted. |
| `F` | None, or `MBO` MODIFY or DELETE | Decided by the fill rule. See [Fills and cancels](#fills-and-cancels). |
| `N` | None | Skipped and counted as a row with no book effect. |

The other columns map as follows:

| Source column | NWT field | Rule |
|---|---|---|
| `order_id` | `order_id` | Kept. 0 on an order event stops the conversion. |
| `price` | `price` | Exact decimal. Null in a DELETE and a CLEAR. |
| `size` | `quantity` | In an `MBO`, the remaining size of the order after the event. In a `TRADE`, the traded size. |
| `side` | `side`, `aggressor` | In an `MBO`: `B` is 1 (bid), `A` is 2 (ask). In a `TRADE`, the aggressor: `B` is 1 (buyer), `A` is 2 (seller), `N` is 0 (unknown). |
| `flags` | None | Checked and not carried. The bit values 2, 8, 32 and 128 are allowed. Any other bit stops the conversion. |

- `priority` is null: the export gives no queue rank. `mbo_flags` is 0.
- `trade_id` counts 1, 2, 3 and so on for each book, in file order: the export has no trade identifier. `conditions` is 0.
- A book begins with a clear row. An add, a cancel or a modify before the first `R` row of its book stops the conversion.

## Derived price levels: BOOK_DELTA

`--emit-deltas` writes a second file of `BOOK_DELTA` records. They are derived: the export has no price-level rows, and the provenance of the file says so.

- After each order-level row is applied, every price whose aggregate changed gets one `BOOK_DELTA`: SET with the new aggregate size and order count, or DELETE when the level is empty.
- A clear row becomes CLEAR with `side` 0 and a null price.
- An order that moves to another price gives a delta for the old price and a delta for the new one.
- `LAST_IN_EVENT` (`delta_flags` bit 0) marks the last delta derived from each source row.
- A book with more than 1,024 price levels on one side stops the conversion: a `BOOK_DELTA` book holds at most 1,024 price levels on a side.
- The file has its own `INSTRUMENT_DEF` records and its own sequence numbers.

## Fills and cancels

An order-level export reports an execution against a resting order as up to three rows: a trade (`T`), a fill (`F`) that names the resting order, and a cancel (`C`) for the same order and size. `--fill-rule` states which row removes the size from the book.

| Fill rule | Fill row | Cancel row |
|---|---|---|
| `cancel-carries-fill` | Does not change the book. It is counted in the provenance. | Removes the filled size. |
| `fill-reduces` | Removes its size from the order, like a cancel. | Removes its own size as well. |

`cancel-carries-fill` is the default, and the samples are built with it. Choose `fill-reduces` for an export in which the cancel row does not repeat the size of the fill.

The first execution of the `equity-orders.nwt` sample shows the default rule. Source lines 18–20 are a sell of 180 at 177.03 against order 18315, which rested with 200:

| `action` | `side` | `price` | `size` | `order_id` |
|---|---|---:|---:|---:|
| `T` | `A` | 177.030000000 | 180 | 0 |
| `F` | `B` | 177.030000000 | 180 | 18315 |
| `C` | `B` | 177.030000000 | 180 | 18315 |

They become one `TRADE` (aggressor seller, quantity 180) and one `MBO` MODIFY that leaves order 18315 with 20:

<!-- nwt-file: fixtures/real-market/equity-orders.jsonl lines=18-19 -->
