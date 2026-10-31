import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 📘 MSIS-2407 — Week 4 Notebook
    ## Analytical and Non-Relational Data Systems

    Companion to `lecture_notes_01_Dimensional_Modeling.md` and
    `lecture_notes_02_Relational_vs_Object_Oriented.md`. A small outdoor-gear
    retailer's **OLTP** database becomes a **star schema** — grain, surrogate
    keys, an unknown member, a Type 2 store dimension — and then one order is
    modeled three ways: relational, nested, and document.

    | Step | Idea |
    |---|---|
    | 1 | the OLTP source |
    | 2 | the grain — proved, not assumed |
    | 3 | dimensions: surrogate keys, unknown members, SCD Type 2 |
    | 4 | the fact table, loaded with an as-of join, and validated |
    | 5 | querying the star: categories, `ROLLUP`, history vs. today |
    | 6 | testing the Type 2 invariants |
    | 7 | additivity: which measures may you `SUM`? |
    | 8 | one order, three models |
    | 9 | what a flexible schema lets through |

    The data is built in code. Every query cell checks the numbers this text
    quotes.
    """)
    return


@app.cell
def _():
    import duckdb
    import pandas as pd

    con = duckdb.connect()
    return con, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 1 — The OLTP source

    Normalized for transactions: stores, products, orders, order lines. Two
    details matter later: store **S2 moved from the West region to the East on
    2025-03-01**, and one order line references a product code, `P-999`, that is
    not in the product table (a real feed always has one).
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE OR REPLACE TABLE src_store (
        store_id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, region VARCHAR NOT NULL);
    INSERT INTO src_store VALUES
        ('S1', 'Downtown', 'West'), ('S2', 'Harbor', 'East'), ('S3', 'Airport', 'East');

    CREATE OR REPLACE TABLE src_store_history (          -- S2 was West until 2025-02-28
        store_id VARCHAR, region VARCHAR, valid_from DATE, valid_to DATE);
    INSERT INTO src_store_history VALUES
        ('S2', 'West', DATE '1900-01-01', DATE '2025-02-28'),
        ('S2', 'East', DATE '2025-03-01', DATE '9999-12-31');

    CREATE OR REPLACE TABLE src_product (
        product_id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, category VARCHAR NOT NULL);
    INSERT INTO src_product VALUES
        ('P-100', 'Trail Shoe',   'Footwear'),
        ('P-101', 'Rain Jacket',  'Apparel'),
        ('P-102', 'Water Bottle', 'Accessories'),
        ('P-103', 'Wool Socks',   'Apparel');

    CREATE OR REPLACE TABLE src_order (
        order_id INTEGER PRIMARY KEY, order_date DATE NOT NULL, store_id VARCHAR NOT NULL);
    INSERT INTO src_order VALUES
        (1001, DATE '2025-01-15', 'S1'), (1002, DATE '2025-02-10', 'S2'),
        (1003, DATE '2025-02-20', 'S3'), (1004, DATE '2025-03-05', 'S2'),
        (1005, DATE '2025-04-12', 'S1'), (1006, DATE '2025-05-03', 'S2');

    CREATE OR REPLACE TABLE src_order_line (
        order_id INTEGER, product_id VARCHAR, qty INTEGER, unit_price DECIMAL(10,2),
        PRIMARY KEY (order_id, product_id));
    INSERT INTO src_order_line VALUES
        (1001, 'P-100', 1, 120), (1001, 'P-103', 2, 15),
        (1002, 'P-101', 1,  90), (1002, 'P-102', 3, 10),
        (1003, 'P-100', 2, 120),
        (1004, 'P-101', 2,  90), (1004, 'P-999', 1, 40),
        (1005, 'P-102', 1,  10), (1005, 'P-103', 4, 15),
        (1006, 'P-100', 1, 120), (1006, 'P-101', 1, 90);
    """)
    source_lines = con.execute("""
    SELECT o.order_id, o.order_date, o.store_id, l.product_id, l.qty, l.unit_price,
           l.qty * l.unit_price AS revenue
    FROM src_order o JOIN src_order_line l USING (order_id)
    ORDER BY o.order_id, l.product_id
    """).df()
    assert len(source_lines) == 11 and float(source_lines["revenue"].sum()) == 1010.0
    source_lines
    return (source_lines,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 2 — The grain

    > **One fact row per order line.**

    Write the grain first, then prove the source can support it: the candidate
    grain key must be unique, and no line may be lost on the way.
    """)
    return


@app.cell
def _(con, source_lines):
    _grain = con.execute("""
    SELECT count(*)                                    AS order_lines,
           count(DISTINCT order_id || '|' || product_id) AS distinct_grain_keys,
           count(DISTINCT order_id)                    AS orders
    FROM src_order_line
    """).df()
    assert _grain.iloc[0].tolist() == [11, 11, 6] and len(source_lines) == 11
    _grain
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    11 lines, 11 distinct grain keys — the grain holds. (At the coarser grain "one
    row per order", `product` could not be a dimension: an order has several.)

    ---
    ## Step 3 — Dimensions

    * **Surrogate keys** — the warehouse's own integers (`product_key`), not the
      source's codes (`product_id`).
    * **Unknown member** — key `-1` in every dimension, so an unmatched fact is
      kept and flagged instead of silently dropped.
    * **SCD Type 2** for stores — one row per *version*, with `valid_from`,
      `valid_to` and `is_current`, so last year's sales stay in last year's region.
    """)
    return


