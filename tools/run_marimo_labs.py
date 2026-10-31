#!/usr/bin/env python3
"""Execute a marimo notebook's cells top-to-bottom in one shared namespace.

Marimo files are plain Python: a sequence of @app.cell-decorated functions.
For a linearly-written notebook (cells already in topological order in the
file) we can faithfully simulate execution by exec'ing each cell body in a
single shared globals dict. Underscore-prefixed names are cell-local in
marimo but harmless to leak here.

Usage: python3 run_marimo.py <file.py> [more.py ...]
"""
import ast
import sys
import types
from pathlib import Path


class FakeMD:
    def __init__(self, text=""):
        self.text = text

    def __repr__(self):
        return f"<md {self.text[:40]!r}>"


class FakeMo:
    """Minimal stand-in for `marimo as mo` so notebooks run headlessly."""

    def md(self, text=""):
        return FakeMD(text)

    def sql(self, query, engine=None, output=True):
        if engine is None:
            raise RuntimeError("mo.sql called without engine")
        return engine.execute(query).df()

    def callout(self, text="", kind="neutral"):
        return FakeMD(str(text))

    def accordion(self, d):
        return FakeMD(str(list(d)[:1]))

    def vstack(self, items, **k):
        return FakeMD("vstack")

    def hstack(self, items, **k):
        return FakeMD("hstack")

    def as_html(self, x):
        return FakeMD("html")

    def plain_text(self, t=""):
        return FakeMD(str(t))

    class _UI:
        def table(self, data=None, **k):
            return FakeMD("table")

    ui = _UI()


def run(path, verbose=False):
    src = Path(path).read_text()
    tree = ast.parse(src)
    g = {"__name__": "__marimo_test__", "__file__": str(path)}
    ncells = 0

    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and node.decorator_list):
            continue
        is_cell = any(
            (isinstance(d, ast.Call) and getattr(d.func, "attr", None) == "cell")
            or (isinstance(d, ast.Attribute) and d.attr == "cell")
            for d in node.decorator_list
        )
        if not is_cell:
            continue
        ncells += 1
        body = [s for s in node.body if not isinstance(s, ast.Return)]
        if not body:
            continue
        mod = ast.Module(body=body, type_ignores=[])
        ast.fix_missing_locations(mod)
        code = compile(mod, filename=f"{path}::cell{ncells}", mode="exec")
        try:
            exec(code, g)
        except Exception as e:
            src_line = getattr(node, "lineno", "?")
            raise RuntimeError(
                f"{Path(path).name}: cell #{ncells} (line {src_line}) raised "
                f"{type(e).__name__}: {e}"
            ) from e
        # after the import cell, swap real marimo for our fake if absent
        if "mo" in g and not isinstance(g["mo"], FakeMo):
            if isinstance(g["mo"], types.ModuleType) and g["mo"].__name__ == "marimo":
                pass
            else:
                g["mo"] = FakeMo()
        if verbose:
            print(f"  cell {ncells} ok")
    return ncells


if __name__ == "__main__":
    # Pre-install a fake `marimo` module so `import marimo as mo` works.
    fake = types.ModuleType("marimo")
    _f = FakeMo()
    fake.md = _f.md
    fake.sql = _f.sql
    fake.callout = _f.callout
    fake.accordion = _f.accordion
    fake.vstack = _f.vstack
    fake.hstack = _f.hstack
    fake.as_html = _f.as_html
    fake.plain_text = _f.plain_text
    fake.ui = _f.ui
    fake.App = lambda **k: types.SimpleNamespace(cell=lambda *a, **kk: (lambda f: f))
    sys.modules.setdefault("marimo", fake)

    failures = 0
    for p in sys.argv[1:]:
        try:
            n = run(p)
            print(f"PASS  {p}  ({n} cells)")
        except Exception as e:
            failures += 1
            print(f"FAIL  {p}\n      {e}")
    sys.exit(1 if failures else 0)
