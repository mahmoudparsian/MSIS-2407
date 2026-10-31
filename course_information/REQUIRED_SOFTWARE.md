# Required Software

[← Course home](../README.md) · **Course information**

> **Took MSIS-2402 this quarter?** You already have everything the labs need.
> The only possible additions are `mysql-connector-python` (for one optional
> Week 3 walkthrough) and the lock-down browser (for the Final Exam).

Every lab is a Marimo notebook that builds its own data with DuckDB, so the
core setup is just **Python plus three packages**.

> **Installing?** Follow the step-by-step guide for your computer in
> [`software_installation/`](../software_installation/README.md). This page
> explains *what* each tool is and *why* the course uses it.

## At a Glance

| # | Tool | Needed for | Install |
|:---:|---|---|---|
| 1 | [Python](#1-python) | Everything | [python.org](https://www.python.org/downloads/) — 3.10+ |
| 2 | [DuckDB](#2-duckdb) | Every lab and notebook | `pip install duckdb` |
| 3 | [Marimo](#3-marimo-notebook) | Every lab and notebook | `pip install "marimo[sql]"` |
| 4 | [Pandas](#4-pandas) | Every lab and notebook | `pip install pandas` |
| 5 | [MySQL](#5-mysql-week-3-walkthrough-only) | *Optional* — one Week 3 walkthrough | [dev.mysql.com](https://dev.mysql.com/downloads/) + `pip install mysql-connector-python` |
| 6 | [A diagramming tool](#6-a-diagramming-tool) | ER diagrams in several labs | [draw.io](https://www.drawio.com) or [Lucidchart](https://www.lucidchart.com) |
| 7 | [Lock-down browser](#7-lock-down-browser-final-exam-only) | The Final Exam only | See below |

---

## 1. Python

🔗 [python.org](https://www.python.org)

**Version:** 3.10 or higher (we recommend 3.12+).

---

## 2. DuckDB

🔗 [duckdb.org](https://duckdb.org)

DuckDB is an open-source, in-process SQL database engine. It runs entirely
inside your Python process — no server to install or configure. It is the
engine for every lab, every week notebook, and every example in this course.

```bash
pip install duckdb
```

---

## 3. Marimo Notebook

🔗 [marimo.io](https://marimo.io)

Marimo is a reactive Python notebook. Every lab is a Marimo notebook: each
task has a cell you complete and a self-check cell that prints ✅ when the
task is right.

```bash
pip install "marimo[sql]"
```

The `[sql]` extra installs `sqlglot`, which Marimo needs to show SQL cells.
To open a notebook:

```bash
marimo edit <notebook>.py
```

---

## 4. Pandas

🔗 [pandas.pydata.org](https://pandas.pydata.org)

The labs read query results as Pandas DataFrames
(`con.execute(...).df()`), and the self-checks inspect them.

```bash
pip install pandas
```

---

## 5. MySQL (Week 3 walkthrough only)

🔗 [dev.mysql.com/downloads](https://dev.mysql.com/downloads/)

Week 3 compares DuckDB with MySQL, a client–server database, and includes a
walkthrough ([`load_csv_to_table_mysql/`](../week3_database_implementation/load_csv_to_table_mysql/README.md))
that loads a CSV file into MySQL from Python. **No lab and no exam question
needs MySQL.** To run the walkthrough yourself, you need MySQL Community
Server and:

```bash
pip install mysql-connector-python
```

Step-by-step install: Step 4 (optional) of the
[installation guide](../software_installation/README.md).

### DuckDB vs. MySQL — what matters for this course

| Topic | DuckDB | MySQL |
|---|---|---|
| Architecture | Embedded, in-process | Networked server with many clients |
| Keys, constraints, normalization | Supported (foreign keys: `RESTRICT` / `NO ACTION` only) | Supported, including `ON DELETE CASCADE` |
| Transactions | ACID, snapshot isolation; a second writer to the same row gets a conflict error | ACID, row locking; a second writer waits |
| Users, roles, `GRANT` / `REVOKE` | None — access control is built with views and enforced by the application | Full account and privilege system |

Week 3's lecture notes go into these differences in detail.

---

## 6. A Diagramming Tool

Several labs ask for an ER diagram alongside the notebook. Any tool that
exports an image or PDF is fine. Free options:

- [draw.io / diagrams.net](https://www.drawio.com) — runs in the browser or as
  a desktop app
- [Lucidchart](https://www.lucidchart.com) — free tier

---

## 7. Lock-down browser (Final Exam only)

**Respondus LockDown Browser** — [SCU LockDown Browser download](https://download.respondus.com/lockdown/download.php?ID=597745928)

The Final Exam is taken on your own laptop in a **required lock-down
browser**, which blocks other applications and websites during the exam. You
**don't** need it for the first class: install it and take the **practice
quiz** at least **one week before the exam**. If you set it up for
MSIS-2402's Final, the same installation works. Step-by-step instructions are
in Step 5 of the [installation guide](../software_installation/README.md).

---

## Quick Install Summary

| Step | What to do |
|:---:|---|
| **1** | Install Python from [python.org](https://www.python.org/downloads/) |
| **2** | Install the Python packages (command below) |
| **3** | Check that everything works — Step 3 of the [installation guide](../software_installation/README.md) runs a verification notebook in Marimo |
| *Optional* | MySQL Community Server + `pip install mysql-connector-python` (Week 3 walkthrough) · a diagramming tool · the lock-down browser before the Final |

```bash
pip install duckdb "marimo[sql]" pandas
```

**Step-by-step setup guides** for each operating system — with a setup
script and a Marimo verification notebook — are in
[`software_installation/`](../software_installation/README.md). DuckDB-only
guides: [macOS](../5_weeks_outline/duckdb_introduction/installing_duckdb_on_macbook.md) ·
[Windows](../5_weeks_outline/duckdb_introduction/installing_duckdb_on_windows.md).

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