@app.cell
def _(con, source_lines):
    con.execute("""
    DROP TABLE IF EXISTS fact_sales;

    CREATE OR REPLACE TABLE dim_product AS
    SELECT -1 AS product_key, 'UNKNOWN' AS product_id, 'Unknown product' AS name,
           'Unknown' AS category
    UNION ALL
    SELECT row_number() OVER (ORDER BY product_id), product_id, name, category
    FROM src_product;

    CREATE OR REPLACE TABLE dim_store AS
    WITH versions AS (
      SELECT s.store_id, s.name,
             coalesce(h.region, s.region)               AS region,
             coalesce(h.valid_from, DATE '1900-01-01')  AS valid_from,
             coalesce(h.valid_to,   DATE '9999-12-31')  AS valid_to
      FROM src_store s LEFT JOIN src_store_history h USING (store_id))
    SELECT -1 AS store_key, 'UNKNOWN' AS store_id, 'Unknown store' AS name,
           'Unknown' AS region, DATE '1900-01-01' AS valid_from,
           DATE '9999-12-31' AS valid_to, true AS is_current
    UNION ALL
    SELECT row_number() OVER (ORDER BY store_id, valid_from), store_id, name, region,
           valid_from, valid_to, valid_to = DATE '9999-12-31'
    FROM versions;

    CREATE OR REPLACE TABLE dim_date AS
    SELECT (year(d) * 10000 + month(d) * 100 + day(d))::INTEGER AS date_key,
           d::DATE AS full_date, year(d) AS year, quarter(d) AS quarter,
           month(d) AS month, monthname(d) AS month_name
    FROM range(DATE '2025-01-01', DATE '2025-07-01', INTERVAL 1 DAY) t(d);
    """)
    dim_store_view = con.execute("SELECT * FROM dim_store ORDER BY store_key").df()
    _sizes = con.execute("""
    SELECT (SELECT count(*) FROM dim_product), (SELECT count(*) FROM dim_store),
           (SELECT count(*) FROM dim_date)
    """).fetchone()
    assert list(_sizes) == [5, 5, 181] and len(source_lines) == 11
    assert dim_store_view[dim_store_view["store_id"] == "S2"]["region"].tolist() == ["West", "East"]
    dim_store_view
    return (dim_store_view,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Store S2 has **two** rows — two versions — with different surrogate keys.

    ---
    ## Step 4 — The fact table

    Each order line looks up its keys. The store lookup is an **as-of join**: pick
    the store version that was valid *on the order date*. An unmatched product
    gets key `-1`, never `NULL`.
    """)
    return


@app.cell
def _(con, dim_store_view):
    con.execute("""
    CREATE OR REPLACE TABLE fact_sales AS
    SELECT d.date_key,
           coalesce(p.product_key, -1) AS product_key,
           coalesce(s.store_key,   -1) AS store_key,
           o.order_id,                                   -- degenerate dimension
           l.qty                       AS quantity,
           l.qty * l.unit_price        AS revenue
    FROM src_order_line l
    JOIN src_order o USING (order_id)
    JOIN dim_date  d ON d.full_date = o.order_date
    LEFT JOIN dim_product p ON p.product_id = l.product_id
    LEFT JOIN dim_store   s ON s.store_id = o.store_id
                           AND o.order_date BETWEEN s.valid_from AND s.valid_to
    """)
    fact_check = con.execute("""
    SELECT (SELECT count(*)     FROM src_order_line)                  AS source_lines,
           (SELECT count(*)     FROM fact_sales)                      AS fact_rows,
           (SELECT sum(qty * unit_price) FROM src_order_line)         AS source_revenue,
           (SELECT sum(revenue) FROM fact_sales)                      AS fact_revenue,
           (SELECT count(*)     FROM fact_sales WHERE product_key = -1) AS unknown_product_rows
    """).df()
    _f = fact_check.iloc[0]
    assert (_f["source_lines"], _f["fact_rows"], _f["unknown_product_rows"]) == (11, 11, 1)
    assert float(_f["source_revenue"]) == float(_f["fact_revenue"]) == 1010.0
    assert len(dim_store_view) == 5
    fact_check
    return (fact_check,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Every line arrived and the revenue reconciles to the cent. Here is why the
    unknown member matters — the same load with a `NULL` key instead of `-1`
    quietly loses a sale in every inner join:
    """)
    return


