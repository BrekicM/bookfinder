_SINGLE_LETTERS = {
    "a": "а",
    "b": "б",
    "v": "в",
    "g": "г",
    "d": "д",
    "đ": "ђ",
    "e": "е",
    "ž": "ж",
    "z": "з",
    "i": "и",
    "j": "ј",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "r": "р",
    "s": "с",
    "t": "т",
    "ć": "ћ",
    "u": "у",
    "f": "ф",
    "h": "х",
    "c": "ц",
    "č": "ч",
    "š": "ш",
}

_DIGRAPHS = {
    "lj": "љ",
    "nj": "њ",
    "dž": "џ",
}


def _map_char(char: str) -> str:
    mapped = _SINGLE_LETTERS.get(char.lower())
    if mapped is None:
        return char
    return mapped.upper() if char.isupper() else mapped


def _match_digraph(text: str, index: int) -> tuple[str, str] | None:
    pair = text[index : index + 2].lower()
    mapped = _DIGRAPHS.get(pair)
    if mapped is None:
        return None
    return pair, mapped


def to_cyrillic(text: str) -> str:
    result = []
    index = 0
    while index < len(text):
        digraph = _match_digraph(text, index)
        if digraph is not None:
            original, mapped = digraph
            if text[index : index + 2] == original.upper():
                mapped = mapped.upper()
            elif text[index].isupper():
                mapped = mapped[0].upper() + mapped[1:]
            result.append(mapped)
            index += 2
        else:
            result.append(_map_char(text[index]))
            index += 1
    return "".join(result)
