# Licenses

This page lists the third-party software that the reference codecs and the documentation site use, the license of each component, and the notices that apply to the sample data. Read it before you redistribute the kit or any file made from the samples.

## Reference codecs

| Component | Used by | License | How it is supplied |
|---|---|---|---|
| [nlohmann/json](https://github.com/nlohmann/json) 3.12.0 | C++ | MIT | Bundled as `examples/cpp/vendor/json.hpp`, with its license text in `examples/cpp/vendor/LICENSE.MIT` |
| [serde](https://github.com/serde-rs/serde), [serde_json](https://github.com/serde-rs/json) | Rust | MIT OR Apache-2.0 | Fetched by Cargo at build time |
| [zstd](https://github.com/gyscos/zstd-rs) crate | Rust, optional | MIT | Fetched by Cargo at build time |
| [libzstd](https://github.com/facebook/zstd) | Python, C#, C++ | BSD or GPLv2, at the user's choice | System library |

**nlohmann/json.** The source is the [3.12.0 release](https://github.com/nlohmann/json/releases/tag/v3.12.0). The SHA-256 of the bundled `json.hpp` is `aaf127c04cb31c406e5b04a63f1ae89369fccde6d8fa7cdda1ed4f32dfc5de63` and matches the checksum of the upstream release.

**Rust crates.** The Rust codec uses serde, serde_json, the optional zstd crate and their transitive dependencies. `Cargo.lock` records the exact version and the registry checksum of each package. Cargo fetches the source code of the dependencies at build time, and the kit does not bundle it. The notices and licenses of each crate are in its package.

**Zstandard.** Frames stored with codec 1 use the system library libzstd, which the authors of Zstandard release under the BSD license or GPLv2, at the user's choice. Python and C# load it at run time. C++ links it when built with `-DNWT_ZSTD`. The kit does not bundle it. The source is the [Zstandard repository](https://github.com/facebook/zstd).

Python and C# use their standard libraries for everything else.

## Documentation site

The static site, generated into `site/nwt-bin-format/`, bundles the files below. The license text of each is copied next to it in `assets/licenses/`.

| Component | License | Source |
|---|---|---|
| [Inter](https://github.com/rsms/inter) and [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) variable fonts | SIL Open Font License 1.1 | Distributed through the [Fontsource](https://github.com/fontsource/fontsource) packages |
| [Hotwire Turbo](https://github.com/hotwired/turbo) 8.0.23 | MIT | [hotwired/turbo](https://github.com/hotwired/turbo) |
| [Vue](https://github.com/vuejs/core) 3.5.43 | MIT | [vuejs/core](https://github.com/vuejs/core) |

The site loads no resource from another host.

## Sample data

The samples are small files for learning the format. Do not use them for trading, pricing or any other decision.

**Samples made from public files.** `venues`, `listings-nasdaq`, `listings-other` and `options` are converted from files that their publishers make available to the public: the ISO 10383 list of market identifier codes and the symbol directories of an exchange. [Reference data samples](docs/REAL-DATA.md) names each source file and its address.

**Samples made from licensed data.** The market data samples and the `secmaster` and `corporate-actions` samples are converted from licensed market-data exports. This data is not public. The samples are kept small: the first few hundred or few thousand rows of a source file, and the one-minute bars of one symbol for one day.

> **Important:** Receiving the kit does not give you a license to this data. Check the license under which the data was obtained before you redistribute these files or anything converted from them.

[SHA256SUMS.txt](files/SHA256SUMS.txt) lists the SHA-256 of every hosted file. [Market data samples](docs/REAL-DATA-MARKET.md) describes what each market data sample contains and how it was made.
