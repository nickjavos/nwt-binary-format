#!/usr/bin/env python3

import argparse
import importlib
import json
import sys
from pathlib import Path

MODULES = ("nwt_convert_market", "nwt_convert_reference")
ERRORS = (ValueError, KeyError, OverflowError, UnicodeError, OSError)


def kinds():
    folder = str(Path(__file__).resolve().parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    registry = {}
    for name in MODULES:
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError as error:
            if error.name != name:
                raise
            continue
        module.add_kinds(registry)
    return registry


def set_options(args, tokens):
    seen = set()
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token.startswith("--") or len(token) == 2:
            raise ValueError(f"expected an --option after OUT, found {token!r}")
        name, equals, value = token[2:].partition("=")
        if not equals:
            flag = i + 1 == len(tokens) or tokens[i + 1].startswith("--")
            value = True if flag else tokens[i + 1]
            i += 0 if flag else 1
        name = name.replace("-", "_")
        if not name.isidentifier() or name in seen or name in ("kind", "src", "out", "options", "func"):
            raise ValueError(f"bad or repeated option {token!r}")
        seen.add(name)
        setattr(args, name, value)
        i += 1


def run(args):
    try:
        registry = kinds()
        if args.kind not in registry:
            known = ", ".join(sorted(registry)) or "none (no converter module is installed)"
            raise ValueError(f"unknown kind {args.kind!r}; known kinds: {known}")
        set_options(args, args.options)
        summary = registry[args.kind](args.src, args.out, args)
    except ERRORS as error:
        print(f"NWT error: {error}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def add_arguments(parser):
    parser.add_argument("kind", help="source format, for example csv-mbo; an unknown kind lists the known ones")
    parser.add_argument("src", help="source file")
    parser.add_argument("out", help="NWT container to write")
    parser.add_argument("options", nargs=argparse.REMAINDER, help="converter options: --name value or --flag")
    parser.set_defaults(func=run)


def register(subparsers):
    add_arguments(subparsers.add_parser("convert", help="convert a source file to an NWT container"))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nwt_convert.py", description="Convert a source file to an NWT container.")
    add_arguments(parser)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
