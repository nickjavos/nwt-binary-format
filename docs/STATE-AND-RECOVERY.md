# State and recovery

This page describes the state a consumer keeps while it reads NWT market data, and how it restores that state after a loss. It is for engineers who build order books, trade tapes or reference stores from NWT records. The rules come from the [Specification](specification/ordering-gaps-snapshots-and-replay.md); their reference implementation is `examples/python/market_state.py`.

## Sections

- [State a consumer keeps](state/state-a-consumer-keeps.md): A consumer starts with no state: every order book, quote and trading status is unknown.
- [Sequence numbers and ordering](state/sequence-numbers-and-ordering.md): NWT has three counters.
- [Order-level book state](state/order-level-book-state.md): An `MBO` record changes the order-level book of one publisher, channel and instrument.
- [Aggregate book with snapshots and deltas](state/aggregate-book-with-snapshots-and-deltas.md): The aggregate book holds price levels, not orders: for each side, a quantity and an order count per price.
- [Quotes and trading status](state/quotes-and-trading-status.md): How QUOTE, BEST_QUOTE, STATUS, OPTION_ANALYTICS and IMBALANCE records replace state, and what a GAP invalidates.
- [Trades and corrections](state/trades-and-corrections.md): A trade is identified by `trade_id` within its publisher, channel and instrument.
- [Reference data and statistics](state/reference-data-and-statistics.md): Reference records describe venues, instruments, symbols and corporate events.
- [Gaps and recovery](state/gaps-and-recovery.md): A transfer failure and a source failure are different events, and a consumer handles them differently.
- [Selective reads, summaries and state](state/selective-reads-summaries-and-state.md): A reader that uses `INDEX` frames and `FRAME_SUMMARY` records to read only some frames also skips the state that the other frames build.
- [Application transaction boundary](state/application-transaction-boundary.md): A frame is the unit of integrity, and a consumer makes it the unit of commitment.
- [Worked sequence](state/worked-sequence.md): The conformance file [all-records.nwt](files/samples/all-records.nwt) holds 47 records in frames of 3.
- [Run the state rules](state/run-the-state-rules.md): How to run examples/python/market_state.py on a container and read the summary of the final state.
