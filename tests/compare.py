#!/usr/bin/env python3
"""Compare schemas on a real librime: frequent words and whole sentences.

  compare.py --drive D --shared DIR --tsi tsi.csv --sentences FILE \
             SCHEMA=LAYOUT[@USERDIR] [...]

tsi.csv is libchewing-data's dict/chewing/tsi.csv. It supplies readings and
frequencies, and is LGPL, so it is fetched rather than kept in this repository.
Every schema must already be deployed in its user directory.
"""
import argparse
import collections
import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layouts import LAYOUTS, keys_for  # noqa: E402


def load_lexicon(path):
    """word -> (frequency, most frequent reading)."""
    lexicon = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 3 or row[0].startswith("#"):
                continue
            try:
                freq = int(row[1])
            except ValueError:
                continue
            word, reading = row[0], row[2]
            current = lexicon.get(word)
            # On a frequency tie prefer the neutral-tone reading: 們 is listed
            # as both ㄇㄣˊ and ㄇㄣ˙, and terra_pinyin only has the latter.
            if (
                current is None
                or freq > current[0]
                or (freq == current[0] and "˙" in reading and "˙" not in current[1])
            ):
                lexicon[word] = (freq, reading)
    return lexicon


def reading_of_sentence(sentence, lexicon, longest=6):
    """Longest-match reading. Both layouts get the same reading, so an odd
    polyphone choice costs them equally."""
    out = []
    at = 0
    while at < len(sentence):
        for size in range(min(longest, len(sentence) - at), 0, -1):
            entry = lexicon.get(sentence[at : at + size])
            if entry:
                out.append(entry[1])
                at += size
                break
        else:
            return None
    return " ".join(out)


def run(drive, shared, user, schema, lines):
    result = subprocess.run(
        [drive, shared, user, schema],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.split("\t") for line in result.stdout.splitlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive", required=True)
    parser.add_argument("--shared", required=True)
    parser.add_argument("--tsi", required=True)
    parser.add_argument("--sentences", required=True)
    parser.add_argument("--words", type=int, default=3000)
    parser.add_argument("--chars", type=int, default=1000)
    parser.add_argument("--misses", type=int, default=0)
    parser.add_argument("schemas", nargs="+", metavar="SCHEMA=LAYOUT@USERDIR")
    args = parser.parse_args()

    lexicon = load_lexicon(args.tsi)
    ranked = sorted(lexicon.items(), key=lambda item: -item[1][0])
    chars = [(w, e) for w, e in ranked if len(w) == 1][: args.chars]
    words = [(w, e) for w, e in ranked if len(w) >= 2][: args.words]
    with open(args.sentences, encoding="utf-8") as handle:
        sentences = [
            s
            for s in (line.strip() for line in handle)
            if s and not s.startswith("#")
        ]
    readable = [(s, reading_of_sentence(s, lexicon)) for s in sentences]
    unread = [s for s, r in readable if r is None]
    if unread:
        print("no reading for:", unread, file=sys.stderr)
    readable = [(s, r) for s, r in readable if r]
    print(
        f"{len(chars)} chars, {len(words)} words, {len(readable)} sentences "
        f"({sum(len(s) for s, _ in readable)} characters)"
    )
    print(f"{'schema':20s} {'char top1':>10s} {'char <=9':>9s} {'word top1':>10s} {'word <=9':>9s} {'sentence top1':>14s}")

    for spec in args.schemas:
        schema, rest = spec.split("=")
        layout, user = rest.split("@")
        table = LAYOUTS[layout]
        cells = []
        misses = []
        for group in (chars, words):
            rows = run(
                args.drive,
                args.shared,
                user,
                schema,
                [f"q\t{keys_for(table, e[1])}\t{w}" for w, e in group],
            )
            assert len(rows) == len(group), (schema, len(rows), len(group))
            total = sum(e[0] for _, e in group)
            top = page = 0
            for (word, entry), row in zip(group, rows):
                rank = int(row[2])
                if rank == 1:
                    top += entry[0]
                else:
                    misses.append((entry[0], word, row[4], rank))
                if 1 <= rank <= 9:
                    page += entry[0]
            cells += [100 * top / total, 100 * page / total]
        rows = run(
            args.drive,
            args.shared,
            user,
            schema,
            [f"q\t{keys_for(table, r)}\t{s}" for s, r in readable],
        )
        hits = sum(1 for row in rows if row[2] == "1")
        print(
            f"{schema:20s} {cells[0]:9.2f}% {cells[1]:8.2f}% {cells[2]:9.2f}% {cells[3]:8.2f}% "
            f"{hits:5d}/{len(readable)}"
        )
        if args.misses:
            misses.sort(reverse=True)
            print("  worst misses:", " ".join(f"{w}→{t}(#{r})" for _, w, t, r in misses[: args.misses]))
            print("  sentence misses:", " | ".join(f"{row[1]}→{row[4]}" for row in rows if row[2] != "1")[:1500])


if __name__ == "__main__":
    main()
