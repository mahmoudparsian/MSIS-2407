---
marp: true
title: DuckDB 101
paginate: true
---

### Slide 1 — DuckDB 101

**MSIS-2407 — DBMS - Design, Development & Administration**

DuckDB Basics — the database engine for this course

Topics:

- What is DuckDB
- Installation
- Reading CSV files
- Creating tables
- Running SQL queries
- DuckDB + Pandas
- Multiple CSV files
- DuckDB vs Spark / BigQuery

---

### Slide 2 — What is DuckDB?

DuckDB is an **in-process analytical database**.

Key idea:

It runs **inside your application** (Python, R, a Marimo notebook).

Characteristics:

- columnar database
- optimized for analytics
- no server required
- extremely fast for large datasets

Think of DuckDB as:

**SQLite for analytics**

---

### Slide 3 — Why Use DuckDB in This Course?

Advantages for students:

- No database server setup
- Works directly with CSV files
- Fast analytics queries
- Runs inside **Marimo notebooks** — every lab in this course
- Supports full SQL: keys, constraints, transactions, views

Typical workflow:

CSV → DuckDB → SQL → results as a table

---

### Slide 4 — DuckDB vs Traditional Databases

| Feature | DuckDB | MySQL / PostgreSQL |
|---|---|---|
| Server required | ❌ No | ✔ Yes |
| Installation complexity | Very easy | Medium |
| Analytics performance | Excellent | Good |
| Runs inside Python | ✔ Yes | Limited |

DuckDB is designed for:

**analytics, data science, and exploration**

---

### Slide 5 — Installing DuckDB

Install using pip:

```bash
python3 -m pip install "duckdb>=2.0"
```

Verify installation:

```python
import duckdb
print(duckdb.__version__)   # 2.x.x
```

Works on Mac, Windows, and Linux.

Full step-by-step setup: the course's **`software_installation/`** guide.

---

### Slide 6 — Using DuckDB in Python

Example:

```python
import duckdb

con = duckdb.connect()

con.execute("SELECT 1+1").fetchall()
```

Output:

```
[(2,)]
```

DuckDB executes **standard SQL queries**.

---

### Slide 7 — Reading a CSV File

DuckDB can read CSV files directly.

```sql
SELECT *
FROM read_csv_auto('orders.csv')
LIMIT 5;
```

DuckDB automatically:

- detects column names
- detects data types

---

### Slide 8 — Creating a Table from CSV

Convert CSV → table:

```sql
CREATE OR REPLACE TABLE orders AS
SELECT *
FROM read_csv_auto('orders.csv');
```

Now the table **orders** exists in DuckDB.

`CREATE OR REPLACE` lets you re-run the cell without an error.

---

### Slide 9 — Query Example

```sql
SELECT customer_id,
       COUNT(order_id) AS num_orders
FROM orders
GROUP BY customer_id
ORDER BY num_orders DESC
LIMIT 10;
```

Business question:

Which customers placed the most orders?

---

### Slide 10 — DuckDB + Pandas

Using the same connection `con` that created `orders`:

```python
df = con.execute("""
    SELECT *
    FROM orders
    LIMIT 10
""").df()

df
```

DuckDB returns a **Pandas DataFrame** — Marimo shows it as a table.

---

### Slide 11 — Query a CSV Without Loading It

```python
df = con.execute("""
    SELECT category, COUNT(*) AS num_sales
    FROM read_csv_auto('sales.csv')
    GROUP BY category
    ORDER BY num_sales DESC
""").df()
```

No `CREATE TABLE` needed — DuckDB reads the file on the fly.

Workflow:

CSV → SQL → DataFrame

---

### Slide 12 — Reading Multiple CSV Files

```sql
SELECT *
FROM read_csv_auto('data/orders_*.csv');
```

DuckDB automatically loads all matching files.

Useful for:

- partitioned datasets
- large data collections

---

### Slide 13 — DuckDB vs Spark vs BigQuery

| System | Best Use Case |
|---|---|
| DuckDB | Local analytics |
| Spark | Distributed big data |
| BigQuery | Cloud warehouse analytics |

Rule of thumb:

```
DuckDB   → laptop
Spark    → cluster
BigQuery → cloud
```

---

### Slide 14 — DuckDB in 30 Seconds

Complete workflow example:

```python
import duckdb

con = duckdb.connect()

df = con.execute("""
    SELECT category, SUM(sales_amount) AS revenue
    FROM read_csv_auto('sales.csv')
    GROUP BY category
    ORDER BY revenue DESC
""").df()

df
```

Pipeline:

CSV → DuckDB → SQL → Pandas DataFrame

---

### Slide 15 — Summary

DuckDB is:

- lightweight
- fast
- easy to install
- ideal for analytics — and for learning database design

Typical workflow:

CSV → DuckDB → SQL → DataFrame

---

### Slide 16 — DuckDB in MSIS-2407

We will use DuckDB throughout this course to:

- build schemas with keys and constraints
- load and validate data
- run transactions and see concurrency at work
- build and query star schemas
- practice security, backup, and data quality

Every lab is a Marimo notebook running on DuckDB.