@app.cell
def _(con, fact_check):
    _null_key = con.execute("""
    WITH fact_with_nulls AS (
      SELECT CASE WHEN product_key = -1 THEN NULL ELSE product_key END AS product_key,
             revenue
      FROM fact_sales)
    SELECT (SELECT sum(f.revenue) FROM fact_sales f
              JOIN dim_product p USING (product_key))     AS revenue_with_unknown_member,
           (SELECT sum(f.revenue) FROM fact_with_nulls f
              JOIN dim_product p USING (product_key))     AS revenue_with_null_key
    """).df()
    assert [float(x) for x in _null_key.iloc[0]] == [1010.0, 970.0] and len(fact_check) == 1
    _null_key
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    $40 vanished, and nothing raised an error.

    ---
    ## Step 5 — Querying the star

    Every question is the same shape: join the fact to the dimensions you need,
    group by their attributes.
    """)
    return


@app.cell
def _(con, fact_check):
    by_category = con.execute("""
    SELECT p.category, sum(f.quantity) AS units, sum(f.revenue) AS revenue
    FROM fact_sales f JOIN dim_product p USING (product_key)
    GROUP BY p.category ORDER BY revenue DESC, p.category
    """).df()
    assert by_category["category"].tolist() == ["Footwear", "Apparel", "Accessories", "Unknown"]
    assert [float(x) for x in by_category["revenue"]] == [480.0, 450.0, 40.0, 40.0]
    assert len(fact_check) == 1
    by_category
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `ROLLUP` adds subtotals in one query — each quarter, and a grand total. A
    `NULL` in a grouping column marks a subtotal row:
    """)
    return


