"""Layout-insensitive source text for policy tests that assert code fragments.

Several safety-policy tests assert that a specific code fragment exists in a
module (for example a fixed ``sysupgrade`` argv). Those checks must survive
automatic formatting, so containment ignores whitespace, statement separators
and trailing commas while still requiring the exact tokens in order.
"""
from __future__ import annotations

import re
from pathlib import Path

_TRAILING_COMMA = re.compile(r",(?=[)\]}])")


def compact(text: str) -> str:
    return _TRAILING_COMMA.sub("", re.sub(r"[\s;]+", "", text))


class SourceText(str):
    """``str`` whose ``in`` checks compare compacted code."""

    def __new__(cls, text: str):
        obj = super().__new__(cls, text)
        obj._compact = compact(text)
        return obj

    def __contains__(self, fragment: object) -> bool:
        if not isinstance(fragment, str):
            return False
        return compact(fragment) in self._compact

    # Positions (including start/end arguments) are offsets in the compacted text:
    # only compare them with each other, never slice the original string with them.
    def count(self, fragment, *args):  # type: ignore[override]
        return self._compact.count(compact(fragment), *args)

    def find(self, fragment, *args):  # type: ignore[override]
        return self._compact.find(compact(fragment), *args)

    def index(self, fragment, *args):  # type: ignore[override]
        return self._compact.index(compact(fragment), *args)


def read_source(path: str | Path) -> SourceText:
    return SourceText(Path(path).read_text(encoding="utf-8"))
