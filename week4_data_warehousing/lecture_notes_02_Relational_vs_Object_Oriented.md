---
marp: true
title: MSIS-2407 — Week 4 (Part 2)
subtitle: Relational vs Object-Oriented and Document Data Models
paginate: true
---

# 📊 Week 4 — Relational vs Object-Oriented and Document Models

Part 1 denormalized the relational model for analysis. This part asks a more
fundamental question: **should the data be relational at all?**

> **Catalog alignment.** The MSIS-2407 description names *"a comparison of
> relational and object-oriented databases"* as a course topic. This is that topic,
> brought up to date — the modern inheritors of the object-oriented database are
> object-relational features and document stores.

---

# 🧩 The problem that started it: impedance mismatch

An application holds an **object**:

```python
order = Order(id=9001, customer=Customer("Ada"),
              lines=[Line("P-100", 2), Line("P-102", 10)])
```

---

# 🧩 The problem that started it: impedance mismatch (cont.)

A normalized database holds **three relations**. Every read shreds the object
across tables; every write reassembles it. That translation layer is the
**object-relational impedance mismatch**, and in the late 1980s it looked
sufficiently painful to justify a new kind of database.

| Mismatch | Object world | Relational world |
|---|---|---|
| Identity | reference / pointer | primary key value |
| Structure | nesting, collections | flat tuples, joins |
| Inheritance | native | mapped by hand (Week 1 Lab 2!) |
| Access | navigate references | declarative set query |

---

# 🏛 What object-oriented databases proposed

**OODBMS** (ObjectStore, Versant, GemStone; later db4o) stored objects directly:

- **Object identity (OID)** — every object has a system identity independent of its
  attribute values
- **Direct references** instead of foreign keys — navigate, do not join
- **Inheritance and methods** stored with the data
- **No shredding** — the application's object graph *is* the storage model

Where it genuinely won: CAD, engineering design, scientific models, telecoms
network topology — deep object graphs, traversed by navigation, with few ad-hoc
analytical queries.

---

# 📉 Why they lost the mainstream

Not because the idea was bad, but because of what they gave up:

---

# 📉 Why they lost the mainstream (cont.)

1. **No declarative query language of comparable power.** OQL never matched SQL's
   ecosystem, optimizer maturity, or user base.
2. **Navigation ties queries to a chosen access path.** Relational's great trick is
   that the *query* says what you want and the *optimizer* decides how — so an
   unanticipated question is still answerable.
3. **Schema evolution was brutal.** Changing a class means migrating every stored
   instance.
4. **Weak analytics story.** "Sum revenue by region for the last three years" is a
   set operation, not a traversal.
5. **Relational vendors absorbed the good parts.** SQL:1999 added user-defined
   types, arrays and inheritance — the *object-relational* model.

---

# 📉 Why they lost the mainstream (cont.)

> The lesson is not "objects lost." It is that **the declarative set model plus a
> cost-based optimizer was harder to displace than anyone expected.**

---

# 📄 The document model — the idea's successor

Document stores (MongoDB, Couchbase, DynamoDB) revived the core insight while
dropping the object machinery:

- store a **whole aggregate** as one JSON-ish document
- no shredding, no join to reassemble
- **flexible schema** — documents in one collection may differ

What they inherited from OODBMS: locality of the aggregate.
What they dropped: OIDs, methods, inheritance.
What they also dropped, at first: joins, and multi-document transactions.

---

# 🔀 Three ways to model one order

| Model | Shape | Reassemble an order | Ad-hoc query across orders |
|---|---|---|---|
| **Relational (3NF)** | `orders`, `order_lines`, `products` | 2 joins | trivial, any dimension |
| **Object-relational (nested)** | one table, `lines` is a `LIST(STRUCT(...))` | none — it is one row | needs `UNNEST` |
| **Document (JSON)** | one column of JSON per order | none | path expressions, no schema guarantees |

---

# 🔀 Three ways to model one order (cont.)

**The trade is always the same: locality versus flexibility of access.**

Nest the data and reading the whole aggregate is one cheap lookup — but any
question that cuts *across* the nesting becomes work. Normalize it and every
question is equally easy, but every read reassembles.

---

# 🧪 All three in DuckDB — no new engine required

DuckDB has native `STRUCT`, `LIST`, `MAP` and JSON, so the comparison is hands-on:

---

# 🧪 All three in DuckDB — no new engine required (cont.)

```sql
-- object-relational: nested collection inside a row
CREATE TABLE order_nested (
    order_id  INTEGER PRIMARY KEY,
    customer  STRUCT(id INTEGER, name VARCHAR),
    lines     STRUCT(sku VARCHAR, qty INTEGER, price DECIMAL(10,2))[]
);

-- reading the whole aggregate: no join
SELECT * FROM order_nested WHERE order_id = 9001;

-- querying across the nesting: UNNEST, i.e. re-shredding at read time
SELECT l.sku, sum(l.qty)
FROM order_nested, UNNEST(lines) AS t(l)
GROUP BY 1;
```

---

# 🧪 All three in DuckDB — no new engine required (cont.)

```sql
-- document: schema-on-read
CREATE TABLE order_doc (order_id INTEGER, doc JSON);
SELECT doc->>'$.customer.name' AS customer FROM order_doc;
```

---

# 🧪 All three in DuckDB — no new engine required (cont.)

Session 8's Lab 2b builds all three from the same source and measures the difference.

---

# 🧭 Choosing — a decision table

| If the dominant pattern is… | Prefer |
|---|---|
| Read/write one whole aggregate by key | document or nested |
| Ad-hoc queries across many entities | relational |
| Strong cross-entity invariants | relational (constraints are declarative) |
| Schema genuinely varies per record | document |
| Analytics and aggregation | relational / columnar |
| Deep graph traversal | graph database (a separate lineage) |

---

# 🧭 Choosing — a decision table (cont.)

**The honest modern answer is usually "both."** Operational systems often use
document stores for aggregates and land the same data, flattened, in a relational
warehouse for analysis. That is exactly the medallion pipeline from Part 1.

---

# ⚠️ What you give up with flexible schema

Flexible schema does not remove the schema. It **moves it into every consumer**,
where it stops being enforced and starts being assumed.

Concretely, in a document store you typically lose:

- declarative referential integrity across documents
- a `CHECK` constraint the engine enforces on every write
- one authoritative answer to "what fields does this collection have?"

Which is why Week 5's data-quality and catalog work exists: **the constraints you
do not declare become audits you must run.** Nothing removes the need for
integrity; you only choose who enforces it and when.

---

# ✅ Check your understanding

1. Give one query that is *cheaper* against `order_nested` than against the 3NF
   schema, and one that is dramatically more expensive. What structural property
   explains both?
2. Object-oriented databases had object identity (OIDs) independent of attribute
   values. Which relational concept from Week 2 Lab 2 does that most resemble, and
   what argument from that lab applies unchanged?
3. A team proposes storing orders as JSON "so the schema can evolve freely." Name
   two integrity guarantees they are giving up and state where each one has to be
   re-implemented.
4. Week 1 Lab 2 mapped a supertype/subtype hierarchy to tables three ways. An
   OODBMS stores inheritance natively. Does that make it the better choice for that
   lab's asset hierarchy? Argue from the queries, not the modeling elegance.

---

# 🙌 End of Week 4 (Part 2)

Lab: Session 8's Lab 2b (`LABS/week4_lab2/`) — model one domain three ways,
then measure what each shape costs.
