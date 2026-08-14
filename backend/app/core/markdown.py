"""Shared markdown normalization helpers."""

import re

# Heading markers and code fences that must start on their own line.
_MARKDOWN_BLOCK_START_RE = re.compile(r"(?<!^)(?<![\n`#])(#{1,6}\s|```)")
# Numbered bold section markers, e.g. "1. **Plan** - ...".
_NUMBERED_SECTION_RE = re.compile(r"(?<!^)(?<![\n`])(\d{1,2}\. \*\*)")
_SQL_FENCE_RE = re.compile(r"(```sql\s*\n)(.*?)(\n```)", re.DOTALL)
_GENERIC_FENCE_RE = re.compile(r"(```[^\n]*\n)(.*?)(\n```)", re.DOTALL)
_SQL_KEYWORD_RE = re.compile(r"\b(SELECT|WITH|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
# Closing code fence glued to a section marker, e.g. "```1. **Plan**".
_CLOSING_FENCE_GLUE_RE = re.compile(r"(```)(?=\d{1,2}\. \*\*)")


def normalize_markdown(text: str) -> str:
    """Ensure markdown block markers start on a new line.

    Models occasionally glue a heading or section marker to the previous
    sentence (e.g. ``"...execute it.## 1. Plan"`` or ``"LIMIT 3;1. **Plan**"``),
    which CommonMark renders as plain text. This inserts the missing newline
    while leaving valid markdown untouched.
    """
    text = _MARKDOWN_BLOCK_START_RE.sub(r"\n\1", text)
    text = _CLOSING_FENCE_GLUE_RE.sub(r"\1\n", text)
    return _NUMBERED_SECTION_RE.sub(r"\n\1", text)


class MarkdownStreamNormalizer:
    """Accumulates raw streamed text and emits line-complete chunks of the
    markdown-normalized full text.

    The model streams text in multiple events, and a glued section marker
    (e.g. ``...DESC`` + ``1. **Plan``) can span an event boundary. Normalizing
    each event separately misses that. This re-normalizes the accumulated text
    on every push and only emits complete lines, so the emitted stream and the
    final ``finish()`` tail are always a clean, normalized document.
    """

    def __init__(self) -> None:
        self._raw_parts: list[str] = []
        self._emitted = 0

    def push(self, text: str) -> list[str]:
        """Append raw streamed text; return newly completed lines to emit."""
        self._raw_parts.append(text)
        normalized = normalize_markdown("".join(self._raw_parts))
        chunks: list[str] = []
        while True:
            index = normalized.find("\n", self._emitted)
            if index == -1:
                break
            chunk = normalized[self._emitted : index + 1]
            chunks.append(chunk)
            self._emitted += len(chunk)
        return chunks

    def finish(self) -> str:
        """Return the remaining (possibly partial) normalized tail."""
        normalized = normalize_markdown("".join(self._raw_parts))
        tail = normalized[self._emitted :]
        self._emitted = len(normalized)
        return tail


def replace_sql_block(text: str, sql: str | None) -> str:
    """Replace the SQL code block in an answer with the actually-executed query.

    The model sometimes paraphrases the query in its narration. This swaps the
    content of the first `````sql`` fence (or the first fence whose content
    looks like SQL) with the real executed ``sql``, keeping the answer honest.
    Returns the text unchanged when there is no SQL or no matching block.
    """
    if not sql:
        return text
    sql = sql.strip()
    match = _SQL_FENCE_RE.search(text)
    if match:
        return _SQL_FENCE_RE.sub(
            lambda m: m.group(1) + sql + m.group(3), text, count=1
        )

    def _replace_if_sql(match: re.Match) -> str:
        if _SQL_KEYWORD_RE.search(match.group(2)):
            return match.group(1) + sql + match.group(3)
        return match.group(0)

    return _GENERIC_FENCE_RE.sub(_replace_if_sql, text, count=1)
