#!/bin/sh
# Rebuild every sample in this folder from source/. Runs from any directory.
# equity-bars takes its trade counts from the venue's full top-of-book file, which is not in the kit:
# it is rebuilt only when NWT_SAMPLES_DIR points at the folder that holds the full exports.
set -eu

F=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$F/../.." && pwd)
S="$F/source"
EQUITY="--dataset REAL.XNAS.ITCH --currency USD --quantity-unit share"

# convert NAME KIND SOURCE [OPTION...]: writes NAME.nwt and the converter's summary, NAME.provenance.json.
convert() {
    name=$1 kind=$2 src=$3
    shift 3
    python3 "$KIT/tools/nwt_convert_market.py" "$kind" "$S/$src" "$F/$name.nwt" "$@" > "$F/$name.provenance.json"
}

convert equity-definitions csv-definition xnas-itch_definition_all.csv $EQUITY
convert equity-orders csv-mbo xnas-itch_mbo_equities.csv $EQUITY \
    --definitions "$S/xnas-itch_definition_equities.csv" --emit-deltas "$F/equity-deltas.nwt"
convert equity-quotes csv-mbp1 xnas-itch_mbp-1_equities.csv $EQUITY \
    --definitions "$S/xnas-itch_definition_equities.csv"
if [ -n "${NWT_SAMPLES_DIR:-}" ]; then
    full=$NWT_SAMPLES_DIR
    if [ -d "$full/normalized" ]; then full=$full/normalized; fi
    convert equity-bars csv-ohlcv xnas-itch_ohlcv-1m_equities.csv $EQUITY \
        --definitions "$S/xnas-itch_definition_equities.csv" --trades "$full/xnas.itch/xnas.itch_mbp-1_equities.csv"
else
    echo "notice: NWT_SAMPLES_DIR is not set; equity-bars is left as it is" >&2
fi
convert futures-orders csv-mbo glbx-mdp3_mbo_futures.csv --dataset REAL.GLBX.MDP3 \
    --definitions "$S/glbx-mdp3_definition_futures.csv" --quantity-unit contract
convert option-definitions csv-definition opra-pillar_definition_all.csv --dataset REAL.OPRA.PILLAR \
    --quantity-unit contract
convert option-best-quotes csv-cmbp1 opra-pillar_cmbp-1_options.csv --dataset REAL.OPRA.PILLAR \
    --definitions "$S/opra-pillar_definition_options.csv" --quantity-unit contract
convert depth-10 csv-mbp10 ifus-impact_mbp-10_options.csv --dataset REAL.IFUS.IMPACT \
    --definitions "$S/ifus-impact_definition_options.csv" --currency USX --quantity-unit contract
convert statistics csv-statistics xeur-eobi_statistics_all.csv --dataset REAL.XEUR.EOBI \
    --definitions "$S/xeur-eobi_definition_statistics.csv" --quantity-unit contract --skip-undefined

for file in "$F"/*.nwt; do
    python3 "$KIT/examples/python/nwt_example.py" to-json "$file" > "${file%.nwt}.jsonl"
    python3 "$KIT/examples/python/nwt_example.py" read "$file" > "${file%.nwt}.fields.txt"
done

cd "$F"
shasum -a 256 source/*.csv *.nwt *.jsonl *.fields.txt *.provenance.json > SHA256SUMS
