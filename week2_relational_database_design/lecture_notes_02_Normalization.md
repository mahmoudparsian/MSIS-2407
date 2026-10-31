---
marp: true
title: MSIS-2407 — Week 2 (Part 2) — Normalization
subtitle: From Messy Data to Clean Design
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

# 📊 Week 2 (Part 2) — Normalization
## From Messy Data → Clean Design

---

# 🎯 Learning Objectives

By the end of today you can:

- Define a functional dependency and write one in `X → Y` notation
- Apply 1NF, 2NF, and 3NF to a messy table
- Explain BCNF, and when it differs from 3NF
- Recognize a 4NF (multivalued dependency) problem by sight
- Avoid both over-normalizing and under-normalizing a schema

---

# 🧠 Why Normalization?

We normalize to:

- eliminate redundancy
- prevent anomalies (Part 1)
- ensure data integrity

Part 1 diagnosed the disease (anomalies). Normalization is the treatment —
a repeatable procedure, not a matter of taste.

---

# 🔑 Functional Dependencies, Formally

**Definition.** `X → Y` ("X determines Y") means: for any two rows that
agree on `X`, they must also agree on `Y`. Knowing `X` is enough to know `Y`.

From the Week 2 dataset:

- `order_id → order_date` — one order has exactly one date
- `product_name → price, category` — a product's price and category depend
  only on which product it is
- `customer_name → customer_email` — a customer's email depends only on
  which customer they are

A functional dependency is a **business rule**, not a coincidence you spot in
a handful of sample rows — three rows happening to agree proves nothing on
their own.

---

# 🔑 Superkeys and Prime Attributes

Two terms the rest of this deck relies on:

- **Superkey** — any set of columns that uniquely identifies a row. It may
  contain more columns than necessary.
- **Candidate key** (Week 1) — a *minimal* superkey: remove any column and
  it stops being unique.
- **Prime attribute** — a column that belongs to **at least one** candidate
  key.
- **Non-prime attribute** — a column that belongs to **no** candidate key.

Every candidate key is a superkey; not every superkey is a candidate key
(a superkey can carry extra, redundant columns).

---

# 💥 Starting Point (Bad Table)

```
order_id | customer_name | customer_email | product_name | category | price | quantity | order_date
```

Sample rows (Week 2 dataset):

| order_id | customer_name | customer_email | product_name | category | price |
|---|---|---|---|---|---|
| 1 | Alice | alice@gmail.com | Laptop | Electronics | 1200 |
| 1 | Alice | alice@gmail.com | Mouse | Electronics | 25 |
| 3 | Charlie | charlie@gmail.com | Tablet | Electronics | 300 |

---

# ⚠️ Problems

- customer repeated (`customer_name`, `customer_email`)
- product repeated (`product_name`, `category`, `price`)
- 👉 inconsistent-data risk, exactly as diagnosed in Part 1

We'll fix this same table, step by step, across the next three normal forms.

---

# 🔥 Step 1 — First Normal Form (1NF)

**Definition (simplified):**

- every column holds **atomic** values (no lists)
- no repeating groups

---

# ❌ Not 1NF — A Concrete Example

```
order_id | products
1        | Laptop, Mouse
```

One cell holding two products. You cannot ask "what is *the* price for this
row's product" — there are two products, with two different prices, jammed
into one field.

---

# ✅ 1NF Fix

Split the multi-valued cell into one row per fact:

| order_id | product_name |
|---|---|
| 1 | Laptop |
| 1 | Mouse |

👉 **Each row now represents exactly one fact.** This is exactly the shape
the real Week 2 dataset already ships in — order 1 is two rows, not one.

---

# 🔥 Step 2 — Second Normal Form (2NF)

**Definition (simplified):**

- must already be in 1NF
- remove **partial dependency**

**Partial dependency:** a column depends on only *part* of a composite
primary key, not the whole thing.

---

# 💥 2NF — The Problem, With Real Columns

Composite key: `(order_id, product_name)` — that's what identifies one line
item.

But:

- `price` depends only on `product_name`
- `category` depends only on `product_name`

Neither depends on `order_id` at all — that's a **partial** dependency, and
it's exactly why `price`/`category` are duplicated on every order that
contains the same product.

---

# ✅ 2NF Fix

Split into a table for the part of the key that owns the dependency, and a
table for the association itself. From here on, each fix is shown two ways:
singular `Table(columns...)` notation for reasoning about dependencies
(the convention this deck uses), and the equivalent
runnable SQL, in plural `snake_case`, matching Part 1 and the course's real
`datasets/oltp_database`:

---

# ✅ 2NF Fix (cont.)

```
Product(product_name, category, price)
Order_Items(order_id, product_name, quantity)
```

```sql
CREATE TABLE products (
    product_name VARCHAR PRIMARY KEY,
    category     VARCHAR NOT NULL,
    price        NUMERIC(10,2) NOT NULL CHECK (price >= 0)
);

CREATE TABLE order_items (
    order_id     INTEGER NOT NULL,
    product_name VARCHAR NOT NULL REFERENCES products(product_name),
    quantity     INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_name)
);
```

