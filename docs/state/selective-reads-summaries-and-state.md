# Selective reads, summaries and state

A reader that uses `INDEX` frames and `FRAME_SUMMARY` records to read only some frames also skips the state that the other frames build. Such a read is correct for questions that need no earlier state, and incomplete for questions that do.

| Question | Frames it needs |
|---|---|
| Trades or quotes of one instrument in a time range, as raw records | The frames that can hold a match |
| Units and identity of those records | Also the frames with the `INSTRUMENT_DEF` records |
| The order-level book at a time | Every frame from the last `CLEAR` or completed snapshot of the book, in file order |
| The aggregate book at a time | Every frame from the last `BOOK_SNAPSHOT` of the book, in file order |
| The current statistic, listing or security record | Every frame that can hold a record with that key |

A store file changes which frames are cheap to find. It does not change the rules of replay: the result of a selective read is labelled partial and is not presented as a reconstructed order book. The [Store profile](../store/what-a-partial-read-returns.md) describes what such a read returns.
