# MSIS-2407 — DBMS - Design, Development & Administration

**Santa Clara University · Leavey School of Business**
**Information Systems & Business Analytics — Graduate Program**

![Course: MSIS-2407](https://img.shields.io/badge/Course-MSIS--2407-862633) ![Level: Graduate](https://img.shields.io/badge/Level-Graduate-555555) ![Units: 2](https://img.shields.io/badge/Units-2-555555) ![Duration: 5 weeks, 10 sessions](https://img.shields.io/badge/Duration-5%20weeks%2C%2010%20sessions-555555) ![Quarter: Winter 2027, weeks 6-10](https://img.shields.io/badge/Quarter-Winter%202027%2C%20weeks%206--10-555555)  
[![SQL engine: DuckDB](https://img.shields.io/badge/SQL%20engine-DuckDB-FFF000?logo=duckdb&logoColor=black)](https://duckdb.org) [![Notebooks: Marimo](https://img.shields.io/badge/Notebooks-Marimo-1C7ED6)](https://marimo.io) [![Language: Python](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)](https://www.python.org) [![Client-server: MySQL](https://img.shields.io/badge/Client--server-MySQL-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com)  
[![Builds on: MSIS-2402](https://img.shields.io/badge/Builds%20on-MSIS--2402-2E7D32)](https://github.com/mahmoudparsian/MSIS-2402)

| | |
|---|---|
| **Format** | 5 weeks · 10 sessions (Tuesday and Thursday, 7:35–9:10 pm, 95 minutes each) |
| **Credit** | 2 units |
| **Quarter** | Winter 2027 (weeks 6–10) |
| **Instructor** | Dr. Mahmoud Parsian |
| **Builds on** | MSIS-2402 — Database Management Systems: Fundamentals of SQL |
| **Primary tools** | [DuckDB](https://duckdb.org) · [Marimo](https://marimo.io) notebooks · Python · MySQL (Week 3) |

---

## Contents

1. [Course Description](#course-description)
2. [Learning Outcomes](#learning-outcomes)
3. [Course Schedule](#course-schedule)
4. [Grading at a Glance](#grading-at-a-glance)
5. [Getting Started](#getting-started)
6. [Weekly Materials](#weekly-materials)
7. [Repository Structure](#repository-structure)
8. [Course Policies & Information](#course-policies--information)

---

## Course Description

From the [SCU Graduate Bulletin](https://www.scu.edu/bulletin/graduate/leavey-school-of-business/chapter-7/information-systems-and-business-analytics-isba.html):

> This course presents technical and managerial approaches to the analysis,
> design, and management of business data, databases, and database management
> systems. The topics include structured and unstructured data management, a
> comparison of relational and object-oriented databases, relational database
> conceptual and logical design, and database implementation and
> administration.

### From MSIS-2402 to MSIS-2407

**MSIS-2402** taught you how to *query* data: SQL, joins, aggregation, and
analytical SQL in DuckDB. **MSIS-2407** teaches you how databases are
*designed, built, and managed* — taking you from SQL user to data-system
designer and decision-maker.

<p align="center"><b>Model → Normalize → Build → Analyze → Manage</b></p>

---

## Learning Outcomes

By the end of the course, you will be able to:

- Distinguish structured, semi-structured, and unstructured data
- Design conceptual models with ER and Enhanced ER (EER) diagrams
- Convert conceptual models into logical relational schemas, and normalize
  them (1NF through BCNF, and 4NF)
- Implement databases in SQL, including indexes and transactions
- Compare relational, object-oriented, and document data models
- Design data warehouses and use them to generate business insights
- Secure, back up, and govern a database

---

## Course Schedule

| Week | Module | Session | Lab topic |
|:---:|---|:---:|---|
| **1** | [Data Management and Conceptual Modeling](week1_data_modeling/) | 1 | Entities, attributes, keys; reverse-engineering an ER model |
| | | 2 | From business rules to an ER model; Enhanced ER |
| **2** | [Relational Design and Normalization](week2_relational_database_design/) | 3 | Normalization: 1NF → 3NF → BCNF |
| | | 4 | Keys and constraints; 4NF |
| **3** | [Database Implementation](week3_database_implementation/) | 5 | Typed DDL and loading messy data |
| | | 6 | Transactions and concurrency |
| **4** | [Analytical and Non-Relational Data Systems](week4_data_warehousing/) | 7 | Star schemas and dimensional modeling |
| | | 8 | Querying a warehouse; relational vs. object-relational vs. document |
| **5** | [Database Administration and Management](week5_database_management/) | 9 | Security, access control, indexes, auditing |
| | | 10 | Backup, recovery, and data quality |

**A typical session:**

| Time | Activity |
|---|---|
| First ~55 minutes | Lecture and live demo |
| Last ~40 minutes | Start the session's lab in class, with the instructor available |
| By **11:00 pm Pacific Time** the same day | Finish and submit the lab on Camino |

### How the catalog topics map to the weeks

| Catalog topic | Week |
|---|:---:|
| Structured and unstructured data management | 1 |
| Relational database conceptual and logical design | 1–2 |
| Database implementation and administration | 3, 5 |
| Comparison of relational and object-oriented databases | 4 |

Week 4 also covers **data warehousing** for analytical workloads — not named
in the catalog, but central to work in business analytics and information
systems.

---

## Grading at a Glance

| Component | Points |
|---|---:|
| **Labs** — one per session, 10 × 70 points | 700 |
| **Final Exam** — 2 hours, closed book, lock-down browser, separate exam slot after Session 10 | 300 |
| **Total** | **1,000** |

- Each session has an **a** lab (core) and a **b** lab (a step more
  challenging). The instructor announces in class which lab(s) count for that
  session. Session 8 also has an optional, ungraded **c** lab.
- Every lab is a Marimo notebook with built-in **self-checks** that print ✅
  when a task is right, so you know before you submit.
- Labs are published in [`LABS/`](LABS/) at the start of each lab block;
  solutions are added after the 11:00 pm Pacific Time deadline.

The full policy — attendance, late submissions, and the Final Exam format — is
in [`ASSIGNMENTS_and_GRADING.md`](course_information/ASSIGNMENTS_and_GRADING.md).

---

## Getting Started

**Before the first session** (set aside about 45 minutes):

1. **Install and verify the course software.** Follow the guide for your
   operating system — [macOS](software_installation/macbook/README.md) or
   [Windows](software_installation/windows/README.md) — starting from
   [`software_installation/README.md`](software_installation/README.md).
   *Just finished MSIS-2402 on the same computer?* You already have the tools;
   the guide shows the quick check to run.
2. **Bring a laptop to every session** — labs start in class. See
   [`LAPTOP.md`](course_information/LAPTOP.md).
3. **Read the grading policy** in
   [`ASSIGNMENTS_and_GRADING.md`](course_information/ASSIGNMENTS_and_GRADING.md).
4. **Review the syllabus** —
   [`MSIS-2407-Syllabus.pdf`](5_weeks_outline/MSIS-2407-Syllabus.pdf) — and, if
   DuckDB is new to you, the
   [DuckDB 101 slides](5_weeks_outline/duckdb_introduction/duckdb_101_slides.pdf).

**Getting the course files:** go to
**<https://github.com/mahmoudparsian/MSIS-2407>**, click **Code → Download
ZIP**, and unzip `MSIS-2407-main.zip` — you get a folder called
`MSIS-2407-main`. Or, if you use Git:

```bash
git clone https://github.com/mahmoudparsian/MSIS-2407.git
```

Download again (or `git pull`) each session to pick up newly released labs,
and copy each lab into your own work folder before you start so updates never
overwrite your work.

---

## Weekly Materials

Each week folder holds the lecture material and a demo notebook, plus a
`README.md` describing every file; labs are released separately in
[`LABS/`](LABS/). Notebooks are opened with `marimo edit <notebook>.py`.
The quick links below jump straight to each week's main materials.

### Week 1 — Data Management and Conceptual Modeling

→ [Full week guide](./week1_data_modeling/README.md)

*Data management in organizations · structured, semi-structured, and
unstructured data · entities, attributes, and relationships · ER diagrams,
cardinality, and participation · Enhanced ER (superclass / subclass)*

| Material | Link |
|---|---|
| Lecture notes | [Data modeling — overview](week1_data_modeling/data_modeling_01_high_level.md) · [Data modeling — in depth](week1_data_modeling/data_modeling_02_explained.md) · [Structured, semi-structured, and unstructured data](week1_data_modeling/data_modeling_03_structured_semistructured_unstructured.md) |
| ER notation | [ERD notation guide](week1_data_modeling/ERD_Notation_Guide.md) · [Crow's Foot notation](week1_data_modeling/ERD_Crows_Foot_Notation.md) |
| Notebooks | [`Week1_Notebook_marimo.py`](week1_data_modeling/Week1_Notebook_marimo.py) · [`data_modeling_03_demo_marimo.py`](week1_data_modeling/data_modeling_03_demo_marimo.py) (structured vs. semi-structured vs. unstructured data) |
| Case studies | [1 — Music catalog](week1_data_modeling/data_modeling_case_study_01_music_catalog/) · [2 — Book store](week1_data_modeling/data_modeling_case_study_02_book_store/) · [3 — E-commerce](week1_data_modeling/data_modeling_case_study_03_ecommerce/) — each a written walkthrough plus a DuckDB notebook |
| Reading | Further reading (linked) in [`data_modeling_docs/`](week1_data_modeling/data_modeling_docs/README.md) |

### Week 2 — Relational Design and Normalization

→ [Full week guide](./week2_relational_database_design/README.md)

*Mapping ER to a relational schema · primary keys, foreign keys, and
integrity constraints · functional dependencies and anomalies · 1NF, 2NF,
3NF, BCNF, and 4NF · when to denormalize*

| Material | Link |
|---|---|
| Slides | [`week2_lecture_slides.pdf`](week2_relational_database_design/week2_lecture_slides.pdf) |
| Lecture notes | [Part 1 — Relational design](week2_relational_database_design/lecture_notes_01_Relational_Design.md) · [Part 2 — Normalization](week2_relational_database_design/lecture_notes_02_Normalization.md) |
| Notebook | [`Week2_Notebook_marimo.py`](week2_relational_database_design/Week2_Notebook_marimo.py) |

### Week 3 — Database Implementation

→ [Full week guide](./week3_database_implementation/README.md)

*`CREATE TABLE`, data types, and constraints — in DuckDB, then MySQL · data
loading and validation · indexing and query performance · transactions, ACID,
and concurrency*

| Material | Link |
|---|---|
| Slides | [`week3_lecture_slides.pdf`](week3_database_implementation/week3_lecture_slides.pdf) |
| Lecture notes | [Part 1 — Implementation foundations](week3_database_implementation/lecture_notes_01_Implementation_Foundations.md) · [Part 2 — Data loading](week3_database_implementation/lecture_notes_02_Data_Loading_and_Transition.md) · [Part 3 — Indexing and performance](week3_database_implementation/lecture_notes_03_Indexing_Performance.md) · [Part 4 — Transactions and ACID](week3_database_implementation/lecture_notes_04_Transactions_ACID.md) |
| Notebook | [`Week3_Notebook_marimo.py`](week3_database_implementation/Week3_Notebook_marimo.py) |
| Walkthroughs | Loading a CSV file into a table — [DuckDB](week3_database_implementation/load_csv_to_table_duckdb/) · [MySQL](week3_database_implementation/load_csv_to_table_mysql/README.md) (optional) |

### Week 4 — Analytical and Non-Relational Data Systems

→ [Full week guide](./week4_data_warehousing/README.md)

*OLTP vs. OLAP and data warehouses · star schemas: facts and dimensions ·
grain, surrogate keys, and slowly changing dimensions (Type 2) · relational
vs. object-oriented and document models · data lakes, lakehouses, and the
medallion architecture*

| Material | Link |
|---|---|
| Slides | [`week4_lecture_slides.pdf`](week4_data_warehousing/week4_lecture_slides.pdf) |
| Lecture notes | [Dimensional modeling and OLAP](week4_data_warehousing/lecture_notes_01_Dimensional_Modeling.md) · [Relational vs. object-oriented and document models](week4_data_warehousing/lecture_notes_02_Relational_vs_Object_Oriented.md) |
| Notebook | [`Week4_Notebook_marimo.py`](week4_data_warehousing/Week4_Notebook_marimo.py) |

### Week 5 — Database Administration and Management

→ [Full week guide](./week5_database_management/README.md)

*The DBA role: performance and monitoring · security and access control
(views, PII, SQL injection) · backup, recovery (RPO / RTO), and capacity ·
data quality and governance*

| Material | Link |
|---|---|
| Slides | [`week5_lecture_slides.pdf`](week5_database_management/week5_lecture_slides.pdf) |
| Lecture notes | [Security and access control](week5_database_management/lecture_notes_01_Security_and_Access_Control.md) · [Backup, recovery, capacity, and governance](week5_database_management/lecture_notes_02_Recovery_and_Governance.md) |

The Final Exam (300 points) covers the whole course and is held in a separate
exam slot after Session 10.

---

## Repository Structure

| Folder | Contents |
|---|---|
| [`5_weeks_outline/`](5_weeks_outline/README.md) | The [course syllabus](5_weeks_outline/MSIS-2407-Syllabus.md) ([PDF](5_weeks_outline/MSIS-2407-Syllabus.pdf)) and a [DuckDB introduction](5_weeks_outline/duckdb_introduction/) with slides and install guides |
| [`week1_data_modeling/`](week1_data_modeling/README.md) | Week 1 — Data Management and Conceptual Modeling |
| [`week2_relational_database_design/`](week2_relational_database_design/README.md) | Week 2 — Relational Design and Normalization |
| [`week3_database_implementation/`](week3_database_implementation/README.md) | Week 3 — Database Implementation |
| [`week4_data_warehousing/`](week4_data_warehousing/README.md) | Week 4 — Analytical and Non-Relational Data Systems |
| [`week5_database_management/`](week5_database_management/README.md) | Week 5 — Database Administration and Management |
| [`LABS/`](LABS/README.md) | **This term's labs**, published during each session (one folder per session); solutions are added after the 11:00 pm Pacific Time deadline |
| [`course_information/`](course_information/) | Grading, academic conduct, office hours, and required software — [see below](#course-policies--information) |
| [`software_installation/`](software_installation/) | Step-by-step macOS and Windows setup and verification, with troubleshooting guides |
| [`datasets/`](datasets/) | Reference datasets for self-study — an OLTP retail schema, a star schema, medallion-architecture (bronze / silver / gold) tables, small Week 1 and Week 2 practice tables, and samples |
| [`tools/`](tools/) | Notebook validation scripts |

---

## Course Policies & Information

All in [`course_information/`](course_information/):

| Document | What it covers |
|---|---|
| [`ASSIGNMENTS_and_GRADING.md`](course_information/ASSIGNMENTS_and_GRADING.md) | Grading weights, how each session's lab works, attendance and late policies, Final Exam format |
| [`ACADEMIC_CONDUCT.md`](course_information/ACADEMIC_CONDUCT.md) | Academic integrity expectations |
| [`QUESTIONS_and_OFFICE_HOURS.md`](course_information/QUESTIONS_and_OFFICE_HOURS.md) | How to get help; office hours (days, times, room, Zoom) |
| [`LAPTOP.md`](course_information/LAPTOP.md) | Laptop requirement for in-class labs |
| [`REQUIRED_SOFTWARE.md`](course_information/REQUIRED_SOFTWARE.md) | Every tool used in the course and why |
| [`marimo_duckdb_notebooks.md`](course_information/marimo_duckdb_notebooks.md) | Setting up and running the course's Marimo notebooks |

---

<sub>MSIS-2407 · Santa Clara University · Leavey School of Business</sub>
