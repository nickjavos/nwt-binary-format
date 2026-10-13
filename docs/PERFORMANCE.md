# Size and speed

This page gives measurements of NWT Binary Format made on the files of this kit: the size of the same records as text and as NWT, the decode throughput of the four reference codecs, and the number of frames a time-range query reads. One script, `tools/bench.py`, produces every number, and you can rerun it on your own machine. The page is for engineers who choose a storage format for market data and want figures they can check.

## Sections

- [What was measured](performance/what-was-measured.md): The six samples and the larger file on which sizes and throughput are measured.
- [Bytes per record](performance/bytes-per-record.md): The size of each sample in NWT, CSV and JSON Lines, divided by its number of records.
- [Bytes per record with Zstandard](performance/bytes-per-record-with-zstandard.md): NWT compresses each `DATA` frame separately.
- [Size at one million records](performance/size-at-one-million-records.md): The larger file shows the same comparison for 1,000,000 records.
- [Decode throughput](performance/decode-throughput.md): The `bench` command of each reference codec loads the file into memory and then walks the container.
- [Selective read](performance/selective-read.md): The store file made from the larger file has 97 `DATA` frames of 1,048,576 raw bytes.
- [How to read these numbers](performance/how-to-read-these-numbers.md): The reference codecs are written for clarity and for byte-exact agreement with each other, and the throughput figures are those of this code.
