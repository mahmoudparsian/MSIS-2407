# Week 2 — Relational Design and Normalization

[← Week 1](../week1_data_modeling/README.md) · [Course home](../README.md) · **Week 2 of 5** · [Week 3 →](../week3_database_implementation/README.md)

This week turns an ER model into relational tables, then tests that design
with functional dependencies and normalizes it — so each fact is stored once
and the anomalies of a "wide" table disappear.

**Topics:** mapping ER to a relational schema · primary keys, foreign keys,
and integrity constraints · functional dependencies and anomalies · 1NF, 2NF,
3NF, BCNF, and 4NF · when to denormalize

## At a Glance

| Session | Lab topic | Lab folder |
|:---:|---|---|
| **3** | Normalization: 1NF → 3NF → BCNF | `LABS/week2_lab1/` |
| **4** | Keys and constraints; 4NF | `LABS/week2_lab2/` |

---

## Slides

[`week2_lecture_slides.pdf`](week2_lecture_slides.pdf) — the week's deck
(source: [`week2_lecture_slides.md`](week2_lecture_slides.md)).

## Lecture Notes

| Notes | What they cover |
|---|---|
| [Part 1 — Relational Design](lecture_notes_01_Relational_Design.md) | ER → relational mapping rules; entities become tables, relationships become foreign keys; 1:M and M:N patterns; keys and constraints; insert, update, and delete anomalies |
| [Part 2 — Normalization](lecture_notes_02_Normalization.md) | Functional dependencies, superkeys, and prime attributes; 1NF, 2NF, and 3NF step by step; a full worked example; BCNF and the 3NF-vs-BCNF trade-off; 4NF |

## Notebook

| Notebook | What it shows |
|---|---|
| [`Week2_Notebook_marimo.py`](Week2_Notebook_marimo.py) | Normalization *tested with SQL*: three anomalies, functional-dependency checks, 1NF, the 2NF/3NF decomposition, a proof that it is lossless, BCNF, and 4NF. Uses [`Week2_dataset.csv`](Week2_dataset.csv) ([about the data](Week2_dataset.csv.NOTES.md)) |

---

## Labs

Each session's labs are published in [`LABS/`](../LABS/) during class — an
**a** lab (core) and a **b** lab (a step more challenging); the instructor
announces which count. Solutions are added after the 11:00 pm deadline.

## Running the Notebook

```bash
marimo edit week2_relational_database_design/Week2_Notebook_marimo.py
```

---

[← Week 1](../week1_data_modeling/README.md) · [Course home](../README.md) · [Week 3 →](../week3_database_implementation/README.md)
