"""Zhuyin-to-key tables for the layouts under test, and the key string for a reading."""

INITIALS = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ"
MEDIALS = "ㄧㄨㄩ"
FINALS = "ㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ"
TONE_MARKS = {"ˊ": "f", "ˇ": "j", "ˋ": "k", "˙": "d"}


def _table(initials, medials, finals):
    assert len(initials) == len(INITIALS)
    assert len(medials) == len(MEDIALS)
    assert len(finals) == len(FINALS)
    table = {}
    table.update(zip(INITIALS, initials))
    table.update(zip(MEDIALS, medials))
    table.update(zip(FINALS, finals))
    return table


LAYOUTS = {
    "eten26": _table("bpmfdtnlvkhgvcgycjqws", "exu", "aorwiqzpmntlh"),
    "bayan": _table("bpmfdtnlgkhjqxzcsrzcs", "iwu", "aoeeiyvpmntlr"),
}


def keys_for(table, reading):
    """Key string for a reading such as 'ㄉㄚˋ ㄐㄧㄚ'. Tone 1 has no key."""
    out = []
    for syllable in reading.split():
        tone = ""
        for symbol in syllable:
            if symbol in TONE_MARKS:
                tone = TONE_MARKS[symbol]
            else:
                out.append(table[symbol])
        out.append(tone)
    return "".join(out)
