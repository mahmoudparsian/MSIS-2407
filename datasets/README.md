# Datasets

[← Course home](../README.md) · **Datasets**

Reference datasets for **self-study and further practice**. No lab, notebook, or
the Final Exam depends on them — each week's notebook builds or ships its own
data. Use these when you want a larger, realistic dataset to model, load,
normalize, or query.

> **Load the `.csv` files.** The `.sql` files beside some CSVs are raw,
> insert-only exports (no `CREATE TABLE`, and dates written in a Python format),
> so they cannot be loaded as-is. The CSVs are the source of truth.

---

## At a Glance

| Folder | What it is | CSV size | Good for |
|---|---|---:|---|
| [`oltp_database/`](oltp_database/) | A retail business in **7 related tables** (100,000 orders, 2021–2024) | 23 MB | Weeks 2–3: normalization, keys and constraints, loading and validating data |
| [`warehouse_star_schema/`](warehouse_star_schema/) | A sales **fact table** at order-line grain | 10 MB | Week 4: dimensional modeling and star schemas |
| [`medallion_architecture/`](medallion_architecture/) | The same order lines as **bronze → silver → gold** layers | 25 MB | Week 4: data-platform layers and data quality |
| [`samples/`](samples/) | 50-row samples of three OLTP tables | < 1 MB | Previewing columns before loading the full tables |
| [`week1_single_table/`](week1_single_table/) | One flat `sales` table, 200 rows | < 1 MB | Week 1: spotting entities in a flat file |
| [`week2_relational/`](week2_relational/) | Small `customers`, `orders`, `products` | < 1 MB | Week 2: a quick relational schema to practice on |

---

## `oltp_database/` — the retail business

| Table | Rows | Columns |
|---|---:|---|
| `customers` | 1,000 | `customer_id`, `gender`, `country`, `segment`, `signup_date` |
| `orders` | 100,000 | `order_id`, `customer_id`, `store_id`, `order_date` |
| `order_items` | 300,000 | `order_item_id`, `order_id`, `product_id`, `quantity`, `category`, `price`, `sales_amount` |
| `products` | 2,000 | `product_id`, `category`, `price` |
| `payments` | 100,000 | `payment_id`, `order_id`, `payment_method`, `payment_date`, `payment_amount` |
| `shipments` | 100,000 | `shipment_id`, `order_id`, `carrier`, `shipment_date`, `delivery_date` |
| `stores` | 50 | `store_id`, `store_type`, `country` |

Orders run from 2021-01-01 to 2024-12-31. **Exercise:** `order_items` repeats
`category` and `price` from `products` — which normal form does that break, and
is it a mistake or a deliberate price-at-time-of-sale?

`reset_mysql.sql` and `verify_dataset.sql` are two small helpers for a MySQL
copy of the four core tables: the first drops them, the second counts their rows.

## `warehouse_star_schema/` — a fact table

`fact_sales.csv`: 300,000 rows, **one row per order line** — `order_date`,
`customer_id`, `store_id`, `product_id`, `quantity`, `sales_amount`. Build the
dimensions yourself from `oltp_database/` (customers, stores, products, a date
dimension) and you have a complete star schema.

## `medallion_architecture/` — bronze, silver, gold

| Layer | File | Rows | What changed |
|---|---|---:|---|
| Bronze | `bronze_orders.csv` | 300,000 | Raw order lines as they landed — **6,000 rows have `price = -1.00`** |
| Silver | `silver_orders.csv` | 294,000 | Cleaned: exactly those 6,000 invalid rows removed |
| Gold | `gold_product_sales.csv` | 2,000 | Business-ready: `total_sales` and `total_quantity` per product, from silver |

**Try it:** rebuild silver from bronze with a data-quality rule, then gold from
silver, and check your gold matches the file exactly. Then compute gold from
*bronze* instead — how many of the 2,000 products get a wrong total?

---

## Loading Into DuckDB

From the repository's top folder:

```python
import duckdb

con = duckdb.connect()          # or duckdb.connect("retail.duckdb") to keep it
for t in ["customers", "orders", "order_items", "products",
          "payments", "shipments", "stores"]:
    con.execute(f"CREATE TABLE {t} AS "
                f"SELECT * FROM read_csv('datasets/oltp_database/{t}.csv')")

con.sql("SELECT COUNT(*) FROM orders").show()     # 100,000
```

`read_csv` detects column names and types; for production-style loading with
declared types, keys, and constraints, follow Week 3's notes and notebook.

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
