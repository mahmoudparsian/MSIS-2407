---
marp: true
title: MSIS-2407 — Week 3 (Part 2) — Data Loading and Transition
subtitle: CSV to DuckDB to MySQL
paginate: true
style: |
  section {
    justify-content: flex-start;
    font-size: 26px;
  }
  h2 {
    background: linear-gradient(90deg, #2c3e50, #4ca1af);
    color: white;
    padding: 10px 18px;
    border-radius: 6px;
    width: fit-content;
  }
---

# 📊 Week 3 (Part 2) — Data Loading & Transition
## From Raw CSV → Working System

This is where you stop designing and start operating a database — the
step where students feel like engineers, not just designers.

---

# 🎯 Learning Objectives

By the end of today you can:

- Define ETL and map it onto a real loading workflow
- Load a CSV into DuckDB, inspect it, and clean it
- Migrate a schema and its data from DuckDB to MySQL
- Explain what changes — and what doesn't — when you switch engines
- Validate that a load succeeded, instead of assuming it did

---

# 🧠 Big Idea

**A database without data is useless.** Every table you created in Part 1
is empty until something loads real rows into it — and loading is where
most real-world data problems actually surface.

---

# 🔑 What Is ETL?

- **Extract** — pull data out of its source (a CSV, an API, another
  database)
- **Transform** — clean it, fix types, remove duplicates, reshape it to
  match your schema
- **Load** — write the transformed data into the destination tables

Today's whole workflow is an ETL pipeline: Extract from CSV → Transform in
DuckDB → Load into MySQL.

---

# 🔁 Workflow Overview

1. Extract — read the raw source
2. Transform — clean and reshape
3. Load — create tables, insert data
4. Validate — confirm the result is correct

Same four steps, every time, regardless of source or destination.

---

# 📥 Step 1 — Extract: The Data Source

Our source: `Week3_dataset.csv`

```
order_id,customer_name,customer_email,product_name,price,quantity,order_date
1,Alice,alice@gmail.com,Laptop,1200,2,2025-01-01
1,Alice,alice@gmail.com,Mouse,25,1,2025-01-01
2,Bob,bob@gmail.com,Phone,800,1,2025-01-02
```

One flat file — the same shape of "messy" data Week 2 taught you to
normalize. Extraction just gets it into a queryable place first.

---

# 🔥 Extracting With DuckDB

```sql
CREATE TABLE raw_orders AS
SELECT * FROM read_csv_auto('Week3_dataset.csv');
```

`read_csv_auto` detects the delimiter, header row, and column types for
you — a single statement takes a CSV from disk to a queryable table.

---

# 🧠 Why DuckDB First?

- zero setup — no server, no configuration
- fast — reads and queries millions of rows in seconds
- perfect for prototyping the transform step before you touch production

---

# 📊 Inspect the Data

```sql
SELECT * FROM raw_orders LIMIT 10;
```

Always look at what actually loaded — column types DuckDB *guessed* aren't
always the types you *want* (a `price` column full of whole numbers might
be inferred as `BIGINT`, not the `DECIMAL` you need for currency).

---

# ⚠️ Data Quality Check

Look for:

- missing values (`NULL` where a value is required)
- wrong types (a `price` column that's actually text, e.g. `"N/A"`)
- duplicates (the same order line loaded twice)

A messy real-world row might look like: `4,"",dave@x.com,Charger,N/A,1,`
— missing name, non-numeric price, missing date. Extraction alone doesn't
catch this; transformation does.

---

# 🔧 Step 2 — Transform: Clean and Cast

```sql
SELECT
    order_id,
    CAST(price AS INTEGER)    AS price,
    CAST(quantity AS INTEGER) AS quantity
FROM raw_orders;
```

`CAST` converts a column to the type you actually need — here, ensuring
`price` and `quantity` are numeric before they reach a business rule.

---

# ⚠️ A DuckDB Gotcha: `/` Is Float Division

```sql
-- average items per order across 5 orders totaling 9 items
SELECT CAST(9 / 5 AS INTEGER) AS avg_items;   -- returns 2 (rounds!)
SELECT CAST(floor(9.0 / 5) AS INTEGER) AS avg_items;  -- returns 1 (truncates)
```

`/` always does float division in DuckDB, so casting the *result* to
`INTEGER` **rounds** rather than truncates. If you want the traditional
"integer division" behavior, use `floor()` before the cast — this exact
trap has silently broken real fiscal-quarter calculations.

---

# 🧬 Duplicate Business Keys and Survivorship

Exact duplicates are easy — `SELECT DISTINCT` removes them. The hard case is
the **same business key with different values**: the source sends supplier
`S-01` twice, once as *Acme Parts* and once, two days later, as *Acme Parts
Inc.* `DISTINCT` keeps both (they differ), and a primary key on
`supplier_code` rejects the load.

You need a **survivorship rule** — a written, ordered rule for which row wins.
For example:

1. the most recent `updated_at` wins;
2. on a tie, prefer the row with a known `city`;
3. on a further tie, take the alphabetically first `supplier_name`.

The last step matters: without a final tie-break, two runs over the same data
can pick different rows. A rule must be **deterministic**.

---

# 🧬 Survivorship in SQL

Encode the rule as the `ORDER BY` of a `ROW_NUMBER()` window and keep row 1
of each key:

```sql
SELECT supplier_code, supplier_name, city, updated_at
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY supplier_code
               ORDER BY updated_at DESC,   -- 1. newest wins
                        (city IS NULL),    -- 2. FALSE sorts first: known city wins
                        supplier_name      -- 3. fixed tie-break
           ) AS rn
    FROM stg_supplier
) AS ranked
WHERE rn = 1;
```

Run it before the upsert, and check: the survivor table has exactly one row
per business key (`COUNT(*) = COUNT(DISTINCT supplier_code)`).

---

# 💼 Business Thinking

**Clean data = reliable decisions.** A report built on uncast, unvalidated
data isn't wrong loudly — it's wrong quietly, and nobody notices until a
decision made from it turns out to be bad.

---

# 🚀 Moving to MySQL

---

# 🧠 Why MySQL?

- widely used in industry — the odds you'll work with it are high
- supports many concurrent users, safely
- closer to how production transactional systems actually run

---

# 🔧 Step 3 — Create Tables in MySQL

```sql
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE
);
```

Same schema as Part 1's DuckDB version — but `VARCHAR` now needs an
explicit length, and `AUTO_INCREMENT` replaces DuckDB's implicit key
generation (Part 1's syntax-difference table, applied). `products`,
`orders`, and `order_items` follow the identical pattern — shown once here
to avoid repeating four nearly-identical `CREATE TABLE` blocks.

---

# 📥 Step 4 — Insert Data

```sql
INSERT INTO customers (name, email)
VALUES ('Alice', 'alice@gmail.com');
```

`customer_id` is omitted — `AUTO_INCREMENT` assigns it.

---

# ⚠️ DuckDB vs. MySQL, In Practice

| | DuckDB | MySQL |
|---|---|---|
| Type checking | flexible, permissive on ingest | strict — a bad value is rejected |
| Ingestion style | bulk, columnar, very fast | row-oriented; bulk needs `LOAD DATA` |
| Typical role here | analytical prototyping | transactional production |

---

# 🔥 Step 5 — Load Bulk Data Into MySQL

```sql
LOAD DATA LOCAL INFILE 'Week3_dataset.csv'
INTO TABLE raw_orders
FIELDS TERMINATED BY ','
IGNORE 1 ROWS;
```

**`LOCAL`** matters: it reads the file from the **client's** filesystem.
Without it, MySQL reads from the **server's** filesystem instead — and
usually fails, because your CSV isn't sitting on the database server.

---

# ⚠️ Common Issue: Permissions and Paths

`LOAD DATA LOCAL INFILE` requires the `local_infile` setting enabled on
**both** the client and the server — many MySQL installs disable it by
default for security. Server-side `LOAD DATA INFILE` (no `LOCAL`) is also
restricted to specific directories via `secure_file_priv`.

👉 In real systems, this is exactly the kind of setup detail that blocks a
pipeline on day one — know it exists before you hit it.

---

# 🔍 Step 6 — Validate the Load

```sql
SELECT COUNT(*) FROM orders;
```

Better: reconstruct the original data with a join, and compare row counts
to the source — Session 5's labs ask for exactly this.

```sql
SELECT c.name AS customer_name, p.name AS product_name, oi.quantity
FROM order_items oi
JOIN orders o    ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p  ON oi.product_id = p.product_id;
```

Alias both `name` columns — `customers.name` and `products.name` are both
literally `name`, and leaving either unaliased risks a duplicate-column
error (exactly the bug this course's own Week 3 notebook had to fix).

---

# 🧠 Key Insight

**Always verify data after loading.** A load that runs without an error is
not the same thing as a load that loaded the right data — row counts and
reconstruction joins catch what silent type coercion hides.

---

# 🔁 The Full Pipeline

```
Extract (CSV → DuckDB) → Transform (clean, cast) → Load (MySQL) → Validate (join, count)
```

Same four ETL steps from the start of this deck — now with a concrete tool
at every stage.

---

# 💼 Real-World Workflow

- **Data engineers** build and run the pipeline (extract, transform, load)
- **Analysts** query the loaded, trusted data
- **Managers** make decisions from what analysts report

Every layer depends on the one before it being correct.

---

# 🧪 In-Class Exercise

1. Load `Week3_dataset.csv` into DuckDB with `read_csv_auto`
2. Inspect it — check types and row count
3. Create the normalized schema in MySQL
4. Insert (or bulk-load) the transformed data
5. Validate with a `COUNT(*)` and a reconstruction join

---

# 💬 Discussion

- Why not load the raw CSV directly into MySQL and skip DuckDB entirely?
- What role does DuckDB play that MySQL doesn't, in this pipeline?

---

# 🧠 Expected Answer

👉 **DuckDB** = fast, disposable experimentation — cheap to get wrong and
redo.

👉 **MySQL** = the controlled, production system — where you land data only
once you trust it.

---

# ⚠️ Common Mistakes

- inserting before casting types (letting bad data reach the real schema)
- forgetting `LOCAL` in `LOAD DATA LOCAL INFILE`
- skipping validation and assuming the load "just worked"
- loading directly into normalized tables instead of staging first

---

# 🧠 What Did We Learn?

- ETL, defined: Extract, Transform, Load
- DuckDB for fast extraction and transformation
- MySQL for the production, multi-user destination
- `LOAD DATA LOCAL INFILE` and why `LOCAL` matters
- Validating a load with counts and reconstruction joins, not assumptions

---

# 🎯 Most Important Idea

**The pipeline matters as much as the schema.** A perfect schema fed by an
unverified load is still an unreliable database.

---

# 🚀 Next Week

- 👉 Performance and indexing
- 👉 Transactions and ACID
- 👉 How a database behaves under real-world load

---

# 🙌 End of Part 2
