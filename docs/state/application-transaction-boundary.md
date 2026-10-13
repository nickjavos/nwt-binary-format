# Application transaction boundary

A frame is the unit of integrity, and a consumer makes it the unit of commitment.

1. Verify the whole frame first: the header CRC-32C, the payload CRC-32C and the structure of every record.
2. Apply the records of the frame to a staged copy of the state.
3. Commit the staged state only when every record of the frame passes its rules. Otherwise discard it.
4. Keep an open snapshot private across commits. It becomes visible with `SNAPSHOT_END`, which can arrive several frames later.
5. Store the committed NWT position, stream ID and `frame_seq`, in the same transaction as the application state it produced.

A position alone does not make side effects happen exactly once. The position and the effects are committed together, or the effects are made safe to repeat.

`MarketState.apply` in the reference implementation changes its state while it checks a record. When it raises an error, discard that `MarketState` instance and rebuild the state from a verified position.
