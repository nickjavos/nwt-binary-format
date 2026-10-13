# Rebuild the samples

The kit keeps the source rows of the samples in `fixtures/real-market/source/`, cut from the start of each export without changing a byte. A sample that needs definitions has a second file with the definition rows of its instruments.

1. Run the rebuild script. It runs from any directory.

   ```bash
   sh fixtures/real-market/rebuild.sh
   ```

   For every sample the script writes `NAME.nwt`, the provenance printed by the converter as `NAME.provenance.json`, the JSON Lines view `NAME.jsonl` and the field-by-field view `NAME.fields.txt`. It ends by writing `SHA256SUMS` for the folder. The rebuilt `.nwt` files are byte-identical to the samples.
2. To rebuild `equity-bars.nwt` as well, set `NWT_SAMPLES_DIR` to the folder that holds the full exports and run the script again. The trade counts of the bars come from the full top-of-book export of the same venue and day, which is not part of the kit. Without the variable, the script prints a notice and leaves `equity-bars.nwt` as it is.

The script runs these conversions from the kit root:

<!-- nwt-title: Equities -->
```bash
S=fixtures/real-market/source
F=fixtures/real-market
python3 tools/nwt_convert_market.py csv-definition $S/xnas-itch_definition_all.csv $F/equity-definitions.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share
python3 tools/nwt_convert_market.py csv-mbo $S/xnas-itch_mbo_equities.csv $F/equity-orders.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share \
    --definitions $S/xnas-itch_definition_equities.csv --emit-deltas $F/equity-deltas.nwt
python3 tools/nwt_convert_market.py csv-mbp1 $S/xnas-itch_mbp-1_equities.csv $F/equity-quotes.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share \
    --definitions $S/xnas-itch_definition_equities.csv
python3 tools/nwt_convert_market.py csv-ohlcv $S/xnas-itch_ohlcv-1m_equities.csv $F/equity-bars.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share \
    --definitions $S/xnas-itch_definition_equities.csv \
    --trades $NWT_SAMPLES_DIR/xnas.itch/xnas.itch_mbp-1_equities.csv
```

<!-- nwt-title: Futures and options -->
```bash
S=fixtures/real-market/source
F=fixtures/real-market
python3 tools/nwt_convert_market.py csv-mbo $S/glbx-mdp3_mbo_futures.csv $F/futures-orders.nwt \
    --dataset REAL.GLBX.MDP3 --definitions $S/glbx-mdp3_definition_futures.csv --quantity-unit contract
python3 tools/nwt_convert_market.py csv-definition $S/opra-pillar_definition_all.csv $F/option-definitions.nwt \
    --dataset REAL.OPRA.PILLAR --quantity-unit contract
python3 tools/nwt_convert_market.py csv-cmbp1 $S/opra-pillar_cmbp-1_options.csv $F/option-best-quotes.nwt \
    --dataset REAL.OPRA.PILLAR --definitions $S/opra-pillar_definition_options.csv --quantity-unit contract
python3 tools/nwt_convert_market.py csv-mbp10 $S/ifus-impact_mbp-10_options.csv $F/depth-10.nwt \
    --dataset REAL.IFUS.IMPACT --definitions $S/ifus-impact_definition_options.csv --currency USX --quantity-unit contract
python3 tools/nwt_convert_market.py csv-statistics $S/xeur-eobi_statistics_all.csv $F/statistics.nwt \
    --dataset REAL.XEUR.EOBI --definitions $S/xeur-eobi_definition_statistics.csv --quantity-unit contract --skip-undefined
```

The options follow from the content of each export:

- The equities definitions have no currency, so the commands pass `--currency USD`.
- In the depth export, 12 instruments are not outright options and have no currency in their definition rows. Every outright option in the sample is priced in `USX`, so the command passes `--currency USX`. These 12 instruments get an `INSTRUMENT_DEF` with `asset_class` 0 and no `OPTION_DEF`.
- In the statistics export, 169 instruments have no currency in their definition rows. The venue trades in several currencies, so the command gives no fallback: `--skip-undefined` leaves these instruments out, and the provenance counts them.
- In the same export, 1,689 options have neither an underlying ID nor an underlying symbol in their definition rows, so they have an `INSTRUMENT_DEF` and no `OPTION_DEF`.
