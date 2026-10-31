# Week 2 — `Week2_dataset.csv`

The Week 1 order export, widened with two more columns — `customer_email` and
`category` — so it contains every kind of dependency that normalization
removes. Five rows, one per **order line**.

| Column | Type | Notes |
|---|---|---|
| `order_id` | integer | 1–3; repeats when an order has several products |
| `customer_name` | text | 3 customers |
| `customer_email` | text | one per customer |
| `product_name` | text | 5 products |
| `category` | text | a single value (Electronics) in this sample |
| `price` | integer | unit price, 25–1,200 |
| `quantity` | integer | 1–3 |
| `order_date` | date | 2025-01-01 to 2025-01-03 |

The key of the table is **(`order_id`, `product_name`)** — one row per product
per order.

## What to look for

- Which columns depend on only **part** of the key? (2NF)
- Which column depends on another non-key column rather than on the key? (3NF)
- If a customer's email address changes, how many rows must be updated?
- After you split the table, can joining the pieces back reproduce the
  original rows exactly — no more, no fewer?

## Used in

[`Week2_Notebook_marimo.py`](Week2_Notebook_marimo.py) — Steps 1–6 test each
functional dependency with SQL, decompose the table to 3NF, and prove the
decomposition is lossless.

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
