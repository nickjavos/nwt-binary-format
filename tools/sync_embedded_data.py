#!/usr/bin/env python3
"""Refresh Python/C++ copies of the editable schema and scenario catalog.

Rust and C# embed the JSON files at build time. Rebuild after running this tool.
This does not regenerate golden binaries or assign a new production stream ID.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
schema = json.loads((ROOT / "schemas/records.json").read_text())
catalog = json.loads((ROOT / "fixtures/catalog.json").read_text())
manifest = (ROOT / "fixtures/manifest.json").read_text().strip()
catalog_v11 = json.loads((ROOT / "fixtures/catalog-v1.1.json").read_text())
manifest_v11 = (ROOT / "fixtures/manifest-v1.1.json").read_text().strip()

python = '"""Generated example inputs. Edit the JSON files, then run tools/sync_embedded_data.py."""\nimport json\n\n'
for name, value in [("SCHEMA", schema), ("CATALOG", catalog), ("CATALOG_V11", catalog_v11)]:
    # repr safely handles quotes, escapes, Unicode and arbitrary input strings.
    text = json.dumps(value, indent=2, ensure_ascii=False)
    python += f"{name} = json.loads({text!r})\n\n"
python += f"MANIFEST = {manifest!r}\n\nMANIFEST_V11 = {manifest_v11!r}\n"
(ROOT / "examples/python/example_data.py").write_text(python)

cpp = "#pragma once\n// Generated example inputs. Numeric field values are decimal strings.\n"
for name, value in [
    ("schema_json", json.dumps(schema, indent=2)),
    ("catalog_json", json.dumps(catalog, indent=2, ensure_ascii=False)),
    ("manifest_json", manifest),
    ("catalog_v11_json", json.dumps(catalog_v11, indent=2, ensure_ascii=False)),
    ("manifest_v11_json", manifest_v11),
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
