#!/usr/bin/env python3
"""Build the hosted files and the kit archive in dist/files/, after scanning the kit for words it must not carry.

Usage: python3 tools/package.py

The scan covers every file of the repository that .gitignore does not exclude, and every file name. When it
finds anything, the script prints every finding and exits with status 1 before it writes a file.
Otherwise it writes SHA256SUMS.txt for the kit, then dist/files/: the schema, the conformance files, the
samples with their JSON Lines views, nwt-binary-format-kit.zip, SHA256SUMS.txt and index.json.
"""

import fnmatch
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "examples/python"))
import nwt_example as nwt

OUT = KIT / "dist/files"
ARCHIVE = "nwt-binary-format-kit.zip"
ARCHIVE_ROOTS = ("README.md", "README.ru.md", "THIRD-PARTY-NOTICES.md", "SHA256SUMS.txt", "docs", "schemas", "examples", "tools", "tests", "fixtures")
ARCHIVE_LEFT_OUT = ("tools/build_site.py", "tools/build_html.py", "tools/site-assets/", "tools/site-ui/")
SAMPLE_FOLDERS = {
    "fixtures/real": ("venues", "listings-nasdaq", "listings-other", "options"),
    "fixtures/real-reference": ("secmaster-us", "secmaster-global", "corporate-actions-us", "corporate-actions-global"),
    "fixtures/real-market": (
        "equity-definitions", "equity-orders", "equity-deltas", "equity-quotes", "equity-bars", "futures-orders",
        "option-definitions", "option-best-quotes", "depth-10", "statistics",
    ),
}
CONFORMANCE = ("all-records.nwt", "all-records.zst.nwt")

# Wire constants: the spec_uri values that a manifest declares for each record type.
WIRE_CONSTANTS = ("urn:nwt:spec:1.0", "urn:nwt:spec:1.1")
# Software of other authors and the lock files state the versions of that software.
OTHER_SOFTWARE = ("examples/cpp/vendor/", "examples/rust/Cargo.lock", "tools/site-assets/", "tools/site-ui/package-lock.json")
# Names and license versions of other software that the documents state.
OTHER_SOFTWARE_NAMES = ("SIL Open Font License 1.1", "OFL-1.1", "OFL 1.1")
# Sample data: prices, rates and versions of source files are data, not labels of the format.
DATA = re.compile(r"fixtures/real[^/]*/.*\.(csv|txt|jsonl|nwt)$")

WORDS = [re.compile(word, re.I) for word in ("data" + "bento", r"(?<![a-z0-9])" + "d" + r"bn(?![a-z0-9])")]
LABELS = [re.compile(p, re.I) for p in (r"(?<![\d.])1\.1(?!\.?\d)", r"1\.0-draft", r"draft\.", r"v1\.?1(?!\d)")]
PRINTABLE = re.compile(rb"[\x20-\x7e]{6,}")


def ignore_rules():
    rules = [line.strip() for line in (KIT / ".gitignore").read_text().splitlines()]
    return [rule.rstrip("/") for rule in rules if rule and not rule.startswith("#")]


def ignored(rel, rules):
    # shortcut: handles plain names, globs and paths from the root, which is all this .gitignore uses;
    # use a full gitignore matcher if it ever gains negations or "**".
    parts = rel.split("/")
    for rule in rules:
        if "/" in rule:
            if rel == rule or rel.startswith(rule + "/"):
                return True
        elif any(fnmatch.fnmatch(part, rule) for part in parts):
            return True
    return False


def kit_files():
    rules = ignore_rules()
    found = []
    for path in sorted(KIT.rglob("*")):
        rel = path.relative_to(KIT).as_posix()
        if path.is_file() and not rel.startswith(".git/") and not ignored(rel, rules):
            found.append(rel)
    return found


def archived(rel):
    hidden = any(part.startswith(".") for part in rel.split("/"))
    inside = rel in ARCHIVE_ROOTS or rel.split("/")[0] in ARCHIVE_ROOTS
    return inside and not hidden and not any(rel == left or rel.startswith(left) for left in ARCHIVE_LEFT_OUT)


def scan_text(text, labels=True):
    """Findings in one text: (line number, matched text, line excerpt)."""
    for constant in WIRE_CONSTANTS + OTHER_SOFTWARE_NAMES:
        text = text.replace(constant, "")
    found = []
    for number, line in enumerate(text.split("\n"), 1):
        for pattern in WORDS + (LABELS if labels else []):
            for match in pattern.finditer(line):
                at = max(match.start() - 30, 0)
                found.append((number, match.group(), line[at : match.end() + 30].strip()))
    return found


