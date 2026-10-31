---
marp: true
title: Installing DuckDB on Windows
paginate: true
---

# Installing DuckDB on Windows

DuckDB runs inside Python and is installed using **pip**.

Recommended command:

```bash
python -m pip install "duckdb>=2.0"
```

> **Full setup guide:** for every tool the course needs, follow
> `software_installation/windows/README.md` — its setup script installs
> DuckDB for you.

---

# Step 1 — Install Python

Go to https://www.python.org/downloads/ and choose the
**standalone installer** — the link that says
*"Or get the standalone installer for Python 3.x.x"* —
not the "Python install manager".

On the installer's first screen, make sure to check:

✔ **Add python.exe to PATH**

This step is very important.

---

# Step 2 — Verify Python Installation

Open **Command Prompt**.

Run:

```bash
python --version
```

Example:

```
Python 3.12.x
```

If you see `3.11` or higher, Python is installed.

---

# Step 3 — Install DuckDB

Run:

```bash
python -m pip install "duckdb>=2.0"
```

Why use this command?

- works even if `pip` is not recognized
- installs into the same Python that `python` runs
- avoids PATH issues

---

# Step 4 — Verify Installation

Start Python:

```bash
python
```

Then run:

```python
import duckdb
print(duckdb.__version__)
```

Example output (the course needs **1.0 or newer**):

```
2.x.x
```

---

# Step 5 — Test DuckDB

Run inside Python:

```python
import duckdb

con = duckdb.connect()

con.execute("SELECT 1+1").fetchall()
```

Output:

```
[(2,)]
```

DuckDB is working.

---

# Troubleshooting

If you see:

```
'pip' is not recognized as an internal or external command
```

Use:

```bash
python -m pip install "duckdb>=2.0"
```

If Python is not recognized:

- reinstall Python from python.org
- check **Add python.exe to PATH** on the first screen
- close and reopen Command Prompt
