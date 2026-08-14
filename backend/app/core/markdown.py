"""Shared markdown normalization helpers."""

import re

# Heading markers and code fences that must start on their own line.
_MARKDOWN_BLOCK_START_RE = re.compile(r"(?<!^)(?<![\n`#])(#{1,6}\s|```)")
# Numbered bold section markers, e.g. "1. **Plan** - ...".
_NUMBERED_SECTION_RE = re.compile(r"(?<!^)(?<![\n`])(\d{1,2}\. \*\*)")


def normalize_markdown(text: str) -> str:
    """Ensure markdown block markers start on a new line.

    Models occasionally glue a heading or section marker to the previous
    sentence (e.g. ``"...execute it.## 1. Plan"`` or ``"LIMIT 3;1. **Plan**"``),
    which CommonMark renders as plain text. This inserts the missing newline
    while leaving valid markdown untouched.
    """
    text = _MARKDOWN_BLOCK_START_RE.sub(r"\n\1", text)
    return _NUMBERED_SECTION_RE.sub(r"\n\1", text)
