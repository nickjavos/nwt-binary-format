#!/bin/sh
# Rebuild every sample in this folder from source/. Runs from any directory.
set -eu

F=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$F/../.." && pwd)

# convert NAME KIND SOURCE: writes NAME.nwt; --retrieved is the day the source files were fetched.
convert() {
    python3 "$KIT/tools/nwt_convert_reference.py" "$2" "$F/source/$3" "$F/$1.nwt" --retrieved 2026-10-13 > /dev/null
}

(cd "$F/source" && shasum -a 256 -c SHA256SUMS)
convert venues mic ISO10383_MIC.csv
convert listings-nasdaq nasdaqlisted nasdaqlisted.txt
convert listings-other otherlisted otherlisted.txt
convert options options options.txt

for file in "$F"/*.nwt; do
    python3 "$KIT/examples/python/nwt_example.py" to-json "$file" > "${file%.nwt}.jsonl"
    python3 "$KIT/examples/python/nwt_example.py" read "$file" > "${file%.nwt}.fields.txt"
done
