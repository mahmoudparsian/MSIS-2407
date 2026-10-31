---
marp: true
title: MSIS-2407 — Week 5 Database Administration and Management
paginate: true
---

# Slide 1 — Week 5

Database Administration and Management

Topics:

• The DBA role and performance
• Security and access control (Session 9)
• Backup, recovery and capacity (Session 10)
• Data quality, governance and monitoring (Session 10)

---

# Slide 2 — Role of a Database Administrator

Database Administrators (DBAs) manage:

• database performance
• backups and recovery
• security and access control
• database monitoring

---

# Slide 3 — Database Administration Tasks

Common DBA responsibilities:

• install database systems
• configure servers
• manage user permissions
• monitor performance

---

# Slide 4 — Database Performance

Performance tuning involves:

• indexing
• query optimization
• hardware configuration

---

# Slide 5 — Query Optimization

A frequent lookup:

```sql
SELECT *
FROM orders
WHERE customer_id = 10;
```

A candidate index:

```sql
CREATE INDEX idx_customer
ON orders(customer_id);
```

Measure before and after — in a columnar engine like DuckDB the index may
not help at all, and every index slows writes.

---

# Slide 6 — Database Security

Security protects sensitive data.

Three questions: who may see what, how is sensitive data protected,
and how could an attacker get around it?

Common threats:

• unauthorized access
• data leaks
• malicious queries (SQL injection)

---

# Slide 7 — Access Control

Example:

```sql
CREATE USER 'analyst'@'localhost'
IDENTIFIED BY 'password';
```

---

# Slide 8 — Granting Permissions

```sql
GRANT SELECT
ON ecommerce.*
TO 'analyst'@'localhost';
```

---

# Slide 9 — Revoking Permissions

```sql
REVOKE INSERT
ON ecommerce.*
FROM 'analyst'@'localhost';
```

---

# Slide 10 — Access Control in DuckDB: Views

DuckDB is embedded: no user accounts, no GRANT or REVOKE.

Use a **view** as the boundary — expose only some columns and rows:

```sql
CREATE VIEW v_customer_marketing AS
SELECT customer_id, postal_code, segment   -- no name, no email
FROM customer;
```

⚠️ A view protects data only if the base table is **not** also readable.

---

# Slide 11 — Protecting PII

| Treatment | What it does | Joinable? |
|---|---|---|
| Redaction | remove the value | no |
| Tokenization | replace with a stable salted hash | yes |
| Generalization | reduce precision (age → band) | partly |

Removing the name is **not** anonymization — a few quasi-identifiers
(postal code, birth date, gender) can re-identify a person.

---

# Slide 12 — SQL Injection

```python
# vulnerable
f"SELECT * FROM booking WHERE name = '{user_input}'"

# safe — bind the parameter
"SELECT * FROM booking WHERE name = ?", [user_input]
```

Escaping quotes is not a defence. **Bind every parameter.**

---

# Slide 13 — Backup and Recovery

Backup types:

• full — everything
• incremental — changes since the last backup
• differential — changes since the last full backup
• log shipping — every committed transaction (point-in-time recovery)

---

# Slide 14 — RPO and RTO

**RPO** — recovery point objective: how much data may we lose?
→ sets backup **frequency**

**RTO** — recovery time objective: how long may we be down?
→ sets backup **method**

Nightly backups mean losing up to 24 hours of data.
That is a business decision, not just a DBA decision.

---

# Slide 15 — MySQL Backup Example

```bash
mysqldump -u root -p ecommerce > backup.sql
```

This creates a full database backup.

---

# Slide 16 — Restoring a Database

```bash
mysql -u root -p ecommerce < backup.sql
```

This restores the database from backup.

---

# Slide 17 — Backup and Restore in DuckDB

```sql
EXPORT DATABASE 'backup_2026_04_01' (FORMAT PARQUET);
-- ... disaster ...
IMPORT DATABASE 'backup_2026_04_01';
```

The backup is a readable folder: schema.sql, load.sql, one Parquet file per table.

---

