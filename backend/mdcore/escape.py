import re


SPECIALS = r"([\\`*_{}\[\]()#+\-!.|~])"


def escape_text(s: str) -> str:
    if not s:
        return s
    s = re.sub(r"\s+", " ", s)
    s = re.sub(SPECIALS, r"\\\1", s)
    return s


def fence_block(s: str, fence: str) -> str:
    return f"{fence}\n{s}\n{fence}"
