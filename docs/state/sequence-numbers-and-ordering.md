# Sequence numbers and ordering

NWT has three counters. They measure different things and are never substituted for one another.

| Counter | Carried in | Counts | A hole means |
|---|---|---|---|
| `frame_seq` | Frame header | Frames of the container, from 0 | A transfer failure |
| `sequence` | Record header | Records of one publisher and channel in the container, from 1, across instruments and record types | A transfer failure |
| `first_missing_source_sequence`, `last_missing_source_sequence` | `GAP` record | Messages of the source feed, in the numbering of the source | A source failure that the producer reports |

- **The order of the bytes is the delivery order.** A consumer applies records in the order of the bytes. Timestamps can move backward, and the sequences of two channels do not define an order between the channels.
- **`sequence` is an output position, not an exchange sequence number.** The scope with publisher 0 and channel 0 belongs to the container: `SYSTEM` records of the container and `FRAME_SUMMARY` records count there.
- **A new container restarts the sequences.** A filtered, merged or re-framed export is a new container with a new stream ID and its own sequences from 1. Its sequences have no holes, so a hole never stands for a source gap.
- **Retries are deduplicated by identity.** For a retry that is identical byte for byte, the keys are stream ID with `frame_seq`, and stream ID with publisher, channel and `sequence`. The same identity with different bytes is an error.

The rules are in [Record header](../specification/record-header.md), [Delivery order](../specification/ordering-gaps-snapshots-and-replay.md#delivery-order) and [Deduplication](../specification/ordering-gaps-snapshots-and-replay.md#deduplication) of the Specification.
