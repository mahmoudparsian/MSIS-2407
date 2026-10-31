---
marp: true
title: MSIS-2407 — Week 5 (Part 2)
subtitle: Backup, Recovery, Capacity and Governance
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

# 💾 Week 5 — Backup, Recovery, Capacity and Governance

Part 1 protected the data from people who should not see it.

This part protects it from **loss**, from **growth**, and from quietly becoming
wrong.

---

# 🧯 A backup you have never restored is a hypothesis

The single most common failure in this area is not the absence of backups. It is
backups that were never tested.

The full cycle has **five** steps, and most teams do four:

1. take the backup
2. compute a verification **checksum** of the source
3. *(the disaster)*
4. restore into a clean database
5. **re-compute the checksum and compare** ← the step that gets skipped

Row counts matching is not verification. You can restore the right *number* of
wrong rows.

---

# ⏱️ RPO and RTO — the two numbers that matter

| Term | Question | Sets |
|---|---|---|
| **RPO** — recovery point objective | how much data may we lose? | backup **frequency** |
| **RTO** — recovery time objective | how long may we be down? | backup **method** |

Nightly backups mean an RPO of up to **24 hours**. That is not a technical fact
to apologize for — it is a commitment somebody signed.

If 24 hours of lost transactions is unacceptable, the answer is continuous log
shipping, and it costs money. **That is a business decision, not a DBA decision.**

---

# 🗂️ Backup types

| Type | Copies | Restore | Cost |
|---|---|---|---|
| **Full** | everything | simplest | slowest, largest |
| **Incremental** | changes since last backup | replay a chain | cheapest to take |
| **Differential** | changes since last *full* | full + one | middle |
| **Log shipping** | every committed transaction | point-in-time | continuous |

Log shipping is what turns "we lost a day" into "we lost 30 seconds", and it is
the only option that supports **point-in-time recovery** — restoring to 14:32,
just before someone ran the bad `DELETE`.

---

# 🦆 In DuckDB

```sql
EXPORT DATABASE 'backup_2026_04_01' (FORMAT PARQUET);
-- ... disaster ...
IMPORT DATABASE 'backup_2026_04_01';
```

The export is an inspectable folder: `schema.sql`, `load.sql`, and one Parquet
file per table. Not a proprietary blob — you can read it without DuckDB, which is
itself a useful property in a backup.

Practised end to end in Session 10's Lab 2a, Tasks 1–3 (and Session 9's Lab 1b,
Task 5) — including the checksum comparison
and measuring exactly how many rows the RPO gap cost.

---

# 📈 Capacity: measure bytes, not rows

"The table has 400,000 rows" tells you nothing about a storage budget.

Two independent savings, worth separating:

| Comparison | What it measures |
|---|---|
| CSV → Parquet (uncompressed) | the value of **columnar layout** |
| Parquet uncompressed → zstd | the value of **compression** |

On the lab's data, CSV → Parquet+zstd is roughly a **15× reduction**.

Plan with **bytes per row × projected rows**, and project the growth rate. A table
doubling quarterly is a different conversation from one growing 5% a year.

---

# 🔍 Data quality has dimensions

"Improve data quality" is not actionable. These six are:

| Dimension | Question |
|---|---|
| **Completeness** | is the value present? |
| **Validity** | does it match its format or code list? |
| **Uniqueness** | one row per real-world thing? |
| **Accuracy** | is the value possible? |
| **Timeliness** | is it fresh enough? |
| **Consistency** | do related facts agree? |

Each becomes a **rule** that returns a count, and rules get **weights** — a
malformed account number is not the same size of problem as a missing email.

---

# 📊 Score the direction, not just the level

A single quality percentage is a comfortable number that hides everything.

Report **bands** and **movement**:

* `RED` / `AMBER` / `GREEN` against a threshold
* and the **change** since the last run

A rule stuck at 97% for a year is a backlog item.
A rule that dropped from 100% to 97% last night is an **incident**.

Alert on drift, not only on level.

---

# 🩹 Remediation must be reversible

Every automated fix needs an **audit trail**: what changed, from what, to what, by
which rule, when. Write the fix and the audit row in **one transaction**.

And know which fixes you are allowed to make automatically:

| Case | Action |
|---|---|
| `'COMMERICAL'` → `'COMMERCIAL'` | ✅ correct it — deterministic, safe |
| a negative meter reading | ⛔ **quarantine** it, do not zero it |

Zeroing an impossible value destroys the evidence that a meter is broken. The
reading is wrong, but *the fact that it arrived* may be the most useful thing in
the table.

---

# 🏛️ Governance: catalog and lineage as data

Documentation in a wiki answers no questions at 2 a.m. Store it as tables:

