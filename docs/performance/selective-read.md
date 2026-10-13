# Selective read

The store file made from the larger file has 97 `DATA` frames of 1,048,576 raw bytes. A query for 60 seconds of `ts_event` from the middle of the file reads the `INDEX`, the frame of `FRAME_SUMMARY` records and the one frame whose time range overlaps the window. That is 2 `DATA` frames out of 97, and the count is exact: it follows from the file and the query, not from the machine.

<!-- nwt-chart: selective-read -->

The second chart gives the time of the same query in the Python `nwt` tool, from opening the file to the last matching record. The whole-file read scans every frame and applies the same filter. Both return the same 181 records. [Store profile](../store/how-a-reader-seeks-by-time-and-instrument.md) describes how a reader chooses the frames, and [The nwt command](../tools/query.md) describes the `query` command.

<!-- nwt-chart: selective-read-time -->

| Read | `DATA` frames read | Time, ms |
|---|---|---|
| Time-range query | 2 | 58.7 |
| Whole file | 97 | 6,410 |
