---
marp: true
title: Installing DuckDB on MacBook
paginate: true
---

# Installing DuckDB on MacBook

DuckDB runs inside Python and is installed using **pip**.

We recommend installing it using:

```bash
python3 -m pip install duckdb
```

> **Full setup guide:** for every tool the course needs, follow
> `software_installation/macbook/README.md` — its setup script installs
> DuckDB for you.

---

# Step 1 — Install Python (if needed)

Download Python **3.10 or newer** from:

https://www.python.org/downloads/

Open the downloaded `.pkg` file and click through the installer.

> Use the **python.org** installer. A Homebrew Python blocks
> `pip install` with an `externally-managed-environment` error.

---

# Step 2 — Verify Python Installation

Open **Terminal** and run:

```bash
python3 --version
```

Example output:

```
Python 3.12.x
```

If you see `3.10` or higher, Python is installed correctly.

---

# Step 3 — Install DuckDB

Run in Terminal:

```bash
python3 -m pip install duckdb
```

Why this command?

- Works even if `pip` is not on your PATH
- Installs into the same Python that `python3` runs
- Avoids common environment issues

---

# Step 4 — Verify Installation

Start Python:

```bash
python3
```

Then run:

```python
import duckdb
print(duckdb.__version__)
```

Example output (the course needs **1.0 or newer**):

```
1.x.x
```

---

# Step 5 — Test DuckDB

Example Python test:

```python
import duckdb

con = duckdb.connect()

con.execute("SELECT 1+1").fetchall()
```

Output:

```
[(2,)]
```

DuckDB is now ready.

---

# Where We Will Use DuckDB

In this course DuckDB will be used for:

- every lab and week notebook (in **Marimo**)
- building schemas with keys and constraints
- loading and validating CSV data
- transactions, star schemas, and database administration
