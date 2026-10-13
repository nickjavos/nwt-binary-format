# Reference data samples

The reference data samples are eight NWT files built from public exchange and registry files and from security-master and corporate-actions exports in CSV. They hold six record types: `VENUE_DEF`, `OPTION_DEF`, `LISTING`, `SYMBOL_MAP`, `SECURITY_DEF` and `CORPORATE_ACTION`. Use them to test a reader against real values, to see how each source column becomes an NWT field, and as a model for converting your own reference data with `tools/nwt_convert_reference.py`. Trades, quotes, books and bars are covered in [Market data samples](REAL-DATA-MARKET.md).

## Sections

- [Samples](real-data/samples.md): The sample files made from real public data, with the record types and contents of each.
- [Convert a file](real-data/convert-a-file.md): The converter, `tools/nwt_convert_reference.py`, is a Python script that uses only the standard library.
- [Converter kinds](real-data/converter-kinds.md): The first argument selects the source format.
- [Rules for every conversion](real-data/rules-for-every-conversion.md): The rules that hold for every kind: exact values, identifiers, timestamps, nulls, order and output.
- [Instrument identifiers](real-data/instrument-identifiers.md): The symbol directories and the option series directory identify an instrument by symbol only.
- [Symbol directories: LISTING and SYMBOL_MAP](real-data/symbol-directories-listing-and-symbol_map.md): The kinds `nasdaqlisted` and `otherlisted` read the two listed-securities files.
- [Option series: OPTION_DEF](real-data/option-series-option_def.md): The kind `options` reads the option series directory.
- [Market identifier codes: VENUE_DEF](real-data/market-identifier-codes-venue_def.md): The kind `mic` reads the ISO 10383 list.
- [Security master: SECURITY_DEF](real-data/security-master-security_def.md): The kind `csv-secmaster` reads a security-master export.
- [Corporate actions: SECURITY_DEF and CORPORATE_ACTION](real-data/corporate-actions-security_def-and-corporate_action.md): The kind `csv-corporate-actions` reads a corporate-actions export.
- [Rounding and dates before 1970](real-data/rounding-and-dates-before-1970.md): NWT prices and ratios hold nine decimal places, and an NWT timestamp cannot hold a date before 1970.
- [Rebuild the samples](real-data/rebuild-the-samples.md): The kit keeps the source rows of every sample, so a rebuild needs no network.
