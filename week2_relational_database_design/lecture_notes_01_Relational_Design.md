---
marp: true
title: MSIS-2407 — Week 2 (Part 1) — Relational Design
subtitle: From ER Model to Tables
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

# 📊 Week 2 (Part 1) — Relational Design
## From ER Model → Tables

---

# 🎯 Learning Objectives

By the end of today you can:

- Convert ER/EER diagrams into relational schemas
- Map entities, attributes, and relationships to tables, columns, and keys
- Apply primary key, foreign key, and other integrity constraints
- Recognize redundancy and the anomalies it causes
- Explain why anomalies motivate normalization (Part 2)

---

# 🧠 The Big Transition

**Week 1:** 👉 Conceptual design — ER/EER diagrams, business language

**Week 2:** 👉 Logical design — relational tables, implementation language

Same model, different altitude. Week 1 asked *"what does the business track?"*
Week 2 asks *"how do we store it?"*

---

# 💼 The Real-World Question

You've drawn the ER diagram. Now: **how do we turn it into an actual
database?**

There's a small, mechanical set of rules that gets you there — no guessing
required.

---

# 🔥 ER → Relational Mapping Rules

| ER concept | Relational concept |
|---|---|
| Entity | Table |
| Attribute | Column |
| Identifier / key attribute | Primary key |
| 1:M relationship | Foreign key, on the "many" side |
| M:N relationship | Bridge (junction) table |

This table is the whole chapter in one line — everything else on the next
slides is a worked example of applying it.

---

# 📦 Entity → Table: A Worked Example

Customer entity (from Week 1): `customer_id`, `name`, `email`

```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    email       VARCHAR NOT NULL UNIQUE
);
```

Each attribute becomes a column; the entity's identifier becomes the
`PRIMARY KEY`.

---

# 📦 Another Example: Order

Order entity: `order_id`, `order_date` — but *not* `customer_id`. That
attribute doesn't belong to Order on its own; it's the relationship to
Customer, and relationships are handled separately (next slide).

```sql
CREATE TABLE orders (
    order_id   INTEGER PRIMARY KEY,
    order_date DATE NOT NULL
);
```

---

# 🔗 Relationships Become Foreign Keys

Customer → Order is 1:M (one customer, many orders). **Rule:** the foreign
key goes on the **many** side.

```sql
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  DATE NOT NULL
);
```

`orders.customer_id` *is* the relationship, expressed as data.

---

# 📊 Handling 1:M — The General Pattern

Any 1:M relationship follows the same recipe:

1. The **"one"** side keeps its own table, unchanged.
2. The **"many"** side gets one new column: a foreign key referencing the
   "one" side's primary key.
3. That FK is `NOT NULL` if participation on the "many" side is mandatory
   (Week 1) — nullable if optional.

Example: Customer (1) → Order (M). `orders.customer_id` is `NOT NULL`,
because Week 1 established that every order has exactly one customer
(mandatory participation).

---

# 🔒 Keys and Constraints Recap

Week 1 covered these conceptually; here's how each becomes SQL:

| Constraint | Enforces | SQL keyword |
|---|---|---|
| Primary key | row uniqueness, never null | `PRIMARY KEY` |
| Foreign key | the referenced row must exist | `FOREIGN KEY ... REFERENCES` |
| Uniqueness (non-key) | no duplicate values | `UNIQUE` |
| Required value | column can't be empty | `NOT NULL` |
| Domain rule | value must satisfy a condition | `CHECK (...)` |

---

# 🔒 Constraints, Worked

```sql
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    category   VARCHAR NOT NULL,
    price      NUMERIC(10,2) NOT NULL CHECK (price >= 0)
);
```

`CHECK (price >= 0)` stops a bad row before it is ever stored — this is
Week 1's *schema-on-write* idea, applied.

---

# 📦 Handling M:N — The Problem

Order ↔ Product: one order has many products; one product appears on many
orders.

❌ **Cannot be implemented directly** — a single foreign-key column can only
point to one row on the other side.

---

# ✅ Handling M:N — The Solution

Introduce a bridge (junction/associative) table — Week 1 already showed why.
`orders` and `products` both already exist (previous slides), so this table
can reference both:

