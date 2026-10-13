# Implementation guide

This guide shows how to build and run the four reference codecs (Python, Rust, C#, C++), how their code is organised, and how to check your own reader or writer against the conformance files. It is for engineers who implement NWT Binary Format in a program of their own. Every reference codec reads and writes all 22 record types, raw and Zstandard frames, and the four produce byte-identical output for the conformance files.

## Sections

- [Requirements](implementation/requirements.md): Each reference codec is one program.
- [Build and run](implementation/build-and-run.md): How to build each reference codec, write the conformance file and compare it with the golden file.
- [Commands of the reference codecs](implementation/commands-of-the-reference-codecs.md): The four programs accept the same commands.
- [How a codec is organised](implementation/how-a-codec-is-organised.md): All four codecs have the same parts under the same names, so you can read one and find your way in the others.
- [Read a file](implementation/read-a-file.md): A reader validates a container in this order.
- [Write a file](implementation/write-a-file.md): The steps of a writer: open the container, check each record, fill a frame, seal the frame and close the container.
- [Encode one record](implementation/encode-one-record.md): The steps that turn the fields of one record into its encoded bytes.
- [Check a codec against the conformance files](implementation/check-a-codec-against-the-conformance-files.md): How to compare the output of a codec with the conformance files, step by step.
- [Extend the schema](implementation/extend-the-schema.md): The schema file `schemas/records.json` is the single description of the record layouts.
