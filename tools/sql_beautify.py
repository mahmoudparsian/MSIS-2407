"""Lightweight, dependency-free SQL beautifier.

Not a full SQL parser -- a conservative tokenizer + clause-keyword splitter
tuned for the straightforward SELECT/FROM/WHERE/GROUP BY/ORDER BY/JOIN/
CREATE TABLE-style queries used in this course. It:

  * puts each top-level clause keyword (SELECT, FROM, WHERE, GROUP BY,
    ORDER BY, HAVING, JOIN variants, ON, LIMIT, CREATE TABLE, INSERT INTO,
    ...) on its own line
  * breaks SELECT / GROUP BY / ORDER BY / VALUES / SET column-lists onto
    one item per line, and WHERE / HAVING / ON onto one AND/OR condition
    per line -- but only when there's more than one item/condition
  * never reformats *inside* parentheses (subqueries, function args, CASE
    expressions, window OVER(...) clauses) -- those are rendered flat, to
    keep risk of corrupting a query low

It intentionally does not re-case keywords or identifiers.
"""
import re

_STRING_TOK = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_BRACE_TOK = re.compile(r"\{[^{}]*\}")

CLAUSE_PHRASES = sorted(
    [
        ("CREATE", "OR", "REPLACE", "TEMP", "TABLE"),
        ("CREATE", "OR", "REPLACE", "TEMPORARY", "TABLE"),
        ("CREATE", "OR", "REPLACE", "TABLE", "IF", "NOT", "EXISTS"),
        ("CREATE", "OR", "REPLACE", "TABLE"),
        ("CREATE", "TEMP", "TABLE"),
        ("CREATE", "TEMPORARY", "TABLE"),
        ("CREATE", "TABLE", "IF", "NOT", "EXISTS"),
        ("CREATE", "TABLE"),
        ("CREATE", "OR", "REPLACE", "VIEW"),
        ("CREATE", "VIEW"),
        ("CREATE", "OR", "REPLACE", "MACRO"),
        ("CREATE", "MACRO"),
        ("DROP", "TABLE", "IF", "EXISTS"),
        ("DROP", "TABLE"),
        ("DROP", "MACRO", "TABLE", "IF", "EXISTS"),
        ("DROP", "MACRO", "IF", "EXISTS"),
        ("DROP", "MACRO"),
        ("DROP", "VIEW"),
        ("INSERT", "INTO"),
        ("DELETE", "FROM"),
        ("UPDATE",),
        ("SET",),
        ("VALUES",),
        ("SELECT", "DISTINCT"),
        ("SELECT",),
        ("FROM",),
        ("WHERE",),
        ("GROUP", "BY"),
        ("ORDER", "BY"),
        ("HAVING",),
        ("LIMIT",),
        ("OFFSET",),
        ("WITH",),
        ("QUALIFY",),
        ("FULL", "OUTER", "JOIN"),
        ("LEFT", "OUTER", "JOIN"),
        ("RIGHT", "OUTER", "JOIN"),
        ("FULL", "JOIN"),
        ("LEFT", "JOIN"),
        ("RIGHT", "JOIN"),
        ("INNER", "JOIN"),
        ("CROSS", "JOIN"),
        ("JOIN",),
        ("ON",),
        ("UNION", "ALL"),
        ("UNION",),
        ("INTERSECT",),
        ("EXCEPT",),
        ("BEGIN", "TRANSACTION"),
        ("BEGIN",),
        ("COMMIT",),
        ("ROLLBACK",),
        ("RETURNING",),
    ],
    key=lambda p: -len(p),
)

MULTILINE_CLAUSES = {
    "SELECT", "SELECT DISTINCT", "GROUP BY", "ORDER BY",
    "WHERE", "HAVING", "ON", "VALUES", "SET",
}

PAREN_NEEDS_SPACE_AFTER = {
    "IN", "VALUES", "EXISTS", "NOT", "AND", "OR", "WHERE", "ON",
    "WHEN", "THEN", "ELSE", "AS", "BY", "SELECT", "FROM", "ONLY",
    "ALL", "ANY", "SOME", "QUALIFY", "HAVING",
}


def tokenize_sql(text):
    tokens = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if text[i:i + 2] == "--":
            j = text.find("\n", i)
            if j == -1:
                j = n
            tokens.append(("comment", text[i:j].rstrip()))
            i = j
            continue
        if c in "'\"":
            m = _STRING_TOK.match(text, i)
            if m:
                tokens.append(("string", m.group(0)))
                i = m.end()
                continue
        if c == "{":
            m = _BRACE_TOK.match(text, i)
            if m:
                tokens.append(("word", m.group(0)))
                i = m.end()
                continue
        if c == "(":
            tokens.append(("lparen", "("))
            i += 1
            continue
        if c == ")":
            tokens.append(("rparen", ")"))
            i += 1
            continue
        if c == ",":
            tokens.append(("comma", ","))
            i += 1
            continue
        if c == ";":
            tokens.append(("semi", ";"))
            i += 1
            continue
        j = i
        while j < n and text[j] not in " \t\r\n(),;'\"{":
            j += 1
        if j == i:
            j += 1
        tokens.append(("word", text[i:j]))
        i = j
    return tokens


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.$]*$")