# Slide 18 — Test the Restore

A backup you have never restored is a hypothesis.

1. take the backup
2. compute a checksum of the source
3. restore into a clean database
4. re-compute the checksum and compare

Matching row counts is not enough — you can restore the right number of wrong rows.

---

# Slide 19 — Capacity Planning

Measure **bytes**, not rows.

• CSV → Parquet: the value of columnar layout
• uncompressed → zstd: the value of compression

Plan with bytes per row × projected rows, and project the growth rate.

---

# Slide 20 — Data Quality

Six dimensions, each a rule that returns a count:

| Dimension | Question |
|---|---|
| Completeness | is the value present? |
| Validity | does it match its format? |
| Uniqueness | one row per real-world thing? |
| Accuracy | is the value possible? |
| Timeliness | is it fresh enough? |
| Consistency | do related facts agree? |

---

# Slide 21 — Data Governance

Organizations must manage:

• data quality
• privacy
• compliance

Store governance as tables, so questions become queries:

• **catalog** — every column, with owner, classification, PII flag
• **lineage** — which object feeds which

---

<style scoped>section { font-size: 24px; } pre { font-size: 19px; }</style>

# Slide 22 — Lineage: What Breaks Downstream?

Lineage stored as edges → impact is a **recursive CTE** (the Week 1 pattern):

```sql
WITH RECURSIVE impact AS (
    SELECT target_object AS obj, 1 AS hops
    FROM lineage WHERE source_object = 'raw_customers'
    UNION ALL
    SELECT l.target_object, i.hops + 1
    FROM lineage AS l JOIN impact AS i ON l.source_object = i.obj
)
SELECT obj, MIN(hops) AS hops FROM impact GROUP BY obj ORDER BY hops;
```

`dim_customer` (1) → `fct_sales` (2) → `rpt_weekly_revenue` (3) → `dash_ceo` (4)

• `MIN(hops)`: an object can be reached by more than one route
• Lineage can contain loops by mistake — stop on revisit

---

# Slide 23 — Master Data: Block, Match, Survive

One real supplier, many records → one **golden record**

1. **Block** — compare only records sharing a cheap key (n² is too many)
2. **Match** — `jaro_winkler_similarity()` above a **threshold**; chain A≈B≈C
3. **Survive** — a deterministic survivorship rule picks the winner

| a | b | similarity |
|---|---|---:|
| Northgate Metals | Northgate Metal | 0.987 |
| Northgate Metals | Northwind Metals | **0.867** ← different companies! |

The threshold trades **wrong merges** against **missed duplicates** — test both.

---

# Slide 24 — Monitoring and the Runbook

A runbook names:

• the metrics and their thresholds
• who is alerted, and when
• the first steps on an alert
• the RPO / RTO you have committed to

Compare metrics against a baseline window, not just yesterday.

---

# Slide 25 — Modern Data Platforms

Organizations run several kinds of database:

• **relational** — MySQL, PostgreSQL, SQL Server: structured data and transactions
• **NoSQL** — MongoDB, Cassandra, DynamoDB: large-scale distributed data
• **cloud** — Amazon RDS, Google BigQuery, Snowflake: managed and scalable

The same administration questions apply to all of them.

---

# Slide 26 — Enterprise Data Architecture

Typical architecture:

Applications
↓
Operational database (OLTP)
↓
Data warehouse
↓
Analytics / dashboards

---

# Slide 27 — Course Summary

During this course you learned:

• data management and conceptual modeling (ER / EER)
• relational design and normalization
• database implementation: DDL, loading, indexes, transactions
• analytical and non-relational data systems
• database administration and management

---

# Slide 28 — What Comes Next: the Final Exam

One exam covering the whole course, in a separately scheduled slot after
Session 10.

You will be asked to:

• model a business scenario (ER → relational schema)
• normalize from functional dependencies
• write DDL with the right keys and constraints
• design and query a star schema
• reason about transactions, security, and recovery

Format and rules: see `course_information/ASSIGNMENTS_and_GRADING.md`.
