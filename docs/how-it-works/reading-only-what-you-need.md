# Reading only what you need

A store file is an ordinary container written with large compressed frames, an index and one `FRAME_SUMMARY` record for every frame. A reader starts at the `END` frame, reads the index and the summaries, and learns the time range, the record types and the instrument range of every frame. It then reads only the frames that can hold a match. The result holds the same records in the same order as a full scan with the same filter. It does not include the definitions and the book state that the skipped frames built, so it is a partial read.

![In a store file a reader goes from the END frame to the INDEX frames, then to the summary frames, and reads only the DATA frames that can hold a match](../diagrams/selective-read.svg "From END to INDEX to the summaries, then to the chosen frames")

[Store profile](../STORE.md) · [Specification: Store profile](../specification/store-profile.md) · [Size and speed](../PERFORMANCE.md)