---

# 🧠 A Week 1 Callback: Is `product_name` a Good Key?

Using `product_name` as `products`' primary key works for this exercise, but
it's a **natural key** (Week 1) — risky if two different products could ever
share a name, or a product gets renamed.

A real system would give `Product` a **surrogate key**, `product_id`, and
keep `product_name` as a `UNIQUE` candidate key instead. Once you see a
partial dependency, ask both questions: *what table does this belong in?*
**and** *is the key I'm using actually stable?*

---

# 🧠 Key Insight

Every column must depend on the **whole** key — not just part of it. That's
the entire content of 2NF, stated one way.

---

# 🔥 Step 3 — Third Normal Form (3NF)

**Definition (simplified):**

- must already be in 2NF
- remove **transitive dependency**

**Transitive dependency:** a non-key column depends on *another non-key
column*, rather than depending directly on the key.

---

# 💥 3NF — The Problem, With Real Columns

```
order_id → customer_name → customer_email
```

`customer_email` depends on `customer_name`, and `customer_name` depends on
`order_id` — but `customer_email` does **not** depend on `order_id`
directly. It only rides along because `customer_name` does.

**Problem:** email is stored once per *order*, when it should be stored once
per *customer*.

---

# ✅ 3NF Fix

```
Customer(customer_name, customer_email)
Order(order_id, customer_name, order_date)
```

```sql
CREATE TABLE customers (
    customer_name  VARCHAR PRIMARY KEY,
    customer_email VARCHAR NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_name VARCHAR NOT NULL REFERENCES customers(customer_name),
    order_date    DATE NOT NULL
);
```

Same natural-vs-surrogate-key caution as the last slide applies here too —
the final schema, later in this deck, upgrades this to `customer_id`.

---

# 🧠 Key Insight

Non-key attributes must depend **only** on the key — the whole key, and
nothing but the key.

---

# 🧪 Full Worked Example: 1NF → 3NF, End to End

Starting from the flat table (Alice/Laptop/Mouse rows), applying all three
steps in order:

1. **1NF:** already atomic — one product per row (the CSV ships this way)
2. **2NF:** split out `Product(product_name, category, price)` — removes the
   partial dependency on `product_name` alone
3. **3NF:** split out `Customer(customer_name, customer_email)` — removes
   the transitive dependency through `customer_name`

**Result:** four tables, each with one subject — Customer, Product, Order,
Order_Items. Exactly the fix Part 1 called for after diagnosing the
anomalies.

---

# 🔥 Step 4 — Boyce–Codd Normal Form (BCNF)

3NF is not the end of the story. A table can satisfy 3NF and still contain
redundancy.

---

# 🧠 The BCNF Rule

For **every** non-trivial dependency `X → Y`:

👉 `X` must be a **superkey**

3NF allows one exception (a determinant that isn't a superkey, as long as
every attribute it determines is prime). BCNF removes that exception.

---

# ❌ 3NF but NOT BCNF

```
Advising(student_id, subject, instructor)
```

Business rules:

- a student has exactly one instructor per subject
- each instructor teaches exactly **one** subject

---

# 🔍 Why It Passes 3NF

Candidate keys:

- `(student_id, subject)`
- `(student_id, instructor)`

Every attribute is part of *some* candidate key, so **every attribute is
prime**. That means there is no non-prime attribute for 3NF's rule to apply
to, so 3NF is satisfied — vacuously, but satisfied.