```sql
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity   INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

Composite primary key, two foreign keys — the bridge-table pattern is the
real-world standard for every M:N relationship you will ever model.

---

# 🔗 More Mapping Rules: 1:1 and Weak Entities

**1:1** — put the foreign key on the side where *every* row has a partner, and
make it `UNIQUE` (that is what turns 1:M into 1:1). Every store has exactly one
manager; an employee manages at most one store:

```sql
CREATE TABLE store (
    store_id   INTEGER PRIMARY KEY,
    city       VARCHAR NOT NULL,
    manager_id INTEGER NOT NULL UNIQUE REFERENCES employee(employee_id)
);
```

---

# 🔗 More Mapping Rules: 1:1 and Weak Entities (cont.)

**Weak entity** (Week 1: `Room` inside `Building`) — the owner's key plus the
partial key form the primary key; the owner's key is also a foreign key:

```sql
CREATE TABLE room (
    building_code VARCHAR NOT NULL REFERENCES building(building_code),
    room_no       VARCHAR NOT NULL,
    seats         INTEGER,
    PRIMARY KEY (building_code, room_no)
);
```

---

# 🧬 Mapping a Specialization: Three Options

Week 1's `Payment` → `Card` / `Bank transfer` (disjoint, total) can become tables
in three ways:

| Option | Tables | Choose it when |
|---|---|---|
| **1. Supertype + one table per subtype** | `payment` + `card_payment` + `bank_transfer_payment`; each subtype's PK is also an FK to `payment` | the default: subtype columns can be `NOT NULL`, subtypes can have their own relationships |
| **2. One table + type column** | `payment` holds every column; subtype columns are `NULL` for the other type | few subtype columns; most queries read all payments |
| **3. One table per subtype only** | `card_payment` and `bank_transfer_payment`, each repeating `order_id`, `amount` | total **and** disjoint, and the kinds are rarely queried together |

---

# 🧬 Mapping a Specialization: Three Options (cont.)

Options 1 and 2 keep a `payment_type` column — the **subtype discriminator** — that
says which subtype a row belongs to. Option 1's subtype table shares the
supertype's key:

```sql
CREATE TABLE card_payment (                      -- option 1
    payment_id INTEGER PRIMARY KEY REFERENCES payment(payment_id),
    card_last4 CHAR(4) NOT NULL,
    auth_code  VARCHAR NOT NULL
);
```

---

# 💥 What Happens Without This Discipline: Redundancy

One flat table instead of four — real rows from the Week 2 dataset:

| order_id | customer_name | customer_email | product_name | category | price |
|---|---|---|---|---|---|
| 1 | Alice | alice@gmail.com | Laptop | Electronics | 1200 |
| 1 | Alice | alice@gmail.com | Mouse | Electronics | 25 |
| 3 | Charlie | charlie@gmail.com | Tablet | Electronics | 300 |
| 3 | Charlie | charlie@gmail.com | Headphones | Electronics | 150 |

Alice's name and email are stored twice. Every repeated fact is a chance for
the copies to disagree.

---

# ⚠️ Three Kinds of Anomalies

- **Insert anomaly** — can't add a fact without an unrelated fact attached
- **Update anomaly** — a repeated fact is updated in one place but not others
- **Delete anomaly** — deleting one fact accidentally erases another

All three come from the same root cause: **one table is doing the job of
several entities at once.**

---

# ❌ Insert Anomaly — Worked Example

**Question:** A new product, "Keyboard," just arrived in inventory — no one
has ordered it yet. Can you record its price and category?

In the flat table: **no.** Every row requires an `order_id`, so there is
nowhere to put a product that isn't attached to an order yet.

**Fix:** a standalone `products` table lets you insert a product with zero
orders.

---

# ❌ Update Anomaly — Worked Example

Alice changes her email to `alice.new@gmail.com`. In the flat table, her
email appears on both of order 1's line items — update only one:

| order_id | customer_name | customer_email |
|---|---|---|
| 1 | Alice | alice.new@gmail.com |
| 1 | Alice | alice@gmail.com |

Same customer, two different emails on file. Which one is correct?

---

# ❌ Delete Anomaly — Worked Example

Bob cancels his only order (`order_id` 2, the Phone).

Delete that row, and every fact about the **Phone product** — its price,
its category — disappears with it, even though the product itself still
exists in the catalog.

Deleting a fact about one entity should never erase facts about a different
entity.

---

# 🧠 Key Insight

All three anomalies share one fix: **one table, one subject.** A table that
mixes Customer facts, Product facts, and Order facts will always have this
problem, no matter how carefully you insert, update, or delete rows.

---

# 🔥 Motivation for Normalization

We normalize to:

- remove redundancy
- prevent anomalies
- keep updates consistent

Part 2 turns *"one table, one subject"* into a precise, repeatable
procedure: 1NF → 2NF → 3NF → BCNF.

---

# 🧪 In-Class Exercise

Given the flat table:

```
order_id, customer_name, customer_email, product_name, category, price, quantity, order_date
```

Sketch the tables you would split this into, and mark each table's primary
and foreign keys. You'll formalize this exact exercise with dependency
reasoning in Part 2.

---

# 💬 Discussion

- Where should `price` live — with the order, or with the product? What
  happens if the store changes a price *after* an order has already shipped?
- Where should customer info live?
- Is `category` a fact about the product, or about the order?

---

# 🧠 What Did We Learn?

- ER → relational mapping rules (entity → table, attribute → column,
  relationship → foreign key)
- 1:M via a foreign key on the "many" side
- M:N via a bridge table with a composite key
- Constraints: `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`, `CHECK`
- Insert, update, and delete anomalies — and their common cause

---

# 🚀 Next: Part 2

- Normalization: 1NF, 2NF, 3NF, BCNF
- Functional dependencies, formally
- Turning *"one table, one subject"* into a repeatable procedure

---

# 🙌 End of Part 1