@app.cell
def _(con, fact_check):
    rollup = con.execute("""
    SELECT d.quarter, s.region, sum(f.revenue) AS revenue
    FROM fact_sales f
    JOIN dim_date  d USING (date_key)
    JOIN dim_store s USING (store_key)
    GROUP BY ROLLUP (d.quarter, s.region)
    ORDER BY d.quarter NULLS LAST, s.region NULLS LAST
    """).df()
    assert len(rollup) == 7 and float(rollup["revenue"].iloc[-1]) == 1010.0
    assert len(fact_check) == 1
    rollup
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Why Type 2 is worth the trouble.** "Revenue by region" has two honest
    answers. *As it was* uses the store version on the fact row. *As it is now*
    maps every sale to the store's current region — S2's February sale moves
    from West to East:
    """)
    return


@app.cell
def _(con, fact_check):
    history_vs_now = con.execute("""
    SELECT s.region AS region,
           sum(f.revenue)                                         AS revenue_as_it_was,
           (SELECT sum(f2.revenue) FROM fact_sales f2
              JOIN dim_store v  ON v.store_key = f2.store_key
              JOIN dim_store cur ON cur.store_id = v.store_id AND cur.is_current
             WHERE cur.region = s.region)                         AS revenue_as_it_is_now
    FROM fact_sales f JOIN dim_store s USING (store_key)
    GROUP BY s.region ORDER BY s.region
    """).df()
    assert history_vs_now["region"].tolist() == ["East", "West"]
    assert [float(x) for x in history_vs_now["revenue_as_it_was"]] == [670.0, 340.0]
    assert [float(x) for x in history_vs_now["revenue_as_it_is_now"]] == [790.0, 220.0]
    assert len(fact_check) == 1
    history_vs_now
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Both totals are 1010; the split differs by S2's $120 February sale. A
    Type 1 dimension (overwrite) could only ever give the second answer.

    ---
    ## Step 6 — Testing the Type 2 invariants

    A Type 2 dimension is only correct if, per business key:

    1. exactly **one** current row
    2. **no overlapping** validity intervals — an overlap double-counts facts
    3. **no gaps** — a gap drops them
    """)
    return


@app.cell
def _(con, dim_store_view):
    _scd = con.execute("""
    WITH s AS (SELECT * FROM dim_store WHERE store_key <> -1)
    SELECT
      (SELECT count(*) FROM (SELECT store_id FROM s GROUP BY store_id
                              HAVING count(*) FILTER (WHERE is_current) <> 1))
          AS keys_without_one_current_row,
      (SELECT count(*) FROM s a JOIN s b
              ON a.store_id = b.store_id AND a.store_key < b.store_key
             AND a.valid_from <= b.valid_to AND b.valid_from <= a.valid_to)
          AS overlapping_pairs,
      (SELECT count(*) FROM (
          SELECT valid_to, lead(valid_from) OVER (PARTITION BY store_id ORDER BY valid_from) AS next_from
          FROM s) WHERE next_from IS NOT NULL AND next_from <> valid_to + 1)
          AS gaps
    """).df()
    assert _scd.iloc[0].tolist() == [0, 0, 0] and len(dim_store_view) == 5
    _scd
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 7 — Additivity

    `quantity` and `revenue` are **additive**: summing them across any dimension
    means something. `unit_price` is **non-additive**: the sum of prices is not a
    price. Derive a ratio *after* summing, never by summing ratios:
    """)
    return


@app.cell
def _(con, fact_check):
    _additivity = con.execute("""
    SELECT (SELECT sum(unit_price)           FROM src_order_line) AS sum_of_unit_prices_meaningless,
           (SELECT round(avg(unit_price), 2) FROM src_order_line) AS avg_of_unit_prices_misleading,
           (SELECT round(sum(revenue) / sum(quantity), 2) FROM fact_sales)
                                                                   AS revenue_per_unit_correct
    """).df()
    assert [float(x) for x in _additivity.iloc[0]] == [720.0, 65.45, 53.16]
    assert len(fact_check) == 1
    _additivity
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The average *price per line* (65.45) is not the average price *per unit sold*
    (53.16): lines with more units must weigh more.

    ---
    ## Step 8 — One order, three models

    The same orders, stored the three ways from Part 2:

    | Model | Shape |
    |---|---|
    | **relational** | `src_order` + `src_order_line` (what we have) |
    | **object-relational (nested)** | one row per order; `lines` is a `LIST` of `STRUCT`s |
    | **document** | one `JSON` value per order |
    """)
    return


