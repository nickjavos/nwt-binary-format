#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
schema = json.loads((ROOT / "schemas/records.json").read_text())
catalog = json.loads((ROOT / "fixtures/catalog.json").read_text())
manifest = (ROOT / "fixtures/manifest.json").read_text().strip()
catalog_golden = json.loads((ROOT / "fixtures/catalog-golden.json").read_text())
manifest_golden = (ROOT / "fixtures/manifest-golden.json").read_text().strip()

python = 'import json\n\n'
for name, value in [("SCHEMA", schema), ("CATALOG", catalog), ("CATALOG_GOLDEN", catalog_golden)]:
    text = json.dumps(value, indent=2, ensure_ascii=False)
    python += f"{name} = json.loads({text!r})\n\n"
python += f"MANIFEST = {manifest!r}\n\nMANIFEST_GOLDEN = {manifest_golden!r}\n"
(ROOT / "examples/python/example_data.py").write_text(python)

cpp = "#pragma once\n"
for name, value in [
    ("schema_json", json.dumps(schema, indent=2)),
    ("catalog_json", json.dumps(catalog, indent=2, ensure_ascii=False)),
    ("manifest_json", manifest),
    ("catalog_golden_json", json.dumps(catalog_golden, indent=2, ensure_ascii=False)),
    ("manifest_golden_json", manifest_golden),
]:
    delimiter = "NWTDATA"
    while f'){delimiter}"' in value:
        delimiter += "X"
    if len(delimiter) > 16:
        raise ValueError("Cannot find a short C++ raw-string delimiter")
    cpp += (
        f'inline constexpr const char* {name} = R"{delimiter}({value}){delimiter}";\n'
    )
(ROOT / "examples/cpp/example_data.hpp").write_text(cpp)
print("Updated Python and C++ embedded data; rebuild Rust/C#/C++ next.")
