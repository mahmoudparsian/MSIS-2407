# Assignments and Grading

[← Course home](../README.md) · **Course information**

| | |
|---|---|
| **Course** | MSIS-2407 — DBMS - Design, Development & Administration |
| **Quarter** | Winter 2027 (weeks 6–10) |

**Contents:** [1. Grading Policy](#1-grading-policy) ·
[2. Labs](#2-labs--how-each-session-works) ·
[3. Attendance](#3-class-attendance) ·
[4. Course Policies](#4-course-policies) ·
[5. The 1,000-Point System and Letter Grades](#5-the-1000-point-system-and-letter-grades)

---

## 1. Grading Policy

| Component | Details | Points |
|---|---|---:|
| 🧪 **Labs** | One lab per class session · 10 labs × 70 points | 700 |
| ✏️ **Final Exam** | Separate scheduled exam slot after Session 10 · 2 hours · closed books, notes, software, Internet, and phone · lock-down browser required | 300 |
| | **Total** | **1,000** |

- **Labs** (one per session — see [Section 2](#2-labs--how-each-session-works)):
  you **start** each lab in class and **submit** it on Camino **by 11:00 pm
  Pacific Time the same day**.
- **Final Exam:** one exam covering the whole course, held in a separate
  scheduled exam slot after the last class session (not during Session 10).
  It is 2 hours, closed books/notes/software/Internet/phone, and taken in a
  lock-down browser — see [Course Policy #2](#4-course-policies).

---

## 2. Labs — How Each Session Works

The course meets for **10 sessions** over 5 weeks (2 per week, Tuesday and
Thursday 7:35–9:10 pm), **95 minutes** each. Every session follows the same
pattern:

| Time | Activity |
|---|---|
| First ~55 minutes | Lecture and live demo of the session's topic |
| Last ~40 minutes | Students **start that session's lab** in class — enough to understand what it asks and get a working start, with the instructor available for questions |
| By **11:00 pm Pacific Time** the same day | Students finish and **submit** the lab on Camino |

Every session has two labs: **a** (core) and **b** (a step more challenging).
The instructor announces in class which lab(s) count for that session.
Session 8 also has an optional **c** lab for extra practice — **not graded**.

Every lab is a Marimo notebook. Each task has a cell you complete and a
**self-check** cell that prints ✅ when the task is right, so you know before
you submit. Most labs also ask for a short memo or a SQL file — the notebook
says which.

**Where to find them:** each session's labs are published in the course
repository's [`LABS/`](../LABS/) folder **during class**, at the start of the
lab block. **Solutions** are added to the same folder after the 11:00 pm
Pacific Time deadline.

| Week | Session | Lab topic |
|---|:---:|---|
| **1** — Data Management and Conceptual Modeling | 1 | Entities, attributes, keys; reverse-engineering an ER model |
| | 2 | From business rules to an ER model; Enhanced ER |
| **2** — Relational Design and Normalization | 3 | Normalization: 1NF → 3NF → BCNF |
| | 4 | Keys and constraints; 4NF |
| **3** — Database Implementation | 5 | Typed DDL and loading messy data |
| | 6 | Transactions and concurrency |
| **4** — Analytical and Non-Relational Data Systems | 7 | Star schemas and dimensional modeling |
| | 8 | Querying a warehouse; relational vs. object-relational vs. document |
| **5** — Database Administration and Management | 9 | Security, access control, indexes, auditing |
| | 10 | Backup, recovery, and data quality |

---

## 3. Class Attendance

**Attendance is mandatory.**

Each lab is started during the class session in which it is assigned. If you
are absent, you receive a zero (`0`) on that session's lab (70 points). There
is no way to make up a missed lab, because the in-class start, with
instructor support, is part of the lab.

> **Exception:** students with a documented emergency, illness, or
> university-approved absence (disability accommodation, religious
> observance, etc.) may arrange an alternative with the instructor in advance
> or within 48 hours. The "lowest lab replaced" policy (Course Policy #1) is
> intended to absorb ordinary, undocumented absences — it is not a substitute
> for accommodation.

---

## 4. Course Policies

1. **Lowest lab replaced.** The lowest lab score is replaced by the average of
   your other nine lab scores, so labs still total 700 points.

2. **Final Exam.** The Final Exam is **2 hours**, proctored in person in a
   separately scheduled exam slot, and **closed books, closed notes, closed
   software, closed Internet, and no phones**. You take it on your laptop in
   a **lock-down browser, which is required** — install it and run a test
   before the exam. The exam tests design reasoning and SQL directly:
   modeling, normalization, DDL and constraints, star schemas, transactions,
   security, and recovery.

3. **Focus of the labs.** Labs emphasize hands-on database design,
   implementation, and administration.

4. **What is graded.** Clear design reasoning and SQL logic are graded more
   heavily than minor formatting or syntax issues.

5. **No copy-paste.** You may use any appropriate resources to help you
   understand and complete your labs. However, the work you submit must
   reflect your own understanding and effort. Discussing general database
   concepts with classmates is fine; sharing queries, schemas, or notebooks
   is not.

6. **Late policy (labs).** A late lab loses **7 points** (10% of 70) for
   **each started 24-hour period** after the 11:00 pm Pacific Time deadline,
   counted from your last upload:

   | Last upload | Penalty |
   |---|---:|
   | by 11:00 pm on the session day | none |
   | up to 24 hours late (e.g. 11:01 pm) | −7 |
   | 24–48 hours late | −14 |
   | 48–72 hours late | −21 |
   | more than 72 hours late | not graded: 0 |

   Lateness is set by the **last** file you upload for the session, and the
   penalty comes off the session's 70-point score (never below 0). Example:
   a lab uploaded at 9:00 am the next day → −7. An extension must be
   arranged with the instructor **before** the deadline.

---

## 5. The 1,000-Point System and Letter Grades

The 1,000-point scale keeps grading simple, transparent, and easy to
understand:

- You always know exactly where you stand.
- No percentage conversions are required — divide by 10:

| Points | Percentage |
|---:|---:|
| 850 | 85% |
| 950 | 95% |

**Letter grades** (total points out of 1,000):

| Letter | Points (out of 1,000) | Percentage |
|:---:|---|---|
| A | 940 – 1,000 | 94% – 100% |
| A− | 900 – 939 | 90% – 93.9% |
| B+ | 870 – 899 | 87% – 89.9% |
| B | 830 – 869 | 83% – 86.9% |
| B− | 800 – 829 | 80% – 82.9% |
| C+ | 770 – 799 | 77% – 79.9% |
| C | 730 – 769 | 73% – 76.9% |
| C− | 700 – 729 | 70% – 72.9% |
| D+ | 670 – 699 | 67% – 69.9% |
| D | 630 – 669 | 63% – 66.9% |
| D− | 600 – 629 | 60% – 62.9% |
| F | below 600 | below 60% |

Fractional totals are rounded to the nearest whole point before this table
is applied (939.5 → 940 → A; 939.4 → 939 → A−).

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
