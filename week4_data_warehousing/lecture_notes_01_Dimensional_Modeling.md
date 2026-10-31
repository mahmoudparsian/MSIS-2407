---
marp: true
title: MSIS-2407 — Week 4 (Part 1)
subtitle: Dimensional Modeling and OLAP
paginate: true
---

# 📊 Week 4 — Dimensional Modeling and OLAP

Weeks 1–3 built a **normalized transactional** database: minimal redundancy, fast
single-row writes, integrity enforced by constraints.

This week asks a different question: *how do you model data for **analysis**?*

The answer is a deliberately **de**normalized model, and understanding why the same
data deserves two different shapes is the intellectual core of the week.

---

# ⚖️ OLTP vs OLAP — two workloads, two designs

| | OLTP (Weeks 1–3) | OLAP (this week) |
|---|---|---|
| Typical operation | insert/update one row | scan and aggregate millions |
| Optimized for | write throughput, integrity | read throughput, query simplicity |
| Normal form | 3NF/BCNF | deliberately denormalized |
| Joins per query | few, narrow | many, but always along a star |
| Redundancy | minimized | accepted, on purpose |
| Time | current state | full history |

The last row matters most. An OLTP system usually stores *what is true now*. A
warehouse stores *what was true then* — which is why Type 2 dimensions exist.

---

# ⭐ The star schema

```text
              dim_date
                  │
   dim_store ── fact_sales ── dim_product
                  │
             dim_customer
```

* **Fact table** — the events. Long and narrow: foreign keys plus numeric measures.
* **Dimension tables** — the context. Short and wide: descriptive attributes you
  filter and group by.

Every analytical question becomes the same shape of query: *filter the dimensions,
aggregate the fact.* That uniformity is the point — it is what lets a BI tool
generate correct SQL without understanding your business.

---

# 🎯 Grain — the first decision, and the one that binds

**The grain is a one-sentence statement of what a single fact row means.**

> "One row per sale line."

Write it before you write any DDL. Everything else follows from it:

- which dimensions can attach (only those that are *single-valued* at the grain)
- which measures are legal (only those that are additive *at* the grain)
- what "count(\*)" means

---

# 🎯 Grain — the first decision, and the one that binds (cont.)

**Getting it wrong is not recoverable by querying differently.** If your grain is
wrong, every aggregate built on it is wrong, and the error is invisible — the
numbers still look plausible.

Prove the grain against the data before you build. Session 7's Lab 1b, Task 1,
does exactly this.

---

# 🔑 Surrogate keys and unknown members

Two non-negotiables in dimensional design:

**Surrogate keys.** The fact stores an integer the warehouse controls, not the
source system's business key. This is what makes Type 2 history possible at all,
and what protects you when a source system renumbers.

**Unknown members.** Every dimension carries a row at key `-1`. A fact arriving
with an unrecognized business key maps to `-1`, never to `NULL`.

> Why never NULL: a NULL foreign key silently drops the fact row from every inner
> join. Your row counts stop reconciling and nothing raises an error. The unknown
> member keeps the row countable while flagging it as unmatched.

---

# 🕰 Slowly changing dimensions

A store moves region. Do last year's sales move with it?

| Type | Behaviour | Use when |
|---|---|---|
| **Type 1** | overwrite; history lost | corrections — a misspelled name |
| **Type 2** | new row per version, with validity dates and a current flag | anything you report on historically |
| **Type 3** | keep a "previous value" column | one-off reorganizations you must report both ways |

---

# 🕰 Slowly changing dimensions (cont.)

**Type 2 is the default for any attribute you group by.** It is also the one with
invariants that must be tested, not assumed:

1. exactly one current row per business key
2. no overlapping validity intervals
3. no gaps between versions

An overlap **double-counts** every fact inside it; a gap **drops** them. Neither
announces itself.

---

# 🔗 The as-of join — why Type 2 is worth the trouble

Loading the fact, resolve the dimension key **as it was on the event date**:

```sql
JOIN dim_store d
  ON d.store_id = s.store_id
 AND s.sale_date BETWEEN d.effective_from AND d.effective_to
```

Join on `d.is_current` instead and every historical sale is silently restated into
today's org chart. Revenue for a region that no longer exists simply vanishes.

The totals still add up. They are just answers to a question nobody asked.

---

# ➕ Additivity — which measures may you SUM?

| Class | Sums across | Example |
|---|---|---|
| **Additive** | every dimension | quantity, revenue, cost |
| **Semi-additive** | every dimension **except time** | inventory on hand, account balance |
| **Non-additive** | none — recompute from components | unit price, margin %, ratios |

---

# ➕ Additivity — which measures may you SUM? (cont.)

Two failure modes to internalize:

- `SUM(on_hand)` across three month-end snapshots triple-counts the same physical
  stock. Semi-additive measures need a declared **time rule** — last value, or
  average — written into the model documentation.