def scan(files):
    findings = []
    for rel in files:
        labels = not rel.startswith(OTHER_SOFTWARE) and not DATA.fullmatch(rel)
        for _, word, _ in scan_text(rel, labels):
            findings.append(f"{rel}: file name contains {word!r}")
        data = (KIT / rel).read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = "\n".join(run.decode("ascii") for run in PRINTABLE.findall(data))
            labels = labels and rel.endswith((".nwt", ".bin"))
        for number, word, excerpt in scan_text(text, labels):
            findings.append(f"{rel}:{number}: {word!r} in: {excerpt}")
    return findings


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def contents(path):
    """(record count, type names in type order) of a container, read with the Python reference codec."""
    counts = {}
    with open(path, "rb") as f:
        for _, raws, _ in nwt.open_reader(f).scan(decode=False):
            for raw in raws:
                typ = nwt.get(raw, 4, 2)
                counts[typ] = counts.get(typ, 0) + 1
    return sum(counts.values()), [nwt.S[typ]["name"] for typ in sorted(counts)]


def write_archive(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in files:
            # A fixed time and mode: two runs over the same files give the same archive.
            info = zipfile.ZipInfo(ARCHIVE[:-4] + "/" + rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if rel.endswith(".sh") else 0o644) << 16
            archive.writestr(info, (KIT / rel).read_bytes(), compresslevel=9)


def build(files):
    shipped = [rel for rel in files if archived(rel) and rel != "SHA256SUMS.txt"]
    sums = "".join(f"{sha256(KIT / rel)}  {rel}\n" for rel in shipped)
    (KIT / "SHA256SUMS.txt").write_text(sums)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "samples").mkdir(parents=True)
    hosted = []  # (hosted path, kind, source path)
    write_archive(OUT / ARCHIVE, ["SHA256SUMS.txt"] + shipped)
    hosted.append((ARCHIVE, "kit", None))
    shutil.copyfile(KIT / "schemas/records.json", OUT / "records.json")
    hosted.append(("records.json", "schema", "schemas/records.json"))
    for name in CONFORMANCE:
        shutil.copyfile(KIT / "fixtures/golden" / name, OUT / "samples" / name)
        hosted.append(("samples/" + name, "conformance", "fixtures/golden/" + name))
    for folder, names in SAMPLE_FOLDERS.items():
        for name in names:
            for suffix, kind in ((".nwt", "sample"), (".jsonl", "view")):
                source = f"{folder}/{name}{suffix}"
                if not (KIT / source).is_file():
                    print(f"skipped: {source} is not in the kit")
                    continue
                shutil.copyfile(KIT / source, OUT / "samples" / (name + suffix))
                hosted.append((f"samples/{name}{suffix}", kind, source))

    entries = []
    for path, kind, source in hosted:
        entry = {"path": path, "bytes": (OUT / path).stat().st_size, "sha256": sha256(OUT / path), "kind": kind}
        if path.endswith(".nwt"):
            entry["records"], entry["types"] = contents(OUT / path)
        if source:
            entry["source"] = source
        entries.append(entry)
    (OUT / "SHA256SUMS.txt").write_text("".join(f"{e['sha256']}  {e['path']}\n" for e in entries))
    sums = OUT / "SHA256SUMS.txt"
    entries.append({"path": "SHA256SUMS.txt", "bytes": sums.stat().st_size, "sha256": sha256(sums), "kind": "checksums"})
    (OUT / "index.json").write_text(json.dumps({"files": entries}, indent=1) + "\n")
    return entries, len(shipped) + 1


def self_check():
    label = "1" + ".1"
    assert scan_text("spec_uri urn:nwt:spec:" + label) == [] and scan_text("price 1" + label + "00 or 0." + label) == []
    assert [word for _, word, _ in scan_text("NWT " + label + " and v" + label)] == [label, label, "v" + label]
    assert scan_text("a " + "DB" + "N file") and not scan_text("the hash 0a" + "db" + "n1")


def main():
    self_check()
    files = kit_files()
    findings = scan(files)
    if findings:
        print("\n".join(findings))
        print(f"package.py: {len(findings)} findings in {len(files)} files; nothing was written")
        return 1
    entries, archived_count = build(files)
    size = sum(e["bytes"] for e in entries)
    print(f"package.py: {len(files)} files scanned, {archived_count} files in {ARCHIVE}, "
          f"{len(entries)} hosted files, {size} bytes in dist/files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
