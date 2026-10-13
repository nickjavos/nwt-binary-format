# Choose settings

| Setting | Option of `repack` | Guidance |
|---|---|---|
| Frame size | `--frame-bytes N`, from 48 to 16777216 | A larger frame compresses better and needs fewer reads for a long range. A query reads a whole frame even when one record matches, so a smaller frame serves narrow queries with fewer bytes. A record larger than the frame size gets a frame of its own. |
| Zstandard level | `--level N`, from 1 to 22 | A higher level gives a smaller file and a slower write. The level does not change how the file is read. |
| Raw frames | `--raw` | Writes every frame raw. Use it when readers run without a Zstandard library. |
| Summaries | `--no-summary` | Leaves out the `FRAME_SUMMARY` frames. Readers then skip frames by time only. |

Only `DATA` frames are compressed, and only when the compressed form is smaller. `INDEX` and `END` are always raw, so a reader finds them without a codec. Two writers with different versions of the Zstandard library produce different compressed bytes for the same records, so compare decoded records, not compressed files.
