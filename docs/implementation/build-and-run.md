# Build and run

Run the commands from the kit root. Each tab builds one codec, writes the conformance file, reads it back and compares the result with [all-records.nwt](files/samples/all-records.nwt), which the kit keeps in `fixtures/golden/`.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
mkdir -p work
python3 examples/python/nwt_example.py write-golden work/python.nwt
python3 examples/python/nwt_example.py read work/python.nwt work/python-again.nwt > work/python-fields.txt
cmp work/python.nwt fixtures/golden/all-records.nwt
cmp work/python-again.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: Rust -->
```bash
mkdir -p work
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example write-golden work/rust.nwt
examples/rust/target/debug/nwt-example read work/rust.nwt work/rust-again.nwt > work/rust-fields.txt
cmp work/rust.nwt fixtures/golden/all-records.nwt
cmp work/rust-again.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: C# -->
```bash
mkdir -p work
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll write-golden work/csharp.nwt
dotnet work/csharp/NwtExample.dll read work/csharp.nwt work/csharp-again.nwt > work/csharp-fields.txt
cmp work/csharp.nwt fixtures/golden/all-records.nwt
cmp work/csharp-again.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: C++ -->
```bash
mkdir -p work
c++ -std=c++20 -O2 -DNWT_ZSTD examples/cpp/main.cpp -o work/nwt-cpp -lzstd
work/nwt-cpp write-golden work/cpp.nwt
work/nwt-cpp read work/cpp.nwt work/cpp-again.nwt > work/cpp-fields.txt
cmp work/cpp.nwt fixtures/golden/all-records.nwt
cmp work/cpp-again.nwt fixtures/golden/all-records.nwt
```
<!-- /nwt-tabs -->

`cmp` prints nothing and exits with status 0 when the two files are byte-identical. That is the expected result in every tab.

Notes on the C++ build:

- When `libzstd` is outside the default search path of the compiler, add its include and library folders. With Homebrew on Apple silicon these are `-I/opt/homebrew/include -L/opt/homebrew/lib`.
- To build without Zstandard, leave out `-DNWT_ZSTD` and `-lzstd`.
- `examples/cpp/CMakeLists.txt` builds the same program with [CMake](https://github.com/Kitware/CMake) 3.16 or later. It links `libzstd` when it finds the library and builds a raw-only codec when it does not.

<!-- nwt-file: examples/cpp/CMakeLists.txt -->

```bash
cmake -S examples/cpp -B work/cpp-build
cmake --build work/cpp-build
```
