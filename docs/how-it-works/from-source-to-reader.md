# From source to reader

A converter maps the rows of a source file to records, and a writer packs the records into one container. The same container serves as a file and as a live stream. A reader validates the container, decodes it in full, or reads only the frames that a query needs.

![Sources feed a converter and a writer, which produce one NWT container; the nwt command, the four reference codecs and selective readers read it](../diagrams/overview.svg "From source files to an NWT container and its readers")

[Use NWT in practice](../USE-CASES.md) · [The nwt command](../TOOLS.md) · [Implementation guide](../IMPLEMENTATION-GUIDE.md)
