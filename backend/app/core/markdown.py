"""Shared markdown normalization helpers."""

import re

# Heading markers and code fences that must start on their own line.
_MARKDOWN_BLOCK_START_RE = re.compile(r"(?<!^)(?<![\n`#])(#{1,6}\s|```)")
# Numbered bold section markers, e.g. "1. **Plan** - ...".
_NUMBERED_SECTION_RE = re.compile(r"(?<!^)(?<![\n`])(\d{1,2}\. \*\*)")
_SQL_FENCE_RE = re.compile(r"(```sql\s*\n)(.*?)(\n```)", re.DOTALL)
_GENERIC_FENCE_RE = re.compile(r"(```[^\n]*\n)(.*?)(\n```)", re.DOTALL)
_SQL_KEYWORD_RE = re.compile(r"\b(SELECT|WITH|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
_SQL_START_RE = re.compile(r"^\s*\b(SELECT|WITH)\b", re.IGNORECASE)
# Section markers in any format: "1. Plan", "1. **Plan**", "**1. Plan**", "## 1.".
_SECTION_MARKER_RE = re.compile(
    r"^\s*(?:\d{1,2}\.\s(?:\*\*)?[A-Z]|\*\*\d{1,2}\.\s[A-Z]|#+\s*\d{1,2}\.)"
)
_GLUED_BOLD_SECTION_RE = re.compile(r"(?<!^)(?<![\n])(\*\*\d{1,2}\. [A-Z])")
_SQL_CLAUSE_RE = re.compile(
    r"\b(FROM|WHERE|GROUP\s+BY|ORDER\s+BY|LIMIT|JOIN|SUM|COUNT|AVG)\b", re.IGNORECASE
)
_SQL_CLAUSE_WORDS = (
    r"SELECT|FROM|WHERE|GROUP|ORDER|LIMIT|HAVING|JOIN|UNION|WITH|AND|OR|AS|BY|ON|IN|NOT|NULL|DESC|ASC"
)
_PROSE_START = rf"[A-Z][a-z]{{2,}}\s+(?!{_SQL_CLAUSE_WORDS}\b)"
_TABLE_ROW_RE = re.compile(r"^\s*\|")
# A SELECT statement in prose, ending at a semicolon, a section marker, a table
# row, a normal prose sentence start, or the end of text. SQL clause keywords
# (FROM/GROUP/ORDER/...) are excluded from the prose-stop detection.
_SQL_STATEMENT_IN_PROSE_RE = re.compile(
    rf"[Ss][Ee][Ll][Ee][Cc][Tt][\s\S]{{0,2500}}?"
    rf"(?:;\s*|(?=(?:\n\s*)?(?:[A-Z][a-z]{{2,}}\s+(?!(?i:{_SQL_CLAUSE_WORDS})\b)"
    rf"|\d{{1,2}}\.\s\*\*|#+\s|\|))|$)"
)
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
    text = _NUMBERED_SECTION_RE.sub(r"\n\1", text)
    text = _ensure_section_breaks(text)
    return _ensure_table_blank_lines(text)


def _ensure_section_breaks(text: str) -> str:
    """Guarantee every numbered section starts on its own line, separated by a
    blank line (covering ``1. Plan``, ``1. **Plan**`` and ``**1. Plan**``)."""
    text = _GLUED_BOLD_SECTION_RE.sub(r"\n\1", text)
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        if _SECTION_MARKER_RE.match(line) and out and out[-1].strip():
            out.append("")
        out.append(line)
    return "\n".join(out)


def _ensure_table_blank_lines(text: str) -> str:
    """Insert a blank line before a pipe-table block.

    GFM only parses a table when it starts on a fresh line. The model sometimes
    writes the section heading and the table on consecutive lines, which makes
    remark-gfm render the rows as raw text. This inserts the missing blank line
    before the first row of a table that follows prose or a list item.
    """
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        if (
            out
            and _TABLE_ROW_RE.match(line)
            and out[-1].strip()
            and not _TABLE_ROW_RE.match(out[-1])
        ):
            out.append("")
        out.append(line)
    return "\n".join(out)


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


def strip_leading_sql(text: str) -> str:
    """Remove a SQL statement that precedes the section structure.

    The model occasionally starts the answer with the query itself instead of
    section 1. If the first non-empty line is SQL (or a code fence), cut
    everything up to the first section marker. Answers that do not start with
    SQL, or have no section structure, are returned unchanged.
    """
    lines = text.splitlines()
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first is None:
        return text
    first_line = lines[first].strip()
    starts_with_sql = bool(_SQL_START_RE.match(first_line) or first_line.startswith("```"))
    if not starts_with_sql:
        return text
    section_index = next(
        (i for i, line in enumerate(lines) if _SECTION_MARKER_RE.match(line)),
        None,
    )
    if section_index is None:
        return text
    return "\n".join(lines[section_index:])


def remove_sql_in_prose(text: str) -> str:
    """Remove SQL SELECT statements that appear outside code fences.

    The model sometimes repeats the query inside prose sections (e.g. section
    4). This drops such statements while keeping fenced SQL (section 3) intact.
    A statement is only removed when it actually looks like SQL (contains a SQL
    clause keyword), and the match is replaced with a newline so surrounding
    prose stays separated.
    """
    parts = text.split("```")
    cleaned: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 1:  # inside a code fence: keep as-is
            cleaned.append(part)
            continue

        def _replace(match: re.Match) -> str:
            if _SQL_CLAUSE_RE.search(match.group(0)):
                return "\n"
            return match.group(0)

        cleaned.append(_SQL_STATEMENT_IN_PROSE_RE.sub(_replace, part))
    return "```".join(cleaned)
