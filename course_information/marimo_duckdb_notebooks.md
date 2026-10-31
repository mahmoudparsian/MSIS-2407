# Marimo Notebooks

[← Course home](../README.md) · **Course information**

Every notebook in this course is a [Marimo](https://marimo.io) notebook — a
plain Python file (`*_marimo.py`) with reactive cells, running SQL against
DuckDB. There are two kinds.

---

## 1. Week Demo Notebooks

Weeks 1–4 each have a demo notebook used in lecture:

| Week | Notebook | What it shows |
|:---:|---|---|
| **1** | [`Week1_Notebook_marimo.py`](../week1_data_modeling/Week1_Notebook_marimo.py) | A flat file → entities, keys, cardinality and participation, an EER specialization |
| **2** | [`Week2_Notebook_marimo.py`](../week2_relational_database_design/Week2_Notebook_marimo.py) | Anomalies, functional dependencies, 1NF → 3NF, a lossless-join check, BCNF, 4NF |
| **3** | [`Week3_Notebook_marimo.py`](../week3_database_implementation/Week3_Notebook_marimo.py) | Typed DDL, quarantine and load validation, an idempotent reload, measured indexes, transactions and concurrency |
| **4** | [`Week4_Notebook_marimo.py`](../week4_data_warehousing/Week4_Notebook_marimo.py) | A star schema with surrogate keys and SCD Type 2, `ROLLUP`, relational vs. nested vs. document models |

- **Data:** Weeks 1–3 read the CSV files in their own folder (wherever you
  start Marimo from); Week 4 builds its data in code.
- **Built-in checks:** every query cell checks its own result, so a cell that
  runs without an error has also produced the expected numbers.

```bash
marimo edit week3_database_implementation/Week3_Notebook_marimo.py
```

Week 1 also has three [worked case studies](../week1_data_modeling/README.md#case-studies),
each with its own notebook.

## 2. Lab Notebooks

Every class session has a lab, published in [`LABS/`](../LABS/) during class
(see [`ASSIGNMENTS_and_GRADING.md`](ASSIGNMENTS_and_GRADING.md)). Lab notebooks
build all their own data, so they run from anywhere:

```bash
marimo edit week1_lab1a_student_marimo.py
```

Each task has a cell you complete and a **self-check** cell that prints ✅ when
the task is right. An unfinished task stops with a `TODO` message — that is
deliberate.

---

## Requirements

```bash
pip install "duckdb>=2.0" pandas "marimo[sql]"
```

See [`REQUIRED_SOFTWARE.md`](REQUIRED_SOFTWARE.md) for details.

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
