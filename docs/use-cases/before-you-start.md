# Before you start

The recipes use the `nwt` command, `tools/nwt.py`, and the Python reference codec, `examples/python/nwt_example.py`. Both run on Python 3.10 or later with the standard library only.

1. Download [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip) and unpack it.
2. Open a terminal in the kit root. Every command on this page runs from there.
3. Create the folder for the output files:

   ```bash
   mkdir -p work
   ```

Each recipe names its input as a download link. In the kit, the same files are in `fixtures/real/`, `fixtures/real-reference/` and `fixtures/real-market/`, and the commands use those paths. A recipe that has a Python program asks you to save it in `work/` and run it from the kit root.

Zstandard frames need the system [libzstd](https://github.com/facebook/zstd) (Python, C#, C++) or the [zstd](https://github.com/gyscos/zstd-rs) crate (Rust). Raw frames need no library. Only [Build an archive and query it](build-an-archive-and-query-it.md) writes Zstandard frames.
