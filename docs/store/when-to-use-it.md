# When to use it

Use the store profile for a complete file that is read many times and queried by time, by record type or by instrument: a daily archive, an object in a bucket that is read with range requests, a research file on disk.

Write an ordinary container while a feed is live, and repack it as a store file when it is closed. The `INDEX`, the summaries and the `ordering` declaration describe the whole file, so a writer produces them when the last record is known.

A consumer that replays a whole file reads a store file like any other container.
