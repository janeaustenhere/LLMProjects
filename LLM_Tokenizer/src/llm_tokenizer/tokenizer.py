import re

import tiktoken


try:
    ENCODING = tiktoken.get_encoding("o200k_base")
    USING_REAL_TOKENIZER = True
except Exception:
    ENCODING = None
    USING_REAL_TOKENIZER = False


def _fallback_pieces(text: str) -> list[str]:
    """Simple estimate used when the tokenizer vocabulary is unavailable."""
    pieces: list[str] = []
    for piece in re.findall(r"\s*\w+|\s[^\w\s]|\s+", text):
        while len(piece) > 4:
            pieces.append(piece[:4])
            piece = piece[4:]
        if piece:
            pieces.append(piece)
    return pieces


def tokenize(text: str) -> list[str]:
    if USING_REAL_TOKENIZER:
        return [ENCODING.decode_single_token_bytes(token).decode("utf-8", errors="replace") for token in ENCODING.encode(text)]
    return _fallback_pieces(text)


def count_tokens(text: str) -> int:
    if USING_REAL_TOKENIZER:
        return len(ENCODING.encode(text))
    return len(_fallback_pieces(text))
