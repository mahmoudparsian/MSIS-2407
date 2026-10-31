# Week 3 — `Week3_orders_dataset.csv`

50,000 synthetic orders, one row each.

| Column | Type | Notes |
|---|---|---|
| `order_id` | integer | unique, 0–49,999 — the primary key |
| `customer_id` | integer | 1–5,000 (5,000 distinct customers) |
| `amount` | integer | 10–2,000; total **50,048,888** |
| `country` | text | Canada, Germany, UK, USA |
| `product` | text | four products |

## Used in

`Week3_Notebook_marimo.py`, Step 7 — load into a typed table with a primary key,
then validate the load: row count (50,000) and control total (50,048,888) against
the file.

## What it is *not* good for

Index timing. At 50,000 rows DuckDB filters the whole table in well under a
millisecond with or without an index, so there is nothing to measure. The notebook
times indexes on 2,000,000 generated rows instead (Step 8) — and even there, in a
columnar engine with zone maps, the honest finding is often "the index barely
helps". Measure; don't assume.

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
