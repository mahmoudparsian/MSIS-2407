---
title: MSIS-2407 — DBMS - Design, Development & Administration
author: Mahmoud Parsian
marp: true
paginate: true
theme: gaia
class: lead
style: |
  section {
    justify-content: flex-start;
    font-size: 26px;
  }
  h1, h2 {
    color: #2c3e50;
  }
  h2 {
    border-bottom: 3px solid #4ca1af;
    padding-bottom: 5px;
  }
---

# 🎓 MSIS-2407
## DBMS - Design, Development & Administration

* 2 Units · 5 Weeks · Winter 2027 (weeks 6–10)
* Tuesday & Thursday, 7:35–9:10 pm — 10 sessions of 95 minutes
* Instructor: Dr. Mahmoud Parsian

---

# 📜 Catalog Description

[MSIS-2407: Official course catalog description →](https://www.scu.edu/bulletin/graduate/leavey-school-of-business/chapter-7/information-systems-and-business-analytics-isba.html)

This course presents technical and managerial 
approaches to the analysis, design, and management 
of business data, databases, and database management systems. 

The topics include structured and unstructured 
data management, a comparison of relational and 
object-oriented databases, relational database 
conceptual and logical design, and database 
implementation and administration.

---

# 🔗 Relationship to MSIS-2402

In **MSIS-2402** you learned:

- SQL querying  
- Joins and aggregation  
- Analytical SQL  
- DuckDB analytics  

In **MSIS-2407** you will learn:

**How databases are designed, built, and managed.**

---

# 🌍 Course Vision

Transform students from:

### ❌ SQL users  
# ➡️  
### ✅ **Data system designers & decision-makers**

---

# 🎯 Learning Outcomes

Students will be able to:

- Distinguish structured, semi-structured and unstructured data  
- Design conceptual models with ER and Enhanced ER diagrams  
- Convert them into logical relational schemas and normalize (1NF–BCNF, 4NF)  
- Implement databases using SQL, with indexes and transactions  
- Compare relational, object-oriented and document models  
- Design data warehouses and generate business insights from them  
- Secure, back up and govern a database  

---

# 🧠 Learning Progression


## Model 
## → Normalize 
## → Build 
## → Analyze 
## → Manage

---

# 📊 Course Structure

| Week | Theme | Skill |
|------|------|------|
| 1 | Data Management and Conceptual Modeling | Structural thinking |
| 2 | Relational Design and Normalization | Dependency reasoning |
| 3 | Database Implementation | System building |
| 4 | Analytical and Non-Relational Data Systems | Model selection |
| 5 | Database Administration and Management | Decision-making |

**10 class sessions** — two per week.

---

# 🗓 How Each Session Works

- Lecture and live demonstration  
- The session's **lab**, started in the last ~40 minutes of class  
- Submitted on Camino by **11:00 pm Pacific Time** the same day  

Every session has two Marimo labs — **a** (core) and **b** (a step more
challenging) — each with built-in self-checks so you know when a task is right.
Labs are published in the course repository's `LABS/` folder during class.

---

# 🧭 Catalog Alignment

Each topic named in the official course description maps to a week:

| Catalog topic | Week |
|---|---|
| Structured and unstructured data management | 1, 4 |
| Relational database conceptual and logical design | 1–2 |
| Database implementation and administration | 3, 5 |
| Comparison of relational and object-oriented databases | 4 |

Week 4 also covers data warehousing for analytical workloads — not named in the
catalog, but central to MSIS/MSBA work.

---

# 📘 Week 1 — Data Management and Conceptual Modeling

- Data management in organizations  
- Structured, semi-structured & unstructured data (basics in Session 1; more in Week 4)  
- Conceptual modeling: entities, attributes, relationships  
- ER diagrams; cardinality and participation  
- Enhanced ER (EER): superclass / subclass  

🧪 Labs — Session 1: entities, keys, a first table split · Session 2: business rules → ER, then Enhanced ER

---

# 📘 Week 2 — Relational Design and Normalization

- Mapping ER → relational schema  
- Primary keys, foreign keys, integrity constraints  
- Functional dependencies and data anomalies  
- 1NF, 2NF, 3NF, BCNF (and 4NF); when to denormalize  

🧪 Labs — Session 3: 1NF → 3NF, then BCNF · Session 4: keys and constraints, then 4NF

---

# 📘 Week 3 — Database Implementation

- CREATE TABLE, data types, PK / FK constraints — in DuckDB, then MySQL  
- Data loading and validation  
- Indexing and query performance  
- Transactions, ACID and concurrency  

🧪 Labs — Session 5: typed DDL and loading messy data · Session 6: transactions and concurrency

---

# 📘 Week 4 — Analytical and Non-Relational Data Systems

- OLTP vs OLAP; data warehouses  
- Star schema: fact and dimension tables  
- Grain, surrogate keys, SCD Type 2  
- Relational vs object-oriented and document models (STRUCT, LIST, JSON)  
- Semi-structured data in depth: schema drift, shredding JSON into tables  
- Data lakes, lakehouse, medallion architecture  

🧪 Labs — Session 7: OLTP → star schema, SCD Type 2 · Session 8: querying a warehouse; relational vs document models

---

# 📘 Week 5 — Database Administration and Management

- The DBA role: performance and monitoring  
- Security and access control (views, PII, SQL injection)  
- Backup, recovery (RPO / RTO) and capacity  
- Data quality and governance  

🧪 Labs — Session 9: security, access, masking, indexes, auditing · Session 10: backup, recovery, data quality

---

# 📦 Assessments

| Component | Points |
|----------|--------:|
| 🧪 10 Labs — one per class session, 70 points each | 700 |
| ✏️ Final Exam — 2 hours, separate exam slot after Session 10 | 300 |
| **Total** | **1000** |

Each lab is started in class and submitted on Camino by 11:00 pm Pacific Time the same day.
Details: `course_information/ASSIGNMENTS_and_GRADING.md`

---

# 🧪 Tools & Technologies

- SQL  
- **DuckDB** — primary engine for all labs and notebooks  
- **MySQL** — transactional-systems contrast (Week 3)  
- **Marimo** — reactive Python notebooks for the labs  
- ER modeling tools (draw.io, Lucidchart)  

---

# 💼 Teaching Philosophy

- Learn by doing  
- Emphasize real-world problems  
- Focus on business impact  

---

# 🧠 Cognitive Levels (Bloom’s Taxonomy)

| Level | Application |
|------|------------|
| Understand | Data types and data modeling |
| Apply | SQL implementation |
| Analyze | Normalization and dependency reasoning |
| Evaluate | Data-model and performance trade-offs |
| Create | Schemas, star schemas, and role views built in the labs |

---

# 🎯 Final Outcome

After completing this course you will be able to:

- Design scalable databases  
- Implement and administer working systems  
- Build analytical data models and deliver actionable insights  
- Understand how enterprise data platforms operate  

---

# 🚀 Career Relevance

Prepares students for roles:

- Data Analyst  
- Data Engineer (entry-level)  
- Business Intelligence Analyst  

---

# 📂 Where to Find Things

All in the course repository:

| Folder | What's there |
|---|---|
| `software_installation/` | Setup guide — do Steps 0–3 **before the first class** |
| `course_information/` | Grading, office hours, laptop rule, required software |
| `week1_…` – `week5_…` | Lecture notes, slides, and demo notebooks |
| `LABS/` | Each session's labs, published during class |

---

# 🙌 End of Syllabus