*(Note: these "so"s describe logical reasoning, not functional dependencies
— don't confuse this chain with `X → Y` notation from two slides ago.)*

---

# 🔥 But Look at This Dependency

```
instructor → subject
```

`instructor` alone determines `subject` (Rule: "each instructor teaches
exactly one subject") — but `instructor` by itself is **not** a superkey
(it doesn't determine `student_id`).

👉 **BCNF violated.**

---

# ⚠️ The Redundancy It Leaves

| student_id | subject | instructor |
|---|---|---|
| S1 | Databases | Dr. Chen |
| S2 | Databases | Dr. Chen |
| S3 | AI | Dr. Patel |

"Dr. Chen teaches Databases" is repeated once per student she advises.
Change her subject to "Networks," and you must update **every** row that
mentions her — miss one, and the table contradicts itself.

---

# ✅ BCNF Fix

```
Instructor(instructor, subject)
Student_Instructor(student_id, instructor)
```

```sql
CREATE TABLE instructors (
    instructor VARCHAR PRIMARY KEY,
    subject    VARCHAR NOT NULL
);

CREATE TABLE student_instructor (
    student_id INTEGER NOT NULL,
    instructor VARCHAR NOT NULL REFERENCES instructors(instructor),
    PRIMARY KEY (student_id, instructor)
);
```

Now "Dr. Chen teaches Databases" is stored exactly once.

---

# 🧠 The Trade-Off (Important!)

The fix is lossless — but the rule

```
(student_id, subject) → instructor
```

can no longer be enforced by any **single** table. You'd need to join
`Instructor` and `Student_Instructor` and check the result, or enforce it in
application code.

---

# ⚖️ 3NF vs. BCNF

| | 3NF | BCNF |
|---|---|---|
| Redundancy | may keep some | removes it |
| Dependency preservation | always preserved | may be **lost** |
| When to prefer | a determinant isn't a superkey, but the constraint matters | redundancy risk outweighs the lost constraint |

---

# 🎯 Practical Guidance

BCNF is not automatically "better." Ask: **who pays?**

- the database, in the form of redundancy (3NF), or
- the application, in the form of a rule enforced only in code, never by the
  schema itself (BCNF)

---

# 📌 A Note on 4NF

BCNF handles functional dependencies. **4NF** handles **multivalued
dependencies** — two independent lists jammed into one table.

```
Claim(claim_id, document_type, adjuster)
```

---

# 📌 4NF — A Concrete Example

Claim `C1` has two document types (`Police Report`, `Photos`) and two
assigned adjusters (`Maria`, `Tom`) — independently of each other. To avoid
implying a false pairing, you're forced to store **every combination**:

| claim_id | document_type | adjuster |
|---|---|---|
| C1 | Police Report | Maria |
| C1 | Police Report | Tom |
| C1 | Photos | Maria |
| C1 | Photos | Tom |

2 document types × 2 adjusters = 4 rows, just to say "these 2 things and
these 2 things are both true of claim C1."

---

# 📌 4NF Fix

```
Claim_Documents(claim_id, document_type)
Claim_Adjusters(claim_id, adjuster)
```

2 rows + 2 rows = 4, instead of 2 × 2 = 4 that only *coincidentally* matches
here — the gap widens fast as the lists grow (3 doc types × 3 adjusters = 9
rows vs. 3 + 3 = 6). Split whenever two independent, multivalued facts share
one table.

Covered hands-on in Session 4's Lab 2b.

---

# 🔥 Final Clean Design

```
Customer(customer_id, name, email)
Product(product_id, name, category, price)
Order(order_id, customer_id, order_date)
Order_Items(order_id, product_id, quantity)
```

---

# 🔥 Final Clean Design (cont.)

```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    email       VARCHAR NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    category   VARCHAR NOT NULL,
    price      NUMERIC(10,2) NOT NULL CHECK (price >= 0)
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  DATE NOT NULL
);

CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity   INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

---

# 🔥 Final Clean Design (cont.)

This is the surrogate-key upgrade of every table built across this deck —
`product_name` and `customer_name` become `product_id` and `customer_id`.

---

# 💼 Business Value

Normalized design ensures:

- consistency
- scalability
- accurate analytics

---

# ⚠️ Common Mistakes

---

# ❌ Over-Normalization

Splitting past the point the business rules justify — e.g., putting
`category` in its own `Category(category_id, category_name)` table when the
course only ever tracks five fixed categories that never repeat enough to
cause redundancy. Result: every query needs an extra join for no real
integrity benefit.

---

# ❌ Under-Normalization

Stopping before removing a real dependency — e.g., leaving `customer_email`
on the `Order` table "because it's convenient for reporting." Result: the
exact transitive-dependency anomaly from Part 1 comes right back.

---

# 🧠 Balance Is Key

Design depends on the use case. Normalize until every remaining redundancy
is one you've deliberately chosen to keep — not one you missed.

---

# 🔥 Real-World Insight

Analytics systems sometimes **de-normalize intentionally** — flattening
tables back together for read performance (Week 4's star schemas are exactly
this).

But only *after* understanding normalization. You can't make an informed
trade-off you don't understand.

---

# 🧪 In-Class Exercise

Normalize:

```
order_id, customer_name, product_name, price, quantity
```

Identify the functional dependencies first, then apply 1NF → 2NF → 3NF.

---

# 💬 Discussion

- What depends on what? Write each dependency as `X → Y` before you draw
  any tables.
- Where should each piece of data live?
- Which table in your design would you nominate for a surrogate key, and why?

---

# 🧠 What Did We Learn?

- Functional dependencies, in `X → Y` notation
- Superkeys, candidate keys, and prime attributes
- 1NF, 2NF, 3NF, BCNF
- Multivalued dependencies (4NF)
- The 3NF ↔ BCNF trade-off: redundancy vs. dependency preservation
- Clean schema design, from a messy flat table to four related tables

---

# 🎯 Most Important Idea

**Good design = correct dependencies.** Every normal form is just a
sharper statement of the same rule: each fact should be stored in exactly
one place, determined by exactly the key that owns it.

---

# 🚀 Next Week

- Implementation: `CREATE TABLE`, constraints
- Indexing and query performance
- Transactions and ACID
- DuckDB → MySQL

---

# 🙌 End of Week 2

Questions?
