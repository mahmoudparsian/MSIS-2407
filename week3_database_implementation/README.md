# Week 3 — Database Implementation

[← Week 2](../week2_relational_database_design/README.md) · [Course home](../README.md) · **Week 3 of 5** · [Week 4 →](../week4_data_warehousing/README.md)

This week builds the design for real: typed tables with constraints, loading
and validating messy data, making queries fast with indexes, and keeping data
correct with transactions — in DuckDB, with MySQL for contrast.

**Topics:** `CREATE TABLE`, data types, and constraints · data loading and
validation · indexing and query performance · transactions, ACID, and
concurrency

## At a Glance

| Session | Lab topic | Lab folder |
|:---:|---|---|
| **5** | Typed DDL and loading messy data | `LABS/week3_lab1/` |
| **6** | Transactions and concurrency | `LABS/week3_lab2/` |

---

## Slides

[`week3_lecture_slides.pdf`](week3_lecture_slides.pdf) — the week's deck
(source: [`week3_lecture_slides.md`](week3_lecture_slides.md)).

## Lecture Notes

| Notes | What they cover |
|---|---|
| [Part 1 — Implementation Foundations](lecture_notes_01_Implementation_Foundations.md) | Why two systems (DuckDB and MySQL); creating tables with primary and foreign keys; constraints that reject bad data; where DuckDB and MySQL syntax differ |
| [Part 2 — Data Loading](lecture_notes_02_Data_Loading_and_Transition.md) | ETL from a raw CSV: extract, inspect, clean and cast, load into MySQL, and validate the load |
| [Part 3 — Indexing and Performance](lecture_notes_03_Indexing_Performance.md) | Full table scans vs. indexes; when to index and when not to; why DuckDB's columnar zone maps change the answer |
| [Part 4 — Transactions and ACID](lecture_notes_04_Transactions_ACID.md) | Transactions and the ACID properties; autocommit; concurrency and lost updates; DuckDB's optimistic concurrency; isolation levels |

## Notebook

| Notebook | What it shows |
|---|---|
| [`Week3_Notebook_marimo.py`](Week3_Notebook_marimo.py) | Load, validate, index, transact: land a raw file, quarantine bad rows, load a typed schema, validate and reload safely, test constraints, measure indexes, run transactions, and watch two writers collide — then the same work in MySQL |

## Datasets

| File | What it is |
|---|---|
| [`Week3_dataset.csv`](Week3_dataset.csv) | The source file loaded in the notebook (which adds two broken rows, as a real export would contain) — described in [its notes](Week3_dataset.csv.NOTES.md) |
| [`Week3_orders_dataset.csv`](Week3_orders_dataset.csv) | 50,000 synthetic orders for the larger load — columns described in [its notes](Week3_orders_dataset.csv.NOTES.md) |

## Walkthroughs: Loading a CSV File into a Table

| Walkthrough | What it shows |
|---|---|
| [`load_csv_to_table_duckdb/`](load_csv_to_table_duckdb/) | A Python script that creates a DuckDB table from `employees.csv` |
| [`load_csv_to_table_mysql/`](load_csv_to_table_mysql/README.md) | The same in MySQL, two ways — row-by-row `INSERT` and bulk `LOAD DATA LOCAL`. **Optional:** needs MySQL (installation Step 4); no lab or exam question depends on it |

---

## Labs

Each session's labs are published in [`LABS/`](../LABS/) during class — an
**a** lab (core) and a **b** lab (a step more challenging); the instructor
announces which count. Solutions are added after the 11:00 pm deadline.

## Running the Notebook

```bash
marimo edit week3_database_implementation/Week3_Notebook_marimo.py
```

---

[← Week 2](../week2_relational_database_design/README.md) · [Course home](../README.md) · [Week 4 →](../week4_data_warehousing/README.md)
