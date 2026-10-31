---
marp: true
title: MSIS-2407 — Week 3 (Part 3) — Indexing and Query Performance
subtitle: From Correct to Fast
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

# 📊 Week 3 (Part 3) — Indexing & Query Performance
## From Correct → Fast

This part is where you move from *building* systems to *understanding how
they behave and scale*.

---

# 🎯 Learning Objectives

By the end of today you can:

- Explain why a full table scan gets slow as data grows
- Create an index and explain what it does mechanically
- Weigh the read/write trade-off an index introduces
- Explain how DuckDB's columnar storage changes indexing intuition from a
  traditional row-store RDBMS

---

# 🧠 Big Idea

**A correct query that is slow is still a bad query.** Users don't
experience "technically correct" — they experience how long they waited.

---

# 💼 Real-World Scenario

- Millions of rows in a table
- Queries need to return in seconds, not minutes
- Users expect near-instant results, every time

At small scale, almost anything is "fast enough." These techniques matter
because scale eventually arrives.

---

# ⚠️ The Problem: Full Table Scan

Without help, finding rows means reading **every row**, checking each one
against your `WHERE` clause, and discarding the ones that don't match.

```sql
SELECT * FROM orders WHERE customer_id = 42;
-- without an index: check all 10,000,000 rows to find the ~3 that match
```

---

# 🐢 What a Full Scan Costs

Work grows **linearly** with table size: a table 10× bigger takes roughly
10× longer to scan, no matter how selective your `WHERE` clause is. This
is the behavior an index exists to avoid.

---

# 🔥 Solution: An Index

An index is like a book's table of contents — a separate, ordered
structure that lets the engine jump straight to the rows you want instead
of reading the whole book.

---

# 📖 The Analogy, Precisely

- **Without an index:** find every mention of "normalization" by reading
  the book cover to cover
- **With an index:** look up "normalization" in the index at the back, get
  a page number, and turn straight there

A database index works the same way: it maps a column value to the row(s)
that have it.

---

# 🔧 Creating an Index

```sql
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

Most indexes are **B-trees**: a sorted, tree-shaped structure that turns
"scan everything" into "narrow down in a handful of comparisons" —
`O(log n)` instead of `O(n)`.

---

# 🧠 What Happens Mechanically?

With the index in place, `WHERE customer_id = 42` no longer scans the
table — it walks the B-tree (a handful of comparisons, even at millions of
rows) straight to the matching rows.

---

# ⚡ Performance Gain

- faster `SELECT ... WHERE`
- faster `JOIN`s on the indexed column
- faster filtering in general, on that column

---

# 💥 The Trade-Off

Indexes aren't free:

- extra **storage** — the index is a second copy of (part of) the data
- slower **INSERT/UPDATE/DELETE** — every write has to also update every
  index on that table, not just the table itself

---

# ⚖️ Trade-Off Table

| Benefit | Cost |
|---|---|
| fast reads on the indexed column | slower writes to that table |
| faster joins | extra storage per index |

---

# 🔥 When to Index

Good candidates:

- foreign key columns (you'll join on them constantly)
- columns that appear often in `WHERE` clauses
- columns with **high cardinality** — many distinct values, so the index
  actually narrows the search a lot

---

# ⚠️ When NOT to Index

- small tables — a full scan of 500 rows is already instant
- rarely queried columns — paying the write cost for a read you never do
- **low-cardinality** columns — a handful of distinct values doesn't narrow
  much (more on this next — DuckDB makes this cost especially visible)

---

# 🧭 DuckDB Is Different: Columnar Zone Maps

Everything so far describes a traditional **row-store** engine (like
MySQL's InnoDB). DuckDB is **columnar**, and it automatically maintains
**zone maps** — the min/max value of every column, per storage block.

A query with `WHERE price > 1000` can already skip any block whose zone map
says `max(price) < 1000` — **before you ever create an index.**

---

# ⚠️ The Counterintuitive Result

- An index on an **already-sorted** column buys you **nothing** — the zone
  map prunes blocks just as effectively on its own.
- An index on a **low-cardinality** column (say, a `status` with 3 possible
  values) can make a scan **slower**, not faster — you pay to maintain and
  traverse a structure that barely narrows anything.

This directly contradicts the row-store intuition from the last few
slides. In DuckDB, indexing decisions must be **measured**, not assumed.

---

# 🧪 Example Query

```sql
SELECT * FROM orders WHERE customer_id = 10;
```

`customer_id` is high-cardinality and unsorted — a good index candidate in
either a row-store or DuckDB.

---

# 🔍 Before vs. After

- Without an index: full scan (row-store) — or a zone-map-assisted scan
  that still touches every matching block (DuckDB)
- With a well-chosen index: a direct, narrow lookup

The word "well-chosen" is now doing real work — see the last two slides.

---

# 🧪 In-Class Exercise

1. Run a query without an index; note how it performs
2. Add an index on the filtered column
3. Compare performance — measure it, don't guess
4. Repeat on a low-cardinality column and compare again

(Session 9's Lab 1b does exactly this, with real timing, on a multi-million-row
table.)

---

# 💬 Discussion

- Why not index every column, "just in case"?
- Would your answer change between MySQL and DuckDB?

---

# 🧠 Expected Answer

👉 Every index costs write performance and storage — and in DuckDB, an
unselective or already-sorted index can cost *read* performance too, with
no benefit to show for it.

---

# 🔥 Key Insight

Optimization is about **balance** — and about **measuring your specific
engine**, not applying a universal rule you learned somewhere else.

---

# 🧠 What Did We Learn?

- Full table scans vs. indexed lookups
- How to create an index, and what it costs
- The general read/write trade-off
- DuckDB's columnar zone maps, and why they change indexing strategy

---

# 🚀 Next: Part 4

- 👉 Transactions and ACID
- 👉 Concurrency
- 👉 How a database behaves under simultaneous access

---

# 🙌 End of Part 3