def _is_function_name(word_text):
    """True if this looks like an identifier/function name (so a following
    '(' should attach directly, e.g. COUNT(...)) rather than an operator or
    symbol (e.g. '=', '+') where '(' needs a leading space."""
    return bool(_IDENTIFIER_RE.match(word_text)) and word_text.upper() not in PAREN_NEEDS_SPACE_AFTER


def render_tokens(tokens):
    NO_SPACE_BEFORE = {",", ")", ";"}
    out = []
    prev = None
    for kind, text in tokens:
        if kind == "comment":
            sep = " " if out else ""
            piece = text
        elif text in NO_SPACE_BEFORE:
            sep = ""
            piece = text
        elif kind == "lparen":
            piece = "("
            if prev is None:
                sep = ""
            elif prev[0] == "word" and _is_function_name(prev[1]):
                sep = ""
            elif prev[0] == "lparen":
                sep = ""
            else:
                sep = " "
        elif prev is not None and prev[0] == "lparen":
            piece = text
            sep = ""
        else:
            piece = text
            sep = " " if out else ""
        out.append(sep + piece)
        prev = (kind, text)
    return "".join(out)


def split_top_level(tokens, seps):
    groups = []
    current = []
    depth = 0
    prefix = None
    pending_between = 0  # BETWEEN x AND y -- that AND isn't a connective
    for kind, text in tokens:
        if kind == "lparen":
            depth += 1
            current.append((kind, text))
            continue
        if kind == "rparen":
            depth -= 1
            current.append((kind, text))
            continue
        if depth == 0 and kind == "word" and text.upper() == "BETWEEN":
            pending_between += 1
            current.append((kind, text))
            continue
        if depth == 0 and kind == "comma" and "," in seps:
            groups.append((prefix, current))
            current = []
            prefix = None
            continue
        if depth == 0 and kind == "word" and text.upper() in ("AND", "OR") and text.upper() in seps:
            if text.upper() == "AND" and pending_between > 0:
                pending_between -= 1
                current.append((kind, text))
                continue
            groups.append((prefix, current))
            current = []
            prefix = text.upper()
            continue
        current.append((kind, text))
    groups.append((prefix, current))
    return [g for g in groups if g[1]]


def _match_clause(tokens, i):
    for phrase in CLAUSE_PHRASES:
        ok = True
        for k, word in enumerate(phrase):
            if i + k >= len(tokens):
                ok = False
                break
            kind, text = tokens[i + k]
            if kind != "word" or text.upper() != word:
                ok = False
                break
        if ok:
            return tokens[i:i + len(phrase)], len(phrase)
    return None


def beautify_sql(text):
    text = text.strip()
    if not text:
        return text
    trailing_semi = text.rstrip().endswith(";")
    if trailing_semi:
        text = text.rstrip()[:-1]
    tokens = tokenize_sql(text)
    if not tokens:
        return text

    n = len(tokens)
    depth = 0
    boundaries = []
    i = 0
    while i < n:
        kind, tok = tokens[i]
        if kind == "lparen":
            depth += 1
            i += 1
            continue
        if kind == "rparen":
            depth -= 1
            i += 1
            continue
        if depth == 0 and kind == "word":
            m = _match_clause(tokens, i)
            if m:
                kw_tokens, consumed = m
                boundaries.append((i, i + consumed, kw_tokens))
                i += consumed
                continue
        i += 1

    if not boundaries:
        return render_tokens(tokens) + (";" if trailing_semi else "")

    lines = []
    for bi, (start, end, kw_tokens) in enumerate(boundaries):
        keyword_text = " ".join(t for _, t in kw_tokens)
        upper_kw = keyword_text.upper()
        body_start = end
        body_end = boundaries[bi + 1][0] if bi + 1 < len(boundaries) else n
        body_tokens = tokens[body_start:body_end]

        if not body_tokens:
            lines.append(keyword_text)
            continue

        if upper_kw in MULTILINE_CLAUSES:
            seps = {","} if upper_kw not in ("WHERE", "HAVING", "ON") else {"AND", "OR"}
            groups = split_top_level(body_tokens, seps)
            if len(groups) <= 1:
                lines.append(keyword_text + " " + render_tokens(body_tokens))
            else:
                lines.append(keyword_text)
                is_comma = seps == {","}
                for gi, (prefix, g) in enumerate(groups):
                    r = render_tokens(g)
                    if is_comma:
                        suffix = "," if gi < len(groups) - 1 else ""
                        lines.append("    " + r + suffix)
                    else:
                        lines.append("    " + (prefix + " " + r if prefix else r))
        else:
            lines.append(keyword_text + " " + render_tokens(body_tokens))

    result = "\n".join(lines)
    if trailing_semi:
        result += ";"
    return result


if __name__ == "__main__":
    import sys
    print(beautify_sql(sys.stdin.read()))
