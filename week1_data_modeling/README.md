# Week 1 — Data Management and Conceptual Modeling

[← Course home](../README.md) · **Week 1 of 5** · [Week 2 →](../week2_relational_database_design/README.md)

Before a database can be built, it has to be *designed*. This week moves from
using data to modeling it: what kinds of data an organization manages, and how
to capture a business's entities, attributes, and relationships in an ER
diagram.

**Topics:** data management in organizations · structured, semi-structured,
and unstructured data · entities, attributes, and relationships · ER
diagrams, cardinality, and participation · Enhanced ER (superclass / subclass)

## At a Glance

| Session | Lab topic | Lab folder |
|:---:|---|---|
| **1** | Entities, attributes, keys; reverse-engineering an ER model | `LABS/week1_lab1/` |
| **2** | From business rules to an ER model; Enhanced ER | `LABS/week1_lab2/` |

**Before Session 1:** install and verify the course software —
[`software_installation/`](../software_installation/README.md).

---

## Lecture Notes

Week 1 is taught from these notes (there is no separate slide deck this week).

**How Part 3 is used:** its **Part A** (the basics of structured, semi-structured
and unstructured data) is taught in **Session 1**; **Part B** (semi-structured data
in depth) is taught in **Session 8**, next to the document model; **Parts C–D**
(unstructured data, governance) are **optional reading**.

| Notes | What they cover |
|---|---|
| [`data_modeling_01_high_level.md`](data_modeling_01_high_level.md) | **Overview** — the purpose of a data model, types of data models, modeling techniques, and best practices |
| [`data_modeling_02_explained.md`](data_modeling_02_explained.md) | **The main notes** — structured vs. semi-structured vs. unstructured data; the modeling process (conceptual → logical → physical); entities, attributes, relationships, cardinality, participation; Enhanced ER |
| [`data_modeling_03_structured_semistructured_unstructured.md`](data_modeling_03_structured_semistructured_unstructured.md) | **Part 3, in depth** — managing semi-structured data (schema drift, shredding JSON into tables, design patterns) and unstructured data (retention, extraction), with a running insurance case |

### ER notation reference

| Guide | What it covers |
|---|---|
| [`ERD_Notation_Guide.md`](ERD_Notation_Guide.md) | Building blocks, cardinality, participation, Crow's Foot symbols, 1:N and M:N patterns, self-referencing relationships, and a quick-reference card |
| [`ERD_Crows_Foot_Notation.md`](ERD_Crows_Foot_Notation.md) | Crow's Foot notation at a glance |

---

## Notebooks

| Notebook | What it shows |
|---|---|
| [`Week1_Notebook_marimo.py`](Week1_Notebook_marimo.py) | From a flat file to entities, candidate keys, and tables; cardinality and participation; an EER specialization; why the flat design causes update anomalies. Uses [`Week1_dataset.csv`](Week1_dataset.csv) ([about the data](Week1_dataset.csv.NOTES.md)) |
| [`data_modeling_03_demo_marimo.py`](data_modeling_03_demo_marimo.py) | Runs every query from the Part 3 notes — semi-structured and unstructured data in DuckDB |

## Case Studies

Three worked examples, each taking one business from requirements to a
relational model — a written walkthrough plus a DuckDB notebook that builds
the model and proves its constraints reject bad data.

| Case study | Walkthrough | Notebook |
|---|---|---|
| **1 — Music catalog** | [`relational_data_modeling_music_catalog.md`](data_modeling_case_study_01_music_catalog/relational_data_modeling_music_catalog.md) | [`music_catalog_data_modeling_duckdb.py`](data_modeling_case_study_01_music_catalog/music_catalog_data_modeling_duckdb.py) |
| **2 — Book store** | [`relational_data_modeling_bookstore.md`](data_modeling_case_study_02_book_store/relational_data_modeling_bookstore.md) | [`bookstore_data_modeling_duckdb.py`](data_modeling_case_study_02_book_store/bookstore_data_modeling_duckdb.py) |
| **3 — E-commerce** (incl. an EER extension: overlapping, partial specialization) | [`relational_data_modeling_duckdb.md`](data_modeling_case_study_03_ecommerce/relational_data_modeling_duckdb.md) | [`ecommerce_data_modeling_duckdb.py`](data_modeling_case_study_03_ecommerce/ecommerce_data_modeling_duckdb.py) |

## Further Reading

Recommended articles, course notes and books on data modeling and the
relational model, with links: [`data_modeling_docs/`](data_modeling_docs/README.md).

---

## Labs

Each session's labs are published in [`LABS/`](../LABS/) during class — an
**a** lab (core) and a **b** lab (a step more challenging); the instructor
announces which count. Solutions are added after the 11:00 pm deadline.

## Running the Notebooks

```bash
marimo edit week1_data_modeling/Week1_Notebook_marimo.py
```

---

[← Course home](../README.md) · [Week 2 →](../week2_relational_database_design/README.md)
