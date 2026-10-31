# Week 3 — `Week3_dataset.csv`

The order export from Weeks 1–2, now used as the **source file for a real
load**: it is landed, cast into typed tables with constraints, and validated.
Five rows, one per **order line**.

| Column | Type | Notes |
|---|---|---|
| `order_id` | integer | 1–3; repeats when an order has several products |
| `customer_name` | text | 3 customers |
| `customer_email` | text | one per customer — used to match rows to customers |
| `product_name` | text | 5 products |
| `price` | integer | unit price, 25–1,200 |
| `quantity` | integer | 1–3 |
| `order_date` | date | 2025-01-01 to 2025-01-03 |

**Control total:** `SUM(price × quantity)` = **4,425** — the number a correct
load must reproduce.

## How the notebook uses it

[`Week3_Notebook_marimo.py`](Week3_Notebook_marimo.py), Steps 1–5:

1. Land the file as text, then **append two broken rows** — the kind a real
   export contains.
2. Create a typed, constrained schema: `customer`, `product`, `orders`,
   `order_items`.
3. Cast with `TRY_CAST`, **quarantine** rows that fail, and load the rest.
4. **Validate** the load three ways — row counts, the control total, and a
   rebuild: joining the four tables back must reproduce the source exactly.
5. Reload the same file and confirm nothing is duplicated.

## What to look for

How do you *know* a load is correct? Counting rows is not enough — what else
must match?

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
