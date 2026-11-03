#!/usr/bin/env python3
"""Print the erase rule for spellings that have no single-syllable entry.

  dead_spellings.py bayan.schema.yaml terra_pinyin.dict.yaml

terra_pinyin has syllables that occur only inside longer words, such as yi5 and
ban2. Typed alone, such a spelling counts as exact, so librime drops the path
that reads its tone key as the next initial, and then finds nothing to offer:
no candidates, and the raw keys in the preedit. check.py finds any that remain.
"""
import re
import sys

schema, dictionary = sys.argv[1:]

rules = []
in_algebra = False
for line in open(schema, encoding="utf-8"):
    line = line.strip()
    if line == "algebra:":
        in_algebra = True
    elif in_algebra and line.startswith("- xform/"):
        left, right = line[len("- xform/") : -1].split("/", 1)
        rules.append((re.compile(left), re.sub(r"\$(\d)", r"\\\1", right)))
    elif in_algebra and line.startswith("- fuzz/"):
        break


def internal(syllable):
    for pattern, replacement in rules:
        syllable = pattern.sub(replacement, syllable)
    return syllable


used = set()
alone = set()
in_body = False
for line in open(dictionary, encoding="utf-8"):
    if not in_body:
        in_body = line.startswith("...")
        continue
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 2 or line.startswith("#") or not parts[1]:
        continue
    syllables = [internal(s) for s in parts[1].split()]
    used.update(syllables)
    if len(syllables) == 1:
        alone.add(syllables[0])


def split(form):
    return (form[:-1], form[-1]) if form[-1].isdigit() else (form, "")


forms = set()
for form in used:
    base, tone = split(form)
    forms.add(form)
    forms.add(base)
    if tone == "5":
        forms.update(base + t for t in "234")

live = set()
for form in alone:
    base, tone = split(form)
    live.add(form)
    live.add(base)
    if tone == "5":
        live.update(base + t for t in "234")

dead = sorted(forms - live)
print(f"# {len(dead)} of {len(forms)} spellings", file=sys.stderr)
print("    - erase/^(" + "|".join(dead) + ")$/")