@app.cell
def _(con, fact_check):
    con.execute("""
    CREATE OR REPLACE TABLE order_nested AS
    SELECT o.order_id, o.order_date, o.store_id,
           list({'sku': l.product_id, 'qty': l.qty, 'price': l.unit_price}
                ORDER BY l.product_id) AS lines
    FROM src_order o JOIN src_order_line l USING (order_id)
    GROUP BY o.order_id, o.order_date, o.store_id;

    CREATE OR REPLACE TABLE order_doc AS
    SELECT order_id,
           to_json({'order_id': order_id, 'order_date': order_date,
                    'store_id': store_id, 'lines': lines}) AS doc
    FROM order_nested;
    """)
    one_order = con.execute("""
    SELECT 'relational' AS model, count(*) AS rows_read
      FROM src_order o JOIN src_order_line l USING (order_id) WHERE order_id = 1001
    UNION ALL
    SELECT 'nested', count(*) FROM order_nested WHERE order_id = 1001
    UNION ALL
    SELECT 'document', count(*) FROM order_doc WHERE order_id = 1001
    """).df()
    assert one_order["rows_read"].tolist() == [2, 1, 1] and len(fact_check) == 1
    one_order
    return (one_order,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Reading one whole order** favors the nested and document models: one row,
    no join. Now a question that cuts **across** orders — units sold per product.
    Relational answers it with a plain `GROUP BY`; the other two must first take
    the nesting apart with `UNNEST`:
    """)
    return


@app.cell
def _(con, one_order):
    _relational = con.execute("""
    SELECT product_id AS sku, sum(qty) AS units FROM src_order_line
    GROUP BY sku ORDER BY sku""").df()
    _nested = con.execute("""
    SELECT l.sku, sum(l.qty) AS units
    FROM order_nested, UNNEST(lines) AS t(l)
    GROUP BY l.sku ORDER BY l.sku""").df()
    _document = con.execute("""
    SELECT l->>'sku' AS sku, sum((l->>'qty')::INTEGER) AS units
    FROM order_doc, UNNEST(json_extract(doc, '$.lines[*]')) AS t(l)
    GROUP BY sku ORDER BY sku""").df()
    assert _relational["units"].tolist() == [4, 4, 4, 6, 1]
    assert _relational.equals(_nested.astype(_relational.dtypes))
    assert _relational.equals(_document.astype(_relational.dtypes))
    assert len(one_order) == 3
    _document
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Same answer, three ways. The trade is always **locality versus flexibility
    of access**: nesting makes the aggregate cheap to read and cross-cutting
    questions more work.

    ---
    ## Step 9 — What a flexible schema lets through

    A new app version starts sending `qty` as a **string**. The relational table
    would reject it (`qty INTEGER`). The document store accepts it — and the
    problem surfaces later, in someone's query:
    """)
    return


@app.cell
def _(con, one_order):
    con.execute("""
    CREATE OR REPLACE TABLE order_doc_v2 AS SELECT * FROM order_doc;
    INSERT INTO order_doc_v2 VALUES
      (1007, '{"order_id": 1007, "order_date": "2025-06-01", "store_id": "S3",
               "lines": [{"sku": "P-100", "qty": "3", "price": 120}]}');
    """)
    qty_types = con.execute("""
    SELECT json_type(l->'qty') AS qty_json_type, count(*) AS lines
    FROM order_doc_v2, UNNEST(json_extract(doc, '$.lines[*]')) AS t(l)
    GROUP BY qty_json_type ORDER BY qty_json_type
    """).df()
    assert qty_types["qty_json_type"].tolist() == ["UBIGINT", "VARCHAR"]
    assert qty_types["lines"].tolist() == [11, 1] and len(one_order) == 3
    qty_types
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    One line now has a different type for the same field. Queries that cast
    (`(l->>'qty')::INTEGER`) still work; a query comparing the raw JSON value
    against a number would silently treat it differently. **Schema-on-read moves
    validation from the database to every reader.** That is why the warehouse
    side of a real system is relational: documents for the application, a typed
    star for analysis.

    ---
    ## 🧪 Try it yourself

    1. Store S1 moves to the East region on 2025-05-01. Close its current
       `dim_store` row, add a new version, reload `fact_sales`, and re-run
       Steps 5 and 6.
    2. Add a `dim_customer` (some orders with no customer → which key?). What
       is the grain now — does it change?
    3. In Step 8, ask a question that favors the nested model: "the lines of
       order 1004". Write it for all three models and count the joins.
    """)
    return


if __name__ == "__main__":
    app.run()
