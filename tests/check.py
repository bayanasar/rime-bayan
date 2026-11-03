#!/usr/bin/env python3
"""Check bayan on a real librime: golden candidates, preedit, and the space key.

  check.py --drive D --shared DIR --user FRESH_DIR [--schema bayan]

Use a fresh user directory. The space checks commit text, which librime learns,
so this must not share a user dictionary with a measurement.
"""
import argparse
import itertools
import os
import string
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def drive(args, lines, deploy=False):
    command = [args.drive, args.shared, args.user, args.schema]
    if deploy:
        command.append("--deploy")
    result = subprocess.run(
        command,
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"drive failed: {result.stderr.strip()}")
    return [line.split("\t") for line in result.stdout.splitlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive", required=True)
    parser.add_argument("--shared", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--schema", default="bayan")
    args = parser.parse_args()

    golden = []
    with open(os.path.join(HERE, "golden.tsv"), encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line and not line.startswith("#"):
                golden.append(line.split("\t"))

    rows = drive(args, [f"q\t{keys}\t{top}" for keys, top, _ in golden], deploy=True)
    failures = 0
    for (keys, top, preedit), row in zip(golden, rows):
        got_top, got_preedit = row[4], row[3]
        if got_top != top or got_preedit != preedit:
            failures += 1
            print(f"FAIL {keys}: want {top} {preedit}, got {got_top} {got_preedit}")

    # The preedit is zhuyin and nothing else, for every string of up to 3 keys.
    letters = string.ascii_lowercase
    typed = [
        "".join(keys)
        for size in (1, 2, 3)
        for keys in itertools.product(letters, repeat=size)
    ]
    latin = [
        row
        for row in drive(args, [f"p\t{keys}" for keys in typed])
        if len(row) < 2 or not row[1] or any(c in string.ascii_letters for c in row[1])
    ]
    if latin:
        failures += 1
        print(f"FAIL {len(latin)} of {len(typed)} key strings leave Latin or nothing in the preedit, such as", latin[:12])

    space = drive(args, ["c\t\t", "c\tdak\t", "c\tdakjia\t"])
    want = [("accepted=0", ""), ("accepted=1", "大"), ("accepted=1", "大家")]
    for (keys, accepted, text), (want_accepted, want_text) in zip(space, want):
        if accepted != want_accepted or text != want_text:
            failures += 1
            print(f"FAIL space after {keys!r}: want {want_accepted} {want_text!r}, got {accepted} {text!r}")

    print(f"{len(golden)} golden, {len(typed)} preedits, {len(want)} space, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