- `AVG(margin_pct)` weights a 1-unit line the same as a 500-unit line. The correct
  blended margin is a **ratio of sums**, never an average of ratios.

---

# 🧊 Fact table flavours

| Flavour | Records | Grain example |
|---|---|---|
| **Transaction** | events as they happen | one row per sale line |
| **Periodic snapshot** | state at intervals | one row per store/product/day |
| **Accumulating snapshot** | a process with milestones | one row per order, updated as it ships |

Snapshot facts are where semi-additive measures live. Their row counts also grow
frighteningly fast — 400 stores × 30,000 SKUs × daily is 12M rows/day — which is
what drives partitioning and aggregate design.

---

# 🧪 Worked Example: One OLTP Order Set, Built Into a Star

The same order lines from Weeks 2–3, normalized as `orders` / `order_items` /
`products` / `customers`. **Grain: one row per order line** — identical to the
grain of `order_items` itself, just widened with keys and a computed measure.

```
order 1: Alice   → Laptop ($1200 × 1), Mouse ($25 × 2)
order 2: Bob     → Phone  ($800 × 1)
order 3: Charlie → Tablet ($300 × 3), Headphones ($150 × 1)
```

---

# 🧪 Worked Example: One OLTP Order Set, Built Into a Star (cont.)

```sql
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,  -- surrogate
    product_id  INTEGER,              -- the OLTP natural key
    name        VARCHAR,
    category    VARCHAR
);

CREATE TABLE fact_sales (
    date_key     INTEGER,
    customer_key INTEGER,
    product_key  INTEGER REFERENCES dim_product(product_key),
    order_id     INTEGER,   -- kept for traceability, not for joining
    quantity     INTEGER,   -- additive
    revenue      DECIMAL(10,2)  -- additive: price × quantity, computed once, at load
);
```

---

# 🧪 Worked Example: One OLTP Order Set, Built Into a Star (cont.)

`revenue` is computed **once**, at load time — every downstream query just sums
a column instead of recomputing `price × quantity` and risking a different
answer per report.

---

# 🧪 Worked Example: Querying the Star

```sql
SELECT dp.name, SUM(f.revenue) AS revenue
FROM fact_sales f
JOIN dim_product dp ON f.product_key = dp.product_key
GROUP BY dp.name
ORDER BY revenue DESC;
```

| name | revenue |
|---|---|
| Laptop | 1200.00 |
| Tablet | 900.00 |
| Phone | 800.00 |
| Headphones | 150.00 |
| Mouse | 50.00 |

**Reconciliation:** `1200 + 900 + 800 + 150 + 50 = 3100`, matching the hand-summed
total of all five order lines above — the same check the Week 4 labs run on every
task, and the same idea as Week 3's "always verify data after loading."

---

# 🌊 Beyond the star — modern architectures

- **Data lake** — raw files in object storage, schema-on-read, cheap, ungoverned
- **Lakehouse** — lake storage plus table semantics: ACID, schema, time travel
- **Medallion** — bronze (raw) → silver (validated) → gold (modeled), staging the
  schema commitment described in Week 1 Part 4

The star schema does not go away in a lakehouse. It reappears as the **gold layer**.
Dimensional modeling is a modeling discipline, not a storage technology.

---

# 🧪 Labs

Week 4's labs are published in `LABS/` during class (Session 7 →
`LABS/week4_lab1/`, Session 8 → `LABS/week4_lab2/`):

| Lab | Focus |
|---|---|
| 1a | OLTP → star schema: grain, surrogate keys, a date dimension |
| 1b | Grain, conformed dimensions, SCD Type 2, as-of loading, additivity |
| 2a | Asking questions of a warehouse — drill-down, `ROLLUP`, windows, top-N per group |
| 2b | Relational vs nested vs document models (see Part 2) |
| 2c | *Optional practice:* OLAP querying — grouping sets, window frames, date spines, cohorts |

Each lab builds its own data inline. For extra practice against a larger,
pre-built fact table with the same shape as the worked example above, see
`datasets/warehouse_star_schema/fact_sales.csv` (`order_date`, `customer_id`,
`store_id`, `product_id`, `quantity`, `sales_amount` — build the dimensions
yourself, as an exercise in the grain and surrogate-key ideas from this deck).

---

# ✅ Check your understanding

1. State the grain of a fact table recording hotel room-nights. Now state the grain
   if the business also wants to report on *cancelled* bookings. Did the grain
   change, or did you need a second fact table?
2. Your CFO asks for last year's sales **using today's regions** — the opposite of
   the as-of join. Is that a wrong question? What is it called, and how do you serve
   both from one dimension?
3. Why is `-1` the conventional unknown-member key rather than `0`?

---

# 🙌 End of Week 4 (Part 1)

Next: **Part 2 — Relational vs Object-Oriented and Document Models.**
