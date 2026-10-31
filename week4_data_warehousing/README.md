# Week 4 — Analytical and Non-Relational Data Systems

[← Week 3](../week3_database_implementation/README.md) · [Course home](../README.md) · **Week 4 of 5** · [Week 5 →](../week5_database_management/README.md)

Operational databases are built for recording transactions; analysis needs a
different design. This week builds a data warehouse with a star schema, then
steps outside the relational model to compare it with object-oriented and
document databases.

**Topics:** OLTP vs. OLAP and data warehouses · star schemas: facts and
dimensions · grain, surrogate keys, and slowly changing dimensions (Type 2) ·
relational vs. object-oriented and document models · semi-structured data: schema drift and shredding JSON · data lakes, lakehouses,
and the medallion architecture

## At a Glance

| Session | Lab topic | Lab folder |
|:---:|---|---|
| **7** | Star schemas and dimensional modeling | `LABS/week4_lab1/` |
| **8** | Querying a warehouse; relational vs. object-relational vs. document | `LABS/week4_lab2/` |

---

## Slides

[`week4_lecture_slides.pdf`](week4_lecture_slides.pdf) — the week's deck
(source: [`week4_lecture_slides.md`](week4_lecture_slides.md)).

## Lecture Notes

| Notes | What they cover |
|---|---|
| [Part 1 — Dimensional Modeling and OLAP](lecture_notes_01_Dimensional_Modeling.md) | OLTP vs. OLAP; the star schema; grain; surrogate keys and unknown members; slowly changing dimensions and the as-of join; additivity; two worked examples; lakes, lakehouses, and the medallion architecture |
| [Week 1, Part 3 — **Part B: Semi-Structured Data, In Depth**](../week1_data_modeling/data_modeling_03_structured_semistructured_unstructured.md#part-b--semi-structured-data-in-depth) | **Session 8.** Schema drift and how to profile it with SQL; renamed fields and changed types; shredding JSON into tables; nested arrays as hidden entities; design patterns and the EAV trap. Queries run in [`data_modeling_03_demo_marimo.py`](../week1_data_modeling/data_modeling_03_demo_marimo.py) |
| [Part 2 — Relational vs. Object-Oriented and Document Models](lecture_notes_02_Relational_vs_Object_Oriented.md) | The impedance mismatch; what object-oriented databases proposed and why they lost the mainstream; the document model; one order modeled three ways in DuckDB; a decision table; what a flexible schema costs |

## Notebook

| Notebook | What it shows |
|---|---|
| [`Week4_Notebook_marimo.py`](Week4_Notebook_marimo.py) | From an OLTP source to a star schema: grain, dimensions with a Type 2 history, the fact table, querying the star, testing the Type 2 invariants, additivity — then one order in three data models, and what a flexible schema lets through. Builds its data in code; no download needed |

## Further Practice

Reference data in [`datasets/`](../datasets/) for exploring on your own: a
[star schema](../datasets/warehouse_star_schema/) fact table and
[medallion-architecture](../datasets/medallion_architecture/) bronze, silver,
and gold tables.

---

## Labs

Each session's labs are published in [`LABS/`](../LABS/) during class — an
**a** lab (core) and a **b** lab (a step more challenging); the instructor
announces which count. Session 8 also has an optional, ungraded **c** lab.
Solutions are added after the 11:00 pm deadline.

## Running the Notebook

```bash
marimo edit week4_data_warehousing/Week4_Notebook_marimo.py
```

---

[← Week 3](../week3_database_implementation/README.md) · [Course home](../README.md) · [Week 5 →](../week5_database_management/README.md)
