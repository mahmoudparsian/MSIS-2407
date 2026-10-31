#!/usr/bin/env python3
"""
Convert Jupyter notebooks (DuckDB-based SQL teaching notebooks) into Marimo
notebooks, using native `mo.sql()` cells wherever a cell is essentially just
running one SQL query.

Stdlib only (no marimo/duckdb needed to run this converter).
"""
import ast
import builtins as _builtins
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sql_beautify import beautify_sql

BUILTIN_NAMES = set(dir(_builtins)) | {
    "__name__", "__file__", "__doc__", "__builtins__", "self", "cls",
    "True", "False", "None", "NotImplemented", "Ellipsis",
}

CON_VAR = "con"

SQL_METHOD_TAILS = {"df", "fetchdf", "fetch_df", "pl", "arrow", "show", "fetchall", "fetchone", "to_df"}


# ---------------------------------------------------------------------------
# Free-variable / bound-variable analysis
# ---------------------------------------------------------------------------

class FreeVarCollector(ast.NodeVisitor):
    """Scope-aware free-variable collector.

    `outer_scope` is a *shared, mutable* set representing names already bound
    at the cell's top level (persists across sequential calls for different
    top-level statements in the same cell, allowing us to correctly treat
    `df = f(df)` as reading an external `df` only if it hasn't been locally
    defined yet).
    """

    def __init__(self, outer_scope):
        self.scopes = [outer_scope]
        self.free = set()

    def _bind_current(self, name):
        self.scopes[-1].add(name)

    def _is_bound(self, name):
        return any(name in s for s in self.scopes)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            if not self._is_bound(node.id):
                self.free.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self._bind_current(node.id)

    def visit_arg(self, node):
        self._bind_current(node.arg)

    def _visit_function_like(self, node, is_lambda=False):
        args = node.args
        # defaults evaluated in enclosing scope
        for d in list(args.defaults) + [d for d in args.kw_defaults if d]:
            self.visit(d)
        if not is_lambda:
            for dec in node.decorator_list:
                self.visit(dec)
        self.scopes.append(set())
        for a in args.posonlyargs + args.args + args.kwonlyargs:
            self.scopes[-1].add(a.arg)
        if args.vararg:
            self.scopes[-1].add(args.vararg.arg)
        if args.kwarg:
            self.scopes[-1].add(args.kwarg.arg)
        if is_lambda:
            self.visit(node.body)
        else:
            for stmt in node.body:
                self.visit(stmt)
        self.scopes.pop()

    def visit_FunctionDef(self, node):
        self._bind_current(node.name)
        self._visit_function_like(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        self._visit_function_like(node, is_lambda=True)

    def visit_ClassDef(self, node):
        self._bind_current(node.name)
        for dec in node.decorator_list:
            self.visit(dec)
        for base in node.bases:
            self.visit(base)
        for kw in node.keywords:
            self.visit(kw.value)
        self.scopes.append(set())
        for stmt in node.body:
            self.visit(stmt)
        self.scopes.pop()

    def _visit_comprehension(self, generators, elts):
        self.scopes.append(set())
        for gen in generators:
            self.visit(gen.iter)
            for tnode in ast.walk(gen.target):
                if isinstance(tnode, ast.Name):
                    self.scopes[-1].add(tnode.id)
            for cond in gen.ifs:
                self.visit(cond)
        for e in elts:
            self.visit(e)
        self.scopes.pop()

    def visit_ListComp(self, node):
        self._visit_comprehension(node.generators, [node.elt])

    def visit_SetComp(self, node):
        self._visit_comprehension(node.generators, [node.elt])

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node.generators, [node.elt])

    def visit_DictComp(self, node):
        self._visit_comprehension(node.generators, [node.key, node.value])

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self._bind_current(name)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname or alias.name
            self._bind_current(name)

    def visit_ExceptHandler(self, node):
        if node.name:
            self._bind_current(node.name)
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def visit_Global(self, node):
        pass

    def visit_Nonlocal(self, node):
        pass


def analyze_cell(tree):
    """Return (defs, refs) for a cell's top-level statement list."""
    outer_scope = set()
    free = set()
    for stmt in tree.body:
        collector = FreeVarCollector(outer_scope)
        collector.visit(stmt)
        free |= collector.free
    defs = outer_scope - BUILTIN_NAMES
    refs = free - BUILTIN_NAMES
    return defs, refs


# ---------------------------------------------------------------------------
# SQL-pattern cell detection
# ---------------------------------------------------------------------------

