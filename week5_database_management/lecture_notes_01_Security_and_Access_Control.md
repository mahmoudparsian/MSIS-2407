---
marp: true
title: MSIS-2407 — Week 5 (Part 1)
subtitle: Security and Access Control
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

# 🔐 Week 5 — Security and Access Control

Weeks 1–4 asked *"is the data correct?"*

This week asks two harder questions:

* **who may see it?**
* **what happens when something goes wrong?**

> **Teaching order.** Part 1 (Session 9) covers who may see the data. Part 2
> (Session 10) covers what happens when something goes wrong.

---

# 🎯 The three questions of database security

| Question | Term | Example |
|---|---|---|
| Who are you? | **authentication** | password, SSO, certificate |
| What may you do? | **authorization** | `SELECT` yes, `DELETE` no |
| What did you do? | **audit** | who ran that `UPDATE`, and when |

Most conversations about "database security" are really about the second one.
The third is the one organizations discover they needed **after** an incident.

---

# 👥 Role-based access control (RBAC)

Do **not** grant permissions to people. Grant them to **roles**, and put people in
roles.

```sql
CREATE ROLE analyst;
GRANT SELECT ON sales TO analyst;
GRANT analyst TO maria;
```

Why it matters operationally:

* someone joins → one `GRANT`
* someone leaves → one `REVOKE`
* an auditor asks "who can read salaries?" → **one query**, not an interview

Per-user grants do not survive staff turnover. They drift, and nobody can say
what the current state is.

---

# 🧱 Least privilege

Grant the **minimum** needed to do the job, and nothing more.

| Role | Needs | Should NOT have |
|---|---|---|
| analyst | `SELECT` on reporting views | base tables, `DELETE` |
| loader | `INSERT`/`UPDATE` on staging | production `SELECT` on PII |
| auditor | `SELECT` on the audit log | any write |

The test: **if this account were compromised tomorrow, what could it do?**

An analyst account with `DROP TABLE` is not a permissions setting. It is an
incident waiting for a bad afternoon.

---

# 🪟 Views as a security boundary

A view can expose *some* rows and *some* columns of a table.

```sql
CREATE VIEW v_customer_marketing AS
SELECT customer_id, postal_code, segment      -- no name, no email
FROM customer;

GRANT SELECT ON v_customer_marketing TO marketing;
REVOKE ALL ON customer FROM marketing;
```

* **column-level** — leave the sensitive columns out of the `SELECT`
* **row-level** — put a `WHERE` in the view, or use a row-level security policy

⚠️ A view is only a boundary if the base table is **not** also readable.
Granting both is the most common mistake in this pattern.

---

# 🕵️ PII and three ways to protect it

| Treatment | What it does | Joinable? | Reversible? |
|---|---|---|---|
| **Redaction** | remove the value | no | no |
| **Tokenization** | replace with a stable hash | yes, consistently | only with the salt |
| **Generalization** | reduce precision (age → band) | partly | no |

Tokenization is the useful middle ground: analysts can still join and count, but
cannot read.

```sql
md5(national_id || :salt) AS national_id_token
```

---

# ⚠️ Removing the name is not anonymization

This is the part people get wrong.

Delete `full_name` and you have **de-identified** the data. You have not made it
anonymous.

Postal code + date of birth + gender is a **quasi-identifier**. In many
populations that combination is unique — so the record is re-identifiable by
anyone holding a second dataset.

---

# 📏 k-anonymity

A dataset is **k-anonymous** if every combination of quasi-identifiers appears at
least *k* times.

* k = 1 → someone is unique → re-identifiable
* k = 5 → each person hides among at least four others

The fix is **generalization**:

```
postal 90210      →  902XX
age 47            →  40-49
```

Raising k always costs analytical precision. That trade is a business decision,
not a technical one.

Measured hands-on in Session 9's Lab 1b, Task 2.

---

# 🦆 A note on DuckDB

DuckDB is an **embedded** engine. There are no user accounts, so `GRANT` and
`REVOKE` do not exist.

The lab therefore implements RBAC with **secure views plus a permissions table** —
the pattern you use whenever the engine's security model is weaker than your
requirement.

Be honest about the limit: that pattern restricts a *well-behaved client*.
Anyone holding the database file can read the base tables. Real enforcement needs
engine-level roles (Postgres, MySQL) or a server between the user and the data.

---

# 💉 The other attack surface: SQL injection

Access control is worthless if the application hands over an arbitrary query.

```python
# ☠️ vulnerable
f"SELECT * FROM booking WHERE name = '{user_input}'"

# ✅ safe
"SELECT * FROM booking WHERE name = ?", [user_input]
```

"We sanitize input" is **not** a defence. Escaping quotes does nothing to a
*numeric* injection point, where no quotes are involved.

Bind every parameter. Always. (Week 3, Lab 2b, Task 5 — and Session 9's Lab 1a, Task 4.)

---

# ✅ Check your understanding

1. Marketing needs to count customers by region but must never see names. Give two
   different technical answers, and say which you would ship.
2. An analyst account has `SELECT` on a masked view **and** on the base table.
   What is the effective permission?
3. Your dataset is k-anonymous at k = 3. A regulator asks for k = 20. What do you
   generalize next, and at what point does the data stop answering the question it
   was collected for?
4. Tokenizing with a single fixed salt keeps joins working. What attack does that
   permit which a per-record salt would not?

---

# 🙌 End of Week 5 (Part 1)

Next: **Part 2 — Backup, Recovery, Capacity and Governance.**

Labs (Session 9, `LABS/week5_lab1/`): **Lab 1a** — classification, role views,
masking, SQL injection, what an index costs, an audit trail; **Lab 1b** — secure
views, k-anonymity, index selectivity, capacity, and a restore drill.
