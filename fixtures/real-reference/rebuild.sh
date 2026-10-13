#!/bin/sh
# Rebuild every sample in this folder from source/. Runs from any directory.
set -eu

F=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$F/../.." && pwd)

# convert NAME KIND DATASET: reads source/NAME.csv and writes NAME.nwt.
convert() {
    python3 "$KIT/tools/nwt_convert_reference.py" "$2" "$F/source/$1.csv" "$F/$1.nwt" --dataset "$3" > /dev/null
}

(cd "$F/source" && shasum -a 256 -c SHA256SUMS)
convert secmaster-us csv-secmaster REAL.SECMASTER.US
convert secmaster-global csv-secmaster REAL.SECMASTER.GLOBAL
convert corporate-actions-us csv-corporate-actions REAL.CORPACT.US
convert corporate-actions-global csv-corporate-actions REAL.CORPACT.GLOBAL

for file in "$F"/*.nwt; do
    python3 "$KIT/examples/python/nwt_example.py" to-json "$file" > "${file%.nwt}.jsonl"
    python3 "$KIT/examples/python/nwt_example.py" read "$file" > "${file%.nwt}.fields.txt"
done