def find_sql_wrapper_functions(all_trees):
    """Detect notebook-defined helper functions like:

        def show_query(sql):
            print(sql)
            return con.execute(sql).df()

    i.e. a thin wrapper whose last statement returns con.execute(<its own
    single str param>)/con.sql(...). Returns a set of such function names.
    """
    wrappers = set()
    for tree in all_trees:
        for stmt in tree.body:
            if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = stmt.args
            posargs = args.posonlyargs + args.args
            if len(posargs) != 1 or args.vararg or args.kwarg or args.kwonlyargs:
                continue
            param_name = posargs[0].arg
            if not stmt.body:
                continue
            last = stmt.body[-1]
            if not (isinstance(last, ast.Return) and isinstance(last.value, ast.Call)):
                continue
            call = last.value
            if not isinstance(call.func, ast.Attribute):
                continue
            base = call.func.value
            attr = call.func.attr
            # allow one zero-arg tail method e.g. .df()/.show(), directly on con.execute/sql
            inner = call
            if isinstance(base, ast.Call) and isinstance(base.func, ast.Attribute):
                if attr in SQL_METHOD_TAILS and not call.args and not call.keywords:
                    inner = base
                    base = inner.func.value
                    attr = inner.func.attr
            if isinstance(base, ast.Name) and base.id == CON_VAR and attr in ("execute", "sql"):
                if len(inner.args) == 1 and isinstance(inner.args[0], ast.Name) and inner.args[0].id == param_name:
                    wrappers.add(stmt.name)
    return wrappers


def _strip_sql_call_tail(call_node, wrapper_fns):
    """If `call_node` is `<base>.method1().method2()...`, walk back through
    trailing zero-arg method calls (.df(), .show(), etc.) to find the base
    `con.execute(...)`/`con.sql(...)`/`<wrapper_fn>(...)` call. Returns that
    base Call node, or None."""
    node = call_node
    while True:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in wrapper_fns:
                return node
            if isinstance(node.func, ast.Attribute):
                base = node.func.value
                attr = node.func.attr
                if isinstance(base, ast.Name) and base.id == CON_VAR and attr in ("execute", "sql"):
                    return node
                if attr in SQL_METHOD_TAILS and not node.args and not node.keywords:
                    node = base
                    continue
        return None


def _sql_string_node(call_node):
    """Given the base con.execute(...)/con.sql(...)/wrapper(...) call node,
    return the single string/f-string argument node, or None if not a clean
    single string argument (e.g. parameterized query, multiple args)."""
    if len(call_node.args) != 1 or call_node.keywords:
        return None
    arg = call_node.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        if "?" in arg.value:
            return None
        return arg
    if isinstance(arg, ast.JoinedStr):
        return arg
    return None


def _is_droppable_tail_stmt(s, target):
    """print(...), display(target), bare `target`, target.head(...)/tail(...)"""
    if not isinstance(s, ast.Expr):
        return False
    v = s.value
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "print":
        return True
    if target is None:
        return False
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "display":
        return len(v.args) == 1 and isinstance(v.args[0], ast.Name) and v.args[0].id == target
    if isinstance(v, ast.Name) and v.id == target:
        return True
    if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
            and isinstance(v.func.value, ast.Name) and v.func.value.id == target
            and v.func.attr in ("head", "tail")):
        return True
    return False


def match_pattern_a(tree, wrapper_fns):
    """Assigned/bare single SQL-call cell, with optional trailing
    print()/display(target)/bare-`target`/target.head() display statements
    (common Jupyter "compute then show" tail)."""
    body = tree.body
    if len(body) < 1:
        return None
    stmt = body[0]
    target = None
    if isinstance(stmt, ast.Expr):
        call = stmt.value
    elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        target = stmt.targets[0].id
        call = stmt.value
    else:
        return None
    if not isinstance(call, ast.Call):
        return None
    base_call = _strip_sql_call_tail(call, wrapper_fns)
    if base_call is None:
        return None
    str_node = _sql_string_node(base_call)
    if str_node is None:
        return None

    i = 1
    while i < len(body):
        if _is_droppable_tail_stmt(body[i], target):
            i += 1
            continue
        return None
    wrapper_name = base_call.func.id if isinstance(base_call.func, ast.Name) else None
    return {"target": target, "sql_node": str_node, "wrapper": wrapper_name}