* **catalog** — every column, with owner, classification, PII flag
* **lineage** — directed edges: this object feeds that one

Then the questions become queries:

* *what breaks if I drop this column?* → recursive traversal
* *what PII do we hold, and who owns it?* → one `SELECT`
* *which objects have no steward?* → the gap the catalog exposes

The value is not the documentation. It is the **gaps** it makes visible.

---

# 🕸️ Lineage impact: "what breaks if I change this?"

Store lineage as edges, `lineage(source_object, target_object)`:

```
raw_orders    -> stg_orders      stg_orders         -> fct_sales
raw_customers -> dim_customer    dim_customer       -> fct_sales
fct_sales     -> rpt_weekly_revenue
rpt_weekly_revenue -> dash_ceo   stg_orders         -> rpt_late_shipments
```

---

# 🕸️ Lineage impact — the query

Everything downstream of `raw_customers` is a walk along the edges — the same
**recursive CTE** you used for hierarchies in Week 1:

```sql
WITH RECURSIVE impact AS (
    SELECT target_object AS obj, 1 AS hops
    FROM lineage
    WHERE source_object = 'raw_customers'
    UNION ALL
    SELECT l.target_object, i.hops + 1
    FROM lineage AS l
    JOIN impact AS i ON l.source_object = i.obj
)
SELECT obj, MIN(hops) AS hops
FROM impact
GROUP BY obj
ORDER BY hops, obj;
```

---

# 🕸️ Lineage impact — the result

| obj | hops |
|---|---:|
| dim_customer | 1 |
| fct_sales | 2 |
| rpt_weekly_revenue | 3 |
| dash_ceo | 4 |

Changing a customer column can reach the CEO's dashboard four steps away.
`MIN(hops)` matters when an object is reachable by two routes (`fct_sales` is fed
by both `stg_orders` and `dim_customer`). Real lineage graphs can contain
mistakes that form a loop — carry the visited path and stop on revisit, exactly
as in Week 1.

---

# 🧑‍🤝‍🧑 Master data: one customer, many records

After a merger or a migration, the same supplier or customer exists in several
systems with slightly different spellings. **Master data management (MDM)**
produces one trusted **golden record** per real-world thing, in three steps:

1. **Block** — only compare records that share a cheap key (e.g. postal code +
   house number). Comparing every pair is *n²/2*: at a million records that's
   500 billion comparisons.
2. **Match** — score each candidate pair with a similarity function, e.g.
   DuckDB's `jaro_winkler_similarity(a, b)` (1.0 = identical), and call it a
   match above a **threshold**. Matches chain: if A≈B and B≈C, all three are
   one cluster (a recursive walk again).
3. **Survive** — pick one record per cluster with a written, deterministic
   **survivorship rule** (Week 3), e.g. most recent update, then most complete.

---

# 🧑‍🤝‍🧑 Matching: similarity and the threshold

| a | b | similarity |
|---|---|---:|
| Acme Industrial Supply | ACME Industrial Supply Co | 0.887 |
| *same, after `lower()` on both* | | 0.976 |
| Northgate Metals | Northgate Metal | 0.987 |
| Northgate Metals | Northwind Metals | **0.867** |

Normalize before comparing (case, punctuation, "Co"/"Inc"). And note the last
row: two **different** companies score 0.867. The threshold is a business
decision with two kinds of error — merging different customers (a privacy and
billing problem) versus leaving duplicates (a reporting problem). Test both
directions on known examples before you trust it.

---

# 🧭 Monitoring and the runbook

A dashboard nobody is accountable for is decoration. A runbook names:

* the metrics and their thresholds
* who is paged, and when
* the first three steps on an alert
* the RPO/RTO you have actually committed to

Watch for the blind spot in step-over-step drift checks: a metric that climbs 10%
a night trips no single-step rule and doubles in a week. Compare against a
**baseline window**, not just yesterday.

---

# ✅ Check your understanding

1. Write the one-sentence RPO and RTO commitment you would sign for a
   student-records system, and name the mechanism that delivers it.
2. Your restore produced the right row count but a different checksum. What are
   two things that could have happened?
3. Give a data-quality rule that a `CHECK` constraint **cannot** enforce, and say
   where it has to live instead.
4. A single weighted quality score reads 96% while one rule sits in RED. What
   would you put on the director's dashboard instead?
5. Storage is doubling every quarter. Name two responses and what each costs you
   analytically.

---

# 🙌 End of Week 5 (Part 2)

Labs (Session 10, `LABS/week5_lab2/`): **Lab 2a** — backup, restore, RPO and
change-log replay, quality rules, quarantine, a data catalog; **Lab 2b** — a
quality scorecard, lineage, and master data management.

Then: the **Final Exam** — see the course grading page for its format.
