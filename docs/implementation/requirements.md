# Requirements

Each reference codec is one program. Build the ones you need.

| Codec | Source | Toolchain | Libraries |
|---|---|---|---|
| Python | `examples/python/nwt_example.py` | Python 3.10 or later | Standard library only |
| Rust | `examples/rust/src/main.rs` | [Rust](https://github.com/rust-lang/rust) with [Cargo](https://github.com/rust-lang/cargo), edition 2021 | [serde](https://github.com/serde-rs/serde), [serde_json](https://github.com/serde-rs/json) and [zstd](https://github.com/gyscos/zstd-rs), pinned in `Cargo.lock` |
| C# | `examples/csharp/Program.cs` | [.NET SDK](https://github.com/dotnet/sdk) 10 | Base class library only |
| C++ | `examples/cpp/main.cpp` | A C++20 compiler: Clang or GCC | [nlohmann/json](https://github.com/nlohmann/json) 3.12.0, bundled in `examples/cpp/vendor/` |

Zstandard frames need the system [libzstd](https://github.com/facebook/zstd) (Python, C#, C++) or the [zstd](https://github.com/gyscos/zstd-rs) crate (Rust). Raw frames need no library.

- Install `libzstd` with your package manager: `brew install zstd` with Homebrew, `apt install libzstd-dev` on Debian and Ubuntu.
- Python and C# load `libzstd` at run time. Python looks for it with `ctypes.util.find_library("zstd")`; set the environment variable `NWT_ZSTD_LIB` to the path of the library to choose one yourself.
- C++ links `libzstd` at build time when you compile with `-DNWT_ZSTD`.
- Rust builds the `zstd` crate by default. `cargo build --no-default-features` builds the codec without it.

A codec that runs without the library reads and writes raw frames and rejects a Zstandard frame with the error `Zstd library not available`.

The licenses of the bundled and linked libraries are listed in [Licenses](https://github.com/nickjavos/nwt-binary-format/blob/main/THIRD-PARTY-NOTICES.md).