def match_pattern_b(tree, wrapper_fns):
    """SQL-string-variable + optional print()s + execute/wrapper-call +
    optional display tail."""
    body = tree.body
    if len(body) < 2:
        return None
    i = 0
    stmt = body[i]
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)):
        return None
    sql_var = stmt.targets[0].id
    val = stmt.value
    if not isinstance(val, (ast.Constant, ast.JoinedStr)):
        return None
    if isinstance(val, ast.Constant) and not isinstance(val.value, str):
        return None
    sql_node = val
    i += 1
    while i < len(body):
        s = body[i]
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Name) and s.value.func.id == "print":
            i += 1
            continue
        break
    if i >= len(body):
        return None
    stmt2 = body[i]
    if not (isinstance(stmt2, ast.Assign) and len(stmt2.targets) == 1 and isinstance(stmt2.targets[0], ast.Name)):
        return None
    df_var = stmt2.targets[0].id
    call = stmt2.value
    if not isinstance(call, ast.Call):
        return None
    base_call = _strip_sql_call_tail(call, wrapper_fns)
    if base_call is None:
        return None
    if len(base_call.args) != 1 or base_call.keywords:
        return None
    arg = base_call.args[0]
    if not (isinstance(arg, ast.Name) and arg.id == sql_var):
        return None
    i += 1
    while i < len(body):
        if _is_droppable_tail_stmt(body[i], df_var):
            i += 1
            continue
        return None
    wrapper_name = base_call.func.id if isinstance(base_call.func, ast.Name) else None
    return {"target": df_var, "sql_node": sql_node, "wrapper": wrapper_name}


CREATE_TABLE_RE = re.compile(
    r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+)?(?:TABLE|VIEW)\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+)[\"']?",
    re.I,
)
CTE_RE = re.compile(r"\bWITH\s+[\"']?(\w+)[\"']?\s+AS\s*\(", re.I)
FROM_JOIN_RE = re.compile(r"\b(?:FROM|JOIN)\s+[\"']?(\w+)[\"']?\s*(\()?", re.I)
REGISTER_RE = re.compile(r"\bcon\.register\(\s*[\"'](\w+)[\"']", re.I)
DUCKDB_TABLE_FUNCS = {
    "read_csv_auto", "read_csv", "read_parquet", "read_json", "read_json_auto",
    "generate_series", "range", "duckdb_functions", "duckdb_tables", "duckdb_views",
    "information_schema", "glob", "unnest", "duckdb_columns",
}


def extract_sql_table_defs_refs(sql_text):
    """Best-effort regex scan of a SQL string for tables it CREATEs and
    tables it references via FROM/JOIN (used to mirror marimo's own SQL-cell
    table-dependency tracking, which threads table names through cell
    signatures alongside real Python variables)."""
    defs = {m.group(1) for m in CREATE_TABLE_RE.finditer(sql_text)}
    ctes = {m.group(1).lower() for m in CTE_RE.finditer(sql_text)}
    refs = set()
    for m in FROM_JOIN_RE.finditer(sql_text):
        name, has_paren = m.group(1), m.group(2)
        if has_paren:
            continue
        if name.lower() in ctes or name.lower() in DUCKDB_TABLE_FUNCS:
            continue
        refs.add(name)
    return defs, refs


def extract_fstring_refs(node):
    refs = set()
    if isinstance(node, ast.JoinedStr):
        for part in node.values:
            if isinstance(part, ast.FormattedValue):
                sub_free = set()
                collector = FreeVarCollector(sub_free)
                collector.visit(part.value)
                refs |= (collector.free - BUILTIN_NAMES)
    return refs


# ---------------------------------------------------------------------------
# Magic-line stripping (preserve line/col positions)
# ---------------------------------------------------------------------------

def strip_magics(source):
    lines = source.split("\n")
    out = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("!") or stripped.startswith("%"):
            indent = line[: len(line) - len(stripped)]
            out.append(indent + "# " + stripped)
        else:
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Notebook -> units
# ---------------------------------------------------------------------------

