# bayan 伯顏

A 26-key zhuyin (bopomofo) layout for [Rime](https://rime.im), with the initials
on the letters they have in pinyin.

```
q ㄑ    w ㄨ    e ㄝㄜ  r ㄖㄦ  t ㄊㄤ  y ㄟ    u ㄩ    i ㄧㄞ  o ㄛ    p ㄆㄡ
a ㄚ    s ㄙㄕ  d ㄉ˙   f ㄈˊ   g ㄍ    h ㄏ    j ㄐˇ   k ㄎˋ   l ㄌㄥ
z ㄗㄓ  x ㄒ    c ㄘㄔ  v ㄠ    b ㄅ    n ㄋㄣ  m ㄇㄢ
```

- Space commits. Tone 1 has no key, and a bare syllable means tone 1.
- `z` `c` `s` stand for both members of a pair and the candidates tell them
  apart.
- `i` holds ㄧ and ㄞ, which also share readings: 代理 and 地理 are on one code.
- The preedit is always zhuyin. Where the keys cannot settle a symbol it shows
  the commoner of the two, whichever candidate is highlighted: `zmk` shows ㄓㄢˋ.
- Tones can be left out. A bare syllable counts tone 1 at full weight and other
  tones at half, so `gwojia` offers 國家, and `dm` offers 但 before 單 because 但 is
  far more common.
- A neutral tone also answers to tones 2-4, because the dictionary writes 早上 as
  `zao3 shang5` and a typist gives ㄕㄤˋ. The cost is that particles lead on those
  codes: `mak` offers 嗎 before 罵.

## Install

Needs `terra_pinyin`, which Rime's default install includes.

```sh
bash rime-install bayanasar/rime-bayan
```

Or copy `bayan.schema.yaml` into your Rime user directory. Then add it to
`default.custom.yaml` and deploy:

```yaml
patch:
  schema_list:
    - {schema: bayan}
```

It shares the `terra_pinyin` user dictionary, so words learned under another
schema on that dictionary carry over.

## Tests

The tests drive a real librime. `tests/drive.c` needs its development headers;
`tests/compare.py` also needs `dict/chewing/tsi.csv` from
[libchewing-data](https://github.com/chewing/libchewing-data), which is LGPL and
so not kept here.

```sh
gcc tests/drive.c -lrime -o drive

# Golden candidates and preedit, and the space key. Use a fresh user directory:
# the space checks commit text, and librime learns what is committed.
mkdir fresh && cp bayan.schema.yaml fresh/
printf 'patch:\n  schema_list:\n    - {schema: bayan}\n' > fresh/default.custom.yaml
python3 tests/check.py --drive ./drive --shared /usr/share/rime-data --user fresh

# Frequent words and whole sentences, against any schema deployed in USERDIR.
python3 tests/compare.py --drive ./drive --shared /usr/share/rime-data \
  --tsi tsi.csv --sentences tests/sentences.txt bayan=bayan@USERDIR
```

## Credits

Derived from [Bopomofo_Eten26_Rime](https://github.com/loustack17/Bopomofo_Eten26_Rime)
by Lou Chang (MIT). Readings and word list come from Rime's `terra_pinyin`.
