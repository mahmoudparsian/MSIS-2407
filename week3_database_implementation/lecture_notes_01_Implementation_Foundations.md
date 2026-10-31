---
marp: true
title: MSIS-2407 — Week 3 (Part 1) — Implementation Foundations
subtitle: From Design to a Real Database
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

# 📊 Week 3 (Part 1) — Implementation Foundations
## From Design → Real Database

---

# 🎯 Learning Objectives

By the end of today you can:

- Explain how a normalized schema becomes a working database
- Create tables with `CREATE TABLE`, choosing appropriate data types
- Define primary keys and foreign keys in SQL
- Explain what each constraint rejects, concretely
- Compare DuckDB and MySQL, and where their SQL syntax differs

---

# 🧠 The Big Transition

**Weeks 1–2:** 👉 Design — ER diagrams, normalized schemas, on paper

**Week 3:** 👉 Build — the same schema, as a running database

The schema doesn't change. What changes is that a database engine now
**enforces** it, instead of you enforcing it by hand.

---

# 💼 The Real-World Question

You have a normalized schema from Week 2:

```
Customer(customer_id, name, email)
Product(product_id, name, price)
Order(order_id, customer_id, order_date)
Order_Items(order_id, product_id, quantity)
```

**How do we turn this into a working database?**

---

# 🔧 The Two Systems We Use

- **DuckDB** — embedded, in-process, zero setup. Runs inside your notebook
  or script; no server to install or manage.
- **MySQL** — client-server, multi-user. A separate server process that
  many applications and users connect to at once.

---

# ⚖️ Why Two Systems?

| | DuckDB | MySQL |
|---|---|---|
| Setup | zero — just a library | install & run a server |
| Optimized for | analytical (OLAP) queries | transactional (OLTP) workloads |
| Concurrency model | single-writer, embedded | many concurrent clients |
| Role in this course | fast prototyping, all labs | the production-system contrast |

Both are real, production-grade engines — the difference is what each is
*optimized* for, not which one is "better."

---

# 🧭 A Caveat Worth Flagging

DuckDB supports transactions too (Part 4 of this week uses it directly) —
"analytical" doesn't mean "no ACID guarantees." The framing above is about
**primary use case**: DuckDB is built for scanning large columns fast;
MySQL is built for many small, concurrent read/write transactions.

---

# 📦 Creating Tables — DuckDB

```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    email       VARCHAR NOT NULL UNIQUE
);
```

Same table, columns, and constraints as Week 1–2 — now it's SQL a database
engine actually runs, not a diagram.

---

# 🔑 Primary Key

```sql
customer_id INTEGER PRIMARY KEY
```

**Meaning:** every `customer_id` value must be unique, and never `NULL`.

**Concretely:** inserting a second row with `customer_id = 1` when one
already exists is **rejected** — the engine raises a constraint violation
and the row never lands in the table.

---

# 🔗 Foreign Key

```sql
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date  DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Meaning:** every `orders.customer_id` value must already exist as some
`customers.customer_id`. This order *belongs to* a real customer — the
engine won't let it belong to a customer that doesn't exist.

---

# 📦 Full Example: Orders Referencing Customers

```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    email       VARCHAR NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  DATE NOT NULL
);
```

`customers` must be created **before** `orders` — the foreign key needs
something to reference.

---

# 🔥 Constraints (Recap from Week 1–2)

| Constraint | Enforces |
|---|---|
| `PRIMARY KEY` | row uniqueness, never null |
| `FOREIGN KEY ... REFERENCES` | the referenced row must exist |
| `UNIQUE` | no duplicate values, even on a non-key column |
| `NOT NULL` | the column can't be left empty |
| `CHECK (...)` | a custom rule (e.g., `price >= 0`) |

Week 1–2 covered these as design concepts. Today they become **rules the
engine enforces on every single insert or update** — automatically.

---

# ⚠️ Why Constraints Matter

Without constraints, nothing stops a row like this from landing in your
table:

```
order_id: 501, customer_id: 9999, order_date: 2026-08-01
```

...even if `customer_id` 9999 doesn't exist anywhere in `customers`. The
row is silently wrong, and every report built on it inherits that error.

---

# 💥 Concrete Example: Rejected Insert

```sql
-- customers currently has customer_id values 1, 2, 3

INSERT INTO orders VALUES (501, 9999, '2026-08-01');
-- ❌ rejected: FOREIGN KEY constraint — 9999 doesn't exist in customers
```

The database refuses the row **at insert time** — this is Week 1's
schema-on-write idea, now enforced by a real engine instead of a diagram.

---

# 🧠 Key Insight

The database enforces correctness **automatically**, on every write, for
every application and every user that connects to it — you don't have to
remember to check.

---

# 📥 Inserting Data

```sql
INSERT INTO customers VALUES (1, 'Alice', 'alice@gmail.com');
INSERT INTO customers VALUES (2, 'Bob', 'bob@gmail.com');
```

---

# 🔍 Querying

```sql
SELECT * FROM customers;
```

| customer_id | name | email |
|---|---|---|
| 1 | Alice | alice@gmail.com |
| 2 | Bob | bob@gmail.com |

---

# 🧭 DuckDB vs. MySQL: Where the Syntax Differs

You'll write nearly-identical SQL in both — these are the differences that
actually trip people up:

---

# 🧭 DuckDB vs. MySQL: Where the Syntax Differs (cont.)

| | DuckDB | MySQL |
|---|---|---|
| `VARCHAR` length | optional, unlimited if omitted | **required**: `VARCHAR(100)` |
| Auto-generated PK | no single keyword — supply values yourself, or use a `SEQUENCE` | one keyword: `AUTO_INCREMENT` |
| Identifier quoting | double quotes `"name"` | backticks `` `name` `` |
| Where it runs | in-process, no server | connect to a running server |

Part 2 puts these differences to work, migrating one schema across both
engines.

---

# 🧪 In-Class Exercise

Write the `CREATE TABLE` statements for:

- `customers` — `customer_id`, `name`, `email`
- `products` — `product_id`, `name`, `price`
- `orders` — `order_id`, `customer_id` (FK), `order_date`

Create them in the order their foreign keys require.

---

# 💬 Discussion

- What happens if you try to insert a `customer_id` that already exists?
- What happens if you try to insert an `orders` row whose `customer_id`
  doesn't exist in `customers`?
- Why does table **creation order** matter here?

---

# 🧠 What Did We Learn?

- Schemas become databases via `CREATE TABLE`
- Primary keys and foreign keys, enforced automatically by the engine
- Constraints reject bad data at insert time — concretely, not just in theory
- DuckDB and MySQL run nearly the same SQL, with a few syntax differences
  that matter once you migrate between them

---

# 🚀 Next: Part 2

- 👉 Data loading — CSV into a real table
- 👉 The DuckDB → MySQL transition, end to end
- 👉 A practical, repeatable workflow

---

# 🙌 End of Part 1