def _resolve_module_public_names(mod_path):
    try:
        mod_tree = ast.parse(Path(mod_path).read_text())
    except SyntaxError:
        return set()
    names = set()
    all_list = None
    for s in mod_tree.body:
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "__all__":
            if isinstance(s.value, (ast.List, ast.Tuple)):
                all_list = [e.value for e in s.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    if all_list is not None:
        names |= set(all_list)
    else:
        for s in mod_tree.body:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not s.name.startswith("_"):
                names.add(s.name)
            elif isinstance(s, ast.Assign):
                for t in s.targets:
                    if isinstance(t, ast.Name) and not t.id.startswith("_"):
                        names.add(t.id)
    return names


def resolve_star_imports(tree, nb_dir):
    """For every `from X import *` at top level, resolve real public names
    by parsing sibling module X.py (respecting __all__ if present)."""
    names = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and any(a.name == "*" for a in stmt.names):
            if not stmt.module:
                continue
            mod_path = Path(nb_dir) / (stmt.module.replace(".", "/") + ".py")
            if not mod_path.exists():
                continue
            names |= _resolve_module_public_names(mod_path)
    return names


def rewrite_star_imports(source, nb_dir):
    """`from X import *` is a SyntaxError inside a function body (which is
    what every marimo cell becomes), so rewrite it to an explicit import
    list using the same resolution as resolve_star_imports."""
    def _repl(m):
        indent, module = m.group(1), m.group(2)
        mod_path = Path(nb_dir) / (module.replace(".", "/") + ".py")
        if not mod_path.exists():
            return m.group(0)
        names = sorted(_resolve_module_public_names(mod_path))
        if not names:
            return m.group(0)
        return f"{indent}from {module} import {', '.join(names)}"

    return re.sub(r"(?m)^([ \t]*)from\s+([\w.]+)\s+import\s+\*\s*$", _repl, source)


def build_units(nb_path):
    nb_dir = Path(nb_path).parent
    nb = json.loads(Path(nb_path).read_text())

    # First pass: clean + parse every code cell so we can detect
    # notebook-defined SQL-wrapper helper functions (e.g. `show_query`)
    # before doing pattern matching.
    prepared = []
    issues = []
    for idx, cell in enumerate(nb["cells"]):
        ctype = cell["cell_type"]
        src = "".join(cell["source"])
        if not src.strip():
            continue
        if ctype == "markdown":
            prepared.append({"kind": "markdown", "text": src})
            continue
        if ctype != "code":
            continue
        cleaned = strip_magics(src)
        cleaned = rewrite_star_imports(cleaned, nb_dir)
        try:
            tree = ast.parse(cleaned)
        except SyntaxError as e:
            issues.append(f"cell {idx}: SyntaxError parsing code cell: {e}")
            prepared.append({"kind": "raw", "text": src, "orig_idx": idx})
            continue
        prepared.append({"kind": "parsed", "cleaned": cleaned, "tree": tree, "orig_idx": idx})

    wrapper_fns = find_sql_wrapper_functions(
        [p["tree"] for p in prepared if p["kind"] == "parsed"]
    )

    units = []
    for p in prepared:
        if p["kind"] in ("markdown", "raw"):
            units.append(p)
            continue
        cleaned, tree, idx = p["cleaned"], p["tree"], p["orig_idx"]

        m = match_pattern_a(tree, wrapper_fns) or match_pattern_b(tree, wrapper_fns)
        if m is not None:
            sql_src = ast.get_source_segment(cleaned, m["sql_node"])
            extra_refs = extract_fstring_refs(m["sql_node"])
            defs = {m["target"]} if m["target"] else set()
            refs = {CON_VAR, "mo"} | extra_refs
            units.append({
                "kind": "sql",
                "target": m["target"],
                "sql_src": sql_src,
                "defs": defs,
                "refs": refs,
                "orig_idx": idx,
            })
        else:
            defs, refs = analyze_cell(tree)
            defs |= resolve_star_imports(tree, nb_dir)
            units.append({
                "kind": "pycode",
                "text": cleaned,
                "defs": defs,
                "refs": refs,
                "orig_idx": idx,
            })

    # Mirror marimo's own SQL-cell table-dependency tracking: scan every
    # cell (SQL and plain Python alike, since table creation often happens
    # via plain con.execute()/con.register() too) for tables that get
    # created, then thread referenced table names through SQL-cell
    # signatures as extra "phantom" parameters -- same as marimo's own
    # generated code does when you open/save a file in the real editor.
    known_tables = set()
    for u in units:
        text = u["sql_src"] if u["kind"] == "sql" else u.get("text", "")
        known_tables |= {m.group(1) for m in CREATE_TABLE_RE.finditer(text)}
        known_tables |= {m.group(1) for m in REGISTER_RE.finditer(text)}
    for u in units:
        if u["kind"] == "sql":
            _, sql_refs = extract_sql_table_defs_refs(u["sql_src"])
            u["table_params"] = sorted(sql_refs & known_tables)

    return units, issues


# ---------------------------------------------------------------------------
# Cross-cell collision resolution (SSA-ish versioning)
# ---------------------------------------------------------------------------

def resolve_names(units):
    """Returns (final_def_name, final_ref_name, orphans) keyed by
    (unit_index, name) -> resolved final identifier."""
    def_positions = defaultdict(list)
    for idx, u in enumerate(units):
        for n in u.get("defs", set()):
            def_positions[n].append(idx)

    colliding = {n for n, pos in def_positions.items() if len(pos) > 1}
    used_global_names = set(def_positions.keys())
    claimed_bare = set()

    current_global = {}
    final_def_name = {}
    final_ref_name = {}
    orphans = []

    for idx, u in enumerate(units):
        for n in sorted(u.get("refs", set())):
            if n in current_global and current_global[n] is not None:
                final_ref_name[(idx, n)] = current_global[n]
            else:
                final_ref_name[(idx, n)] = n
                orphans.append((idx, n))
        for n in sorted(u.get("defs", set())):
            if n not in colliding:
                chosen = n
            else:
                next_def_idx = next((p for p in def_positions[n] if p > idx), len(units))
                consumed = any(n in units[j].get("refs", set()) for j in range(idx + 1, next_def_idx))
                if not consumed:
                    chosen = "_" + n
                else:
                    if n not in claimed_bare:
                        chosen = n
                        claimed_bare.add(n)
                    else:
                        k = 2
                        while f"{n}_{k}" in used_global_names or f"{n}_{k}" in claimed_bare:
                            k += 1
                        chosen = f"{n}_{k}"
                        claimed_bare.add(chosen)
                        used_global_names.add(chosen)
            final_def_name[(idx, n)] = chosen
            current_global[n] = None if chosen.startswith("_") else chosen

    return final_def_name, final_ref_name, orphans


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def indent_block(text, spaces=4):
    pad = " " * spaces
    lines = text.split("\n")
    return "\n".join((pad + l) if l.strip() else "" for l in lines)


def md_cell_code(text):
    quote = '"""'
    if '"""' in text:
        quote = "'''"
    body = text.strip("\n")
    return (
        "@app.cell(hide_code=True)\n"
        "def _(mo):\n"
        f"    mo.md(r{quote}\n"
        f"{indent_block(body, 4)}\n"
        f"    {quote})\n"
        "    return\n"
    )


def return_stmt(names):
    names = [n for n in names if not n.startswith("_")]
    if not names:
        return "return"
    if len(names) == 1:
        return f"return ({names[0]},)"
    return f"return {', '.join(names)}"


def sql_literal_to_fstring_body(text):
    # Take a string-literal source segment (e.g. a triple-quoted SELECT
    # statement, or an f-string), extract the inner SQL, run it through the
    # beautifier, and return it re-wrapped as an f-string triple-quoted
    # literal -- marimo's canonical format for SQL cells (renders as a
    # clean SQL-only editor pane with the connection tucked into a
    # dropdown, instead of generic Python). Caller indents the result.
    m = re.match(r'^([a-zA-Z]*)(\'\'\'|"""|\'|")', text)
    if not m:
        return text
    prefix, quote = m.groups()
    inner = text[len(m.group(0)):-len(quote)]
    beautified = beautify_sql(inner) or inner.strip()
    return 'f"""\n' + beautified + '\n"""'


def sql_cell_code(unit, idx, final_def_name, final_ref_name, consumed):
    params = set()
    for n in unit["refs"]:
        params.add(final_ref_name[(idx, n)])
    params |= set(unit.get("table_params", []))
    params_str = ", ".join(sorted(params))
    target = unit["target"]
    # marimo's own SQL cells always assign the result (default `_df` when
    # first created via the UI) rather than leaving the call bare -- match
    # that "pure SQL" convention consistently.
    final_target = final_def_name[(idx, target)] if target else "_df"
    sql_lines = sql_literal_to_fstring_body(unit["sql_src"])
    call = (
        f"    {final_target} = mo.sql(\n"
        f"{indent_block(sql_lines, 8)},\n"
        f"        engine=con\n"
        f"    )\n"
    )
    keep = target and not final_target.startswith("_") and final_target in consumed
    ret = return_stmt([final_target]) if keep else "return"
    return (
        f"@app.cell\n"
        f"def _({params_str}):\n"
        f"{call}"
        f"    {ret}\n"
    )


def apply_renames(text, renames):
    for orig, final in renames.items():
        if orig == final:
            continue
        text = re.sub(rf"\b{re.escape(orig)}\b", final, text)
    return text


def pycode_cell_code(unit, idx, final_def_name, final_ref_name, consumed):
    renames = {}
    params = set()
    for n in unit["refs"]:
        final = final_ref_name[(idx, n)]
        params.add(final)
        if final != n:
            renames[n] = final
    returns = []
    for n in unit["defs"]:
        final = final_def_name[(idx, n)]
        if final != n:
            renames[n] = final
        if not final.startswith("_") and final in consumed:
            returns.append(final)
    text = apply_renames(unit["text"], renames)
    params_str = ", ".join(sorted(params))
    ret = return_stmt(sorted(returns))
    return (
        f"@app.cell\n"
        f"def _({params_str}):\n"
        f"{indent_block(text, 4)}\n"
        f"    {ret}\n"
    )


def raw_cell_code(unit):
    text = unit["text"]
    commented = "\n".join("# " + l for l in text.split("\n"))
    return (
        "@app.cell\n"
        "def _():\n"
        "    # NOTE: original cell could not be parsed automatically and was\n"
        "    # commented out for manual review.\n"
        f"{indent_block(commented, 4)}\n"
        "    return\n"
    )


DEP_MAP = {
    "duckdb": "duckdb",
    "pandas": "pandas",
    "pd": "pandas",
    "matplotlib": "matplotlib",
    "plt": "matplotlib",
    "folium": "folium",
    "numpy": "numpy",
    "np": "numpy",
}


def detect_deps(units):
    deps = {"marimo", "duckdb", "pandas"}
    for u in units:
        if u["kind"] == "pycode":
            for name, pkg in DEP_MAP.items():
                if re.search(rf"\b{name}\b", u["text"]):
                    deps.add(pkg)
    return sorted(deps)


def convert_notebook(nb_path, out_path):
    units, issues = build_units(nb_path)
    deps = detect_deps(units)

    needs_display = any(
        "display" in u.get("refs", set()) for u in units if u["kind"] == "pycode"
    )
    mo_unit = {"kind": "synthetic", "defs": {"mo"}, "refs": set()}
    synth_units = [mo_unit]
    if needs_display:
        synth_units.append({"kind": "synthetic", "defs": {"display"}, "refs": set()})
    code_units = synth_units + [u for u in units if u["kind"] in ("sql", "pycode")]
    final_def_name, final_ref_name, orphans = resolve_names(code_units)
    orphans = [o for o in orphans if o[1] not in ("mo", "display")]
    idx_map = {id(u): i for i, u in enumerate(code_units)}
    # marimo only keeps a defined name in a cell's return tuple if some
    # other cell actually consumes it -- match that instead of returning
    # every top-level name unconditionally.
    consumed = set(final_ref_name.values())

    parts = []
    parts.append("import marimo\n")
    parts.append('__generated_with = "0.23.10"')
    parts.append('app = marimo.App(width="medium")\n')
    parts.append("@app.cell\ndef _():\n    import marimo as mo\n    return (mo,)\n")
    if needs_display:
        parts.append(
            "@app.cell\n"
            "def _():\n"
            "    # Jupyter's IPython.display.display() shim, since these\n"
            "    # notebooks call display() directly for mid-cell output.\n"
            "    try:\n"
            "        from IPython.display import display\n"
            "    except ImportError:\n"
            "        def display(x):\n"
            "            print(x)\n"
            "    return (display,)\n"
        )

    for u in units:
        if u["kind"] == "markdown":
            parts.append(md_cell_code(u["text"]))
        elif u["kind"] == "raw":
            parts.append(raw_cell_code(u))
        elif u["kind"] == "sql":
            idx = idx_map[id(u)]
            parts.append(sql_cell_code(u, idx, final_def_name, final_ref_name, consumed))
        elif u["kind"] == "pycode":
            idx = idx_map[id(u)]
            parts.append(pycode_cell_code(u, idx, final_def_name, final_ref_name, consumed))

    parts.append('if __name__ == "__main__":\n    app.run()\n')

    full = "\n\n".join(parts) + "\n"
    Path(out_path).write_text(full)
    return issues, orphans, len(units)


if __name__ == "__main__":
    nb = sys.argv[1]
    out = sys.argv[2]
    issues, orphans, n = convert_notebook(nb, out)
    print(f"units={n} issues={issues} orphans={orphans}")
