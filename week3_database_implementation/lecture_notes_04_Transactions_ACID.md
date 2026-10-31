---
marp: true
title: MSIS-2407 — Week 3 (Part 4) — Transactions and ACID
subtitle: Databases as Systems With Guarantees
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

# 📊 Week 3 (Part 4) — Transactions & ACID
## Transactions and Data Integrity

This is where a database stops being "storage" and becomes a **system with
guarantees**.

---

# 🎯 Learning Objectives

By the end of today you can:

- Define a transaction and explain why "all or nothing" matters
- Explain each ACID property with a concrete example
- Use `BEGIN` / `COMMIT` / `ROLLBACK` correctly
- Explain DuckDB's default autocommit behavior, and why it's risky unmanaged
- Explain how DuckDB handles two writers on the same row

---

# 🧠 What Is a Transaction?

A transaction is a **unit of work** — a group of operations that must
either *all* succeed or *all* fail together. There is no valid in-between
state.

---

# 💼 Example: A Bank Transfer

Moving $100 from Account A to Account B is really two operations:

1. Deduct $100 from Account A
2. Add $100 to Account B

👉 Both must happen, or **neither** should.

---

# ⚠️ The Problem

What if the system crashes **between** step 1 and step 2?

---

# 💥 The Result, Without a Transaction

- $100 is deducted from A
- The crash happens before B is credited
- $100 has **vanished** — the system is now inconsistent, and nothing in
  the data says why

---

# 🔥 The Solution: Transactions

A transaction guarantees **all or nothing**: if the system crashes before
`COMMIT`, every change in that transaction is undone automatically, as if
none of it ever ran.

---

# 🧠 ACID Properties

---

# 🔒 Atomicity

**All operations in a transaction succeed, or none do.** The bank transfer
either completes both steps or leaves both accounts untouched — never a
half-finished transfer.

---

# 📊 Consistency

**The database moves from one valid state to another.** Every constraint
(foreign keys, `CHECK`s, business rules like "total money in the system is
unchanged") holds true both before and after the transaction.

---

# 🔁 Isolation

**Concurrent transactions don't see each other's half-finished work.** Even
if two transactions physically run at overlapping times, each behaves as
if it ran alone.

---

# 💾 Durability

**Once a transaction commits, it survives a crash.** Turn the power off the
instant after `COMMIT` returns — the change is still there when the system
comes back up.

---

# 🧠 Easy Way to Remember

**ACID = the guarantees that make "reliable database" mean something
specific**, not just a vague promise.

---

# 🔧 A Transaction, in SQL

```sql
BEGIN;

UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;

COMMIT;
```

Both updates happen together, or neither does.

---

# ❌ If Something Fails

```sql
BEGIN;

UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
-- something goes wrong here (a constraint fails, the app crashes, you change your mind)

ROLLBACK;
-- the first UPDATE is undone — balance is back to what it was
```

---

# 🧠 Key Idea

- `COMMIT` — save every change in the transaction, permanently
- `ROLLBACK` — undo every change in the transaction, as if it never ran

---

# ⚠️ The Default You Don't See: Autocommit

Outside an explicit `BEGIN`, **every statement is its own transaction**,
committed immediately. Run the two `UPDATE`s from the transfer example
*without* `BEGIN`/`COMMIT`, and a crash between them really does lose the
$100 — with no error, because each statement already succeeded on its own.

👉 This is exactly why you wrap related statements in an explicit
transaction — autocommit alone gives you no "all or nothing" guarantee
across statements.

---

# 🔥 Concurrency

Multiple users (or processes) accessing and modifying the same data at the
same time.

---

# 💥 The Problem

Two users try to update the **same row**, at close to the same time.

---

# ⚠️ Issues This Raises

- **Lost updates** — one user's change is silently overwritten by another
- **Inconsistent reads** — a query sees a mix of old and new data mid-update

---

# 🧠 Worked Example: A Lost Update

1. User A reads `balance = 500`
2. User B updates `balance` to `600` and commits
3. User A, still working from its stale read of `500`, computes `500 - 50`
   and writes `balance = 450`

👉 User B's update is **gone** — overwritten without anyone being told.

---

# 🧭 How DuckDB Handles This: Optimistic Concurrency

DuckDB does **not** make a second writer wait. Instead:

1. Both transactions proceed independently, each against its own snapshot
2. If they conflict (both write the same row), the **second writer's
   `UPDATE` fails** at once with `Conflict on update!` — not silently
   queued, not blocked
3. Your application must catch that error and **retry** the transaction

This is different from a system like MySQL/InnoDB, which typically **locks**
the row and makes the second writer wait its turn.

---

# 🧠 Why "Optimistic"?

DuckDB assumes conflicts are **rare** and detects them **after the fact**,
rather than preventing them **up front** with locks. It's optimistic in
the literal sense: proceed without locking, and raise an error the moment
a second writer touches a row another open transaction has changed.
This is exactly why a real system needs a **retry policy** — not just a
`try`, but a plan for what happens when it fails.

---

# 🔒 Isolation Levels (Conceptual)

- **Low isolation** — faster, but more exposure to anomalies like the lost
  update above
- **High isolation** — safer, but transactions may wait longer or abort
  more often

---

# 💼 The Business Trade-Off

| | Speed | Safety |
|---|---|---|
| Low isolation | high | low |
| High isolation | low | high |

There is no setting that gives you both for free.

---

# 🔥 Real-World Thinking

- **Banks** → strong consistency, even at a speed cost — losing $100 is
  unacceptable
- **Analytics dashboards** → often relaxed, faster, "good enough" freshness

The right isolation level depends on what happens if you get it wrong.

---

# 🧪 In-Class Exercise

Using an `accounts(account_id, balance)` table:

1. Simulate two "users" both updating the same `account_id` in DuckDB
2. Observe what happens to the second write
3. Discuss: how would you make the second attempt retry instead of fail?

---

# 💬 Discussion

- Is strong consistency always required?
- When is it safe to relax it?

---

# 🧠 Key Insight

Databases balance **performance** and **correctness** — and that balance is
a deliberate design choice, not an accident.

---

# ⚠️ Common Misconception

**Students think:** 👉 "A database is just storage."

**Reality:** 👉 A database is a **system with guarantees** — about
atomicity, consistency, isolation, and durability — that storage alone
does not provide.

---

# 🧠 What Did We Learn?

- Transactions, and why "all or nothing" matters
- ACID: atomicity, consistency, isolation, durability
- Autocommit as the invisible default, and why it's risky unmanaged
- DuckDB's optimistic concurrency: abort-and-retry, not lock-and-wait
- Concurrency trade-offs between speed and safety

---

# 🎯 Most Important Idea

**Databases guarantee correctness under real-world conditions** — crashes,
concurrent users, and conflicting writes included, not just the happy path.

---

# 🚀 Next Week

**Week 4 — Analytical and Non-Relational Data Systems**

- 👉 OLTP vs. OLAP, and star schemas
- 👉 Dimensional modeling
- 👉 Relational vs. object-oriented and document models

---

# 🙌 End of Part 4

Questions?
