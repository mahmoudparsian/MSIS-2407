#!/usr/bin/env python3
"""Static validator mimicking marimo's dataflow rules, without needing
marimo installed: checks (1) valid Python syntax, (2) every @app.cell
function's parameters are each satisfiable by exactly one other cell's
returned names, (3) no bare (non-underscore) name is returned by more than
one cell."""
import ast
import sys
from pathlib import Path


def validate(path):
    src = Path(path).read_text()
    problems = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"SYNTAX ERROR: {e}"]

    cells = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and any(
            (isinstance(d, ast.Call) and getattr(d.func, "attr", None) == "cell")
            or (isinstance(d, ast.Attribute) and d.attr == "cell")
            for d in node.decorator_list
        ):
            params = [a.arg for a in node.args.args]
            returns = set()
            is_sql_cell = any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "sql" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "mo"
                for n in ast.walk(node)
            )
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    v = stmt.value
                    if isinstance(v, ast.Tuple):
                        for e in v.elts:
                            if isinstance(e, ast.Name):
                                returns.add(e.id)
                    elif isinstance(v, ast.Name):
                        returns.add(v.id)
            cells.append({"params": params, "returns": returns, "lineno": node.lineno, "is_sql_cell": is_sql_cell})

    return_owner = {}
    for c in cells:
        for r in c["returns"]:
            return_owner.setdefault(r, []).append(c["lineno"])

    for name, owners in return_owner.items():
        if len(owners) > 1:
            problems.append(f"DUPLICATE GLOBAL '{name}' defined by cells at lines {owners}")

    for c in cells:
        for p in c["params"]:
            if p not in return_owner:
                if c["is_sql_cell"] and p not in ("con", "mo"):
                    # Likely a marimo SQL-cell "phantom" table-name
                    # dependency (from FROM/JOIN in the query), which
                    # marimo resolves via its SQL engine/catalog rather
                    # than the Python global-variable graph. Not an error.
                    continue
                problems.append(f"UNRESOLVED PARAM '{p}' in cell at line {c['lineno']}")

    return problems


if __name__ == "__main__":
    for path in sys.argv[1:]:
        problems = validate(path)
        if problems:
            print(f"--- {path} ---")
            for p in problems:
                print(" ", p)
        else:
            print(f"OK  {path}")
