# Third-party dependencies

C++ uses nlohmann/json 3.12.0, distributed under its included MIT license. Source: https://github.com/nlohmann/json/releases/tag/v3.12.0 . The included json.hpp SHA-256 is `aaf127c04cb31c406e5b04a63f1ae89369fccde6d8fa7cdda1ed4f32dfc5de63`, matching the upstream release checksum.

Rust uses serde and serde_json under their upstream MIT OR Apache-2.0 licenses, the optional zstd crate under MIT, and their transitive dependencies. Cargo.lock records exact package versions and registry checksums. Dependency source code is fetched by Cargo at build time, not bundled in this kit. Consult the respective crate packages for their notices and licenses.

Zstandard (codec 1) uses the system library libzstd, which Zstandard's authors release under the BSD license or GPLv2, at the user's choice. Python and C# load it at run time and C++ links it when built with `-DNWT_ZSTD`. It is not bundled in this kit. Source: https://github.com/facebook/zstd .

Python and C# use their standard libraries for everything else.

## Documentation site

The generated static site (`site/nwt-bin-format/`) bundles these files. Their licence texts are copied next to them in `assets/licenses/`.

- Inter and JetBrains Mono variable fonts, under the SIL Open Font License 1.1, distributed through the Fontsource packages.
- Hotwire Turbo 8.0.23, under the MIT license. Source: https://github.com/hotwired/turbo .
- Vue 3.5.43, under the MIT license. Source: https://github.com/vuejs/core .

The site loads no resource from another host. The single-file `NWT-Documentation.html` loads no external resource at all and contains no scripts from these packages.
