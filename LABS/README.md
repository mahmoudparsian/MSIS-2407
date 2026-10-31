# Labs

[← Course home](../README.md) · **Labs — 10 sessions × 70 points**

Every class session has a hands-on lab. Labs are where you practice the
session's ideas — designing, building, and managing real databases — and they
make up **700 of the course's 1,000 points**.

> **This folder fills up during the term.** Each session's labs appear here
> during class, at the start of the lab block. Before Session 1 it holds only
> this page.

---

## How a Lab Works

| When | What happens |
|---|---|
| **In class** — last ~40 minutes | The session's labs are published here. You start the lab, with the instructor available for questions |
| **By 11:00 pm Pacific Time** the same day | Finish and submit the lab on Camino |
| **After 11:00 pm** | Solutions are added to the same session folder |

**Two versions per session:**

- **a** — the core lab
- **b** — a step more challenging

The instructor announces in class which lab(s) count for that session.
Session 8 also has an optional **c** lab for extra practice — **not graded**.

**What you submit:** your completed notebook. Most labs also ask for a short
memo or a SQL file — the notebook says which.

---

## Running a Lab

Every lab is a [Marimo](https://marimo.io) notebook that **builds its own
data**, so there is nothing to download besides the notebook itself.

```bash
cd LABS/week1_lab1
marimo edit week1_lab1a_student_marimo.py
```

If you haven't set up the course software yet, see
[`software_installation/`](../software_installation/README.md).

### Self-checks

Each task has a cell you complete and a **self-check** cell right after it:

- ✅ — the task is right; move on.
- A `TODO` message — the task isn't finished yet. Unfinished tasks stop the
  notebook **on purpose**, so you always know where you are.

When every self-check shows ✅, the notebook's tasks are done — then add any
memo or SQL file the lab asks for, and submit on Camino.

### Getting new labs

- **Downloaded the ZIP?** Download the repository again after each session's
  labs are released.
- **Cloned with Git?** Run `git pull`.

Either way, **copy each lab into your own work folder before you start**, so
an update never overwrites your work.

---

## Lab Schedule

| Week | Session | Folder | Topic |
|:---:|:---:|---|---|
| **1** | 1 | `week1_lab1/` | Entities, attributes, keys; reverse-engineering an ER model |
| | 2 | `week1_lab2/` | From business rules to an ER model; Enhanced ER |
| **2** | 3 | `week2_lab1/` | Normalization: 1NF → 3NF → BCNF |
| | 4 | `week2_lab2/` | Keys and constraints; 4NF |
| **3** | 5 | `week3_lab1/` | Typed DDL and loading messy data |
| | 6 | `week3_lab2/` | Transactions and concurrency |
| **4** | 7 | `week4_lab1/` | Star schemas and dimensional modeling |
| | 8 | `week4_lab2/` | Querying a warehouse; relational vs. object-relational vs. document |
| **5** | 9 | `week5_lab1/` | Security, access control, indexes, auditing |
| | 10 | `week5_lab2/` | Backup, recovery, and data quality |

Each session folder also gets its own `README.md` listing its files when it is
released.

---

## Grading and Policies

| Policy | In short |
|---|---|
| **Points** | 10 labs × 70 points = 700 |
| **Lowest lab** | Replaced by the average of your other nine |
| **Late work** | −7 points for each started 24 hours after the deadline, counted from your last upload; more than 72 hours late: 0 |
| **Absence** | A missed session's lab scores zero — the in-class start is part of the lab. Documented emergencies and approved absences: contact the instructor |
| **Your own work** | Discussing concepts is fine; sharing queries, schemas, or notebooks is not |

The full policy is in
[`ASSIGNMENTS_and_GRADING.md`](../course_information/ASSIGNMENTS_and_GRADING.md).

---

[← Course home](../README.md)
