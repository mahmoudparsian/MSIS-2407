# Week 1 — `Week1_dataset.csv`

A five-row flat export of an online shop's orders — one row per **order
line** (one product within one order). It is deliberately **not** a good
design: it mixes several entities in one table, so the same facts repeat
across rows. Small enough to check every answer by eye.

| Column | Type | Notes |
|---|---|---|
| `order_id` | integer | 1–3; repeats when an order has several products |
| `customer_name` | text | 3 customers (Alice, Bob, Charlie) |
| `product_name` | text | 5 products (Laptop, Mouse, Phone, Tablet, Headphones) |
| `price` | integer | unit price, 25–1,200 |
| `quantity` | integer | 1–3 |
| `order_date` | date | 2025-01-01 to 2025-01-03 |

## What to look for

- Which columns describe a **customer**, which an **order**, and which a
  **product**? Which column belongs to none of them alone?
- Which facts are stored more than once?
- If the Laptop's price changes, how many rows must change — and what happens
  if one is missed?
- Orders and products are related many-to-many. Where is that relationship
  hiding in a single flat table?

## Used in

[`Week1_Notebook_marimo.py`](Week1_Notebook_marimo.py) — Steps 1–5 derive the
entities, candidate keys, and tables from this file, and Step 7 demonstrates the
update anomaly it invites.

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
