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
    # 📘 MSIS-2407 — Week 1 Notebook
    ## Conceptual Modeling: From a Flat File to Entities, Keys and EER

    Companion to `data_modeling_02_explained.md`. We start from the five-row flat
    file `Week1_dataset.csv` (an online shop's order export) and work out — with
    SQL as the evidence — the entities, keys, cardinality, participation, and one
    Enhanced ER (EER) specialization hiding in it.

    | Step | Idea |
    |---|---|
    | 1 | the flat file, and what repeats in it |
    | 2 | entities and attributes |
    | 3 | candidate keys |
    | 4 | from ER to tables: PK, FK, and the M:N bridge |
    | 5 | cardinality and participation |
    | 6 | EER: a superclass and its subclasses |
    | 7 | why the flat design hurts: an update anomaly |

    Every query cell checks the numbers this text quotes. (Structured vs.
    semi-structured vs. unstructured data has its own notebook:
    `data_modeling_03_demo_marimo.py`.)
    """)
    return


@app.cell
def _(mo):
    import duckdb
    import pandas as pd

    con = duckdb.connect()
    data_file = mo.notebook_dir() / "Week1_dataset.csv"
    return con, data_file, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 1 — The flat file

    One row per **order line**: which customer bought which product, at what
    price, how many, and when.
    """)
    return


@app.cell
def _(con, data_file):
    con.execute(f"""
    CREATE OR REPLACE TABLE orders_flat AS
    SELECT * FROM read_csv('{data_file.as_posix()}')
    """)
    flat = con.execute("SELECT * FROM orders_flat ORDER BY order_id, product_name").df()
    assert len(flat) == 5
    flat
    return (flat,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Read it slowly. **Alice** and **Charlie** each appear twice, because each of
    their orders has two lines. **Order 1** appears twice for the same reason. The
    file mixes three different *things* in one row — that is the first sign that
    it holds several entities.
    """)
    return


@app.cell
def _(con, flat):
    _repeats = con.execute("""
    SELECT customer_name, count(*) AS rows_in_file
    FROM orders_flat
    GROUP BY customer_name
    ORDER BY customer_name
    """).df()
    assert _repeats["rows_in_file"].tolist() == [2, 1, 2] and len(flat) == 5
    _repeats
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 2 — Entities and attributes

    Ask of each column: *what thing is this a fact about?*

    | Column | Describes | Entity |
    |---|---|---|
    | `customer_name` | the person buying | **Customer** |
    | `order_id`, `order_date` | one purchase event | **Order** |
    | `product_name`, `price` | an item for sale | **Product** |
    | `quantity` | how many of *this product* in *this order* | the **Order ↔ Product** relationship |

    `quantity` belongs to neither Order nor Product alone — it describes the
    pairing. That is the clue that Order and Product are many-to-many.
    """)
    return


@app.cell
def _(con, flat):
    _entities = con.execute("""
    SELECT count(DISTINCT customer_name) AS customers,
           count(DISTINCT order_id)      AS orders,
           count(DISTINCT product_name)  AS products,
           count(*)                      AS order_lines
    FROM orders_flat
    """).df()
    assert _entities.iloc[0].tolist() == [3, 3, 5, 5] and len(flat) == 5
    _entities
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 3 — Candidate keys

    A **key** identifies exactly one row. Test it: a column (or set of columns)
    is a candidate key of this file only if it has as many distinct values as
    there are rows.
    """)
    return


@app.cell
def _(con, flat):
    _keys = con.execute("""
    SELECT count(*)                                        AS file_rows,
           count(DISTINCT order_id)                        AS distinct_order_id,
           count(DISTINCT order_id || '|' || product_name) AS distinct_order_product
    FROM orders_flat
    """).df()
    assert _keys.iloc[0].tolist() == [5, 3, 5] and len(flat) == 5
    _keys
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `order_id` alone is **not** a key of the flat file (3 values, 5 rows), but the
    pair **(order_id, product_name)** is — the composite key of an *order line*.

    Note what this test can and cannot prove: five rows can show that a column is
    *not* a key, but they can never prove that it *is* one. Uniqueness is a
    **business rule** ("a product appears at most once per order"), not a pattern
    in a sample.

    Names are also poor keys: two customers can share a name, and a product can be
    renamed. So the tables below get **surrogate** integer keys.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 4 — From ER to tables

    ```
    CUSTOMER ──< ORDER >──< ORDER_ITEM >── PRODUCT
    ```

    * each entity becomes a table with a primary key
    * the 1:M relationship Customer → Order becomes a **foreign key** in `orders`
    * the M:N relationship Order ↔ Product becomes a **bridge table**,
      `order_item`, whose key is the pair and which carries `quantity`

    We also add one order the file does not have — Alice's second order — so the
    "many" sides become visible, and one product nobody has bought yet.
    """)
    return


@app.cell
def _(con, flat):
    con.execute("""
    DROP TABLE IF EXISTS order_item;
    DROP TABLE IF EXISTS card_payment;
    DROP TABLE IF EXISTS bank_transfer_payment;
    DROP TABLE IF EXISTS payment;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS product;
    DROP TABLE IF EXISTS customer;

    CREATE TABLE customer (
        customer_id INTEGER PRIMARY KEY,
        name        VARCHAR NOT NULL
    );
    CREATE TABLE product (
        product_id INTEGER PRIMARY KEY,
        name       VARCHAR NOT NULL UNIQUE,
        price      DECIMAL(10,2) NOT NULL CHECK (price >= 0)
    );
    CREATE TABLE orders (
        order_id    INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customer(customer_id),
        order_date  DATE    NOT NULL
    );
    CREATE TABLE order_item (
        order_id   INTEGER NOT NULL REFERENCES orders(order_id),
        product_id INTEGER NOT NULL REFERENCES product(product_id),
        quantity   INTEGER NOT NULL CHECK (quantity > 0),
        PRIMARY KEY (order_id, product_id)
    );

    INSERT INTO customer
    SELECT row_number() OVER (ORDER BY customer_name), customer_name
    FROM (SELECT DISTINCT customer_name FROM orders_flat);

    INSERT INTO product
    SELECT row_number() OVER (ORDER BY product_name), product_name, price
    FROM (SELECT DISTINCT product_name, price FROM orders_flat);

    INSERT INTO orders
    SELECT DISTINCT f.order_id, c.customer_id, f.order_date
    FROM orders_flat f JOIN customer c ON c.name = f.customer_name;

    INSERT INTO order_item
    SELECT f.order_id, p.product_id, f.quantity
    FROM orders_flat f JOIN product p ON p.name = f.product_name;

    -- not in the file: Alice's second order, and a product with no sales yet
    INSERT INTO orders     VALUES (4, 1, DATE '2025-01-04');
    INSERT INTO order_item VALUES (4, (SELECT product_id FROM product WHERE name = 'Mouse'), 1);
    INSERT INTO product    VALUES (6, 'Keyboard', 45);
    """)
    table_sizes = con.execute("""
    SELECT (SELECT count(*) FROM customer)   AS customer,
           (SELECT count(*) FROM orders)     AS orders,
           (SELECT count(*) FROM product)    AS product,
           (SELECT count(*) FROM order_item) AS order_item
    """).df()
    assert table_sizes.iloc[0].tolist() == [3, 4, 6, 6] and len(flat) == 5
    table_sizes
    return (table_sizes,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nothing was lost: joining the four tables back together reproduces every line
    of the flat file (plus Alice's new order).
    """)
    return


@app.cell
def _(con, table_sizes):
    _rebuilt = con.execute("""
    SELECT o.order_id, c.name AS customer_name, p.name AS product_name,
           p.price, oi.quantity, o.order_date
    FROM order_item oi
    JOIN orders   o ON o.order_id    = oi.order_id
    JOIN customer c ON c.customer_id = o.customer_id
    JOIN product  p ON p.product_id  = oi.product_id
    ORDER BY o.order_id, product_name
    """).df()
    assert len(_rebuilt) == 6 and len(table_sizes) == 1
    _rebuilt
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 5 — Cardinality and participation

    **Cardinality** — the maximum: *how many* on each side?
    **Participation** — the minimum: *must* each instance take part?

    | Relationship | Cardinality | Participation |
    |---|---|---|
    | Customer places Order | 1 : M | every order **must** have a customer; a customer **may** have no orders |
    | Order contains Product | M : N | an order **must** have at least one line; a product **may** never be sold |

    The query shows the "many" sides in the data:
    """)
    return


@app.cell
def _(con, table_sizes):
    _card = con.execute("""
    SELECT
      (SELECT max(n) FROM (SELECT count(*) AS n FROM orders GROUP BY customer_id))
          AS max_orders_per_customer,
      (SELECT max(n) FROM (SELECT count(*) AS n FROM order_item GROUP BY order_id))
          AS max_products_per_order,
      (SELECT max(n) FROM (SELECT count(*) AS n FROM order_item GROUP BY product_id))
          AS max_orders_per_product,
      (SELECT count(*) FROM product p
        WHERE NOT EXISTS (SELECT 1 FROM order_item oi WHERE oi.product_id = p.product_id))
          AS products_never_sold
    """).df()
    assert _card.iloc[0].tolist() == [2, 2, 2, 1] and len(table_sizes) == 1
    _card
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The database **enforces** the mandatory side of Customer → Order:
    `orders.customer_id` is `NOT NULL` and a foreign key. An order with no
    customer, or with a customer who does not exist, is rejected:
    """)
    return


@app.cell
def _(con, pd, table_sizes):
    _attempts = []
    for _label, _sql in [
        ("order with no customer",      "INSERT INTO orders VALUES (90, NULL, DATE '2025-02-01')"),
        ("order for customer 99",       "INSERT INTO orders VALUES (91, 99,   DATE '2025-02-01')"),
    ]:
        try:
            con.execute(_sql)
            _attempts.append((_label, "accepted"))
        except Exception as _e:
            _attempts.append((_label, "rejected: " + type(_e).__name__))
    _result = pd.DataFrame(_attempts, columns=["attempt", "outcome"])
    assert all(_result["outcome"].str.startswith("rejected")) and len(table_sizes) == 1
    _result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The *optional* sides need no constraint at all — a customer with no orders,
    or the unsold Keyboard, is simply a row nobody references. ("An order must
    have at least one line" is a rule a plain FK cannot enforce; it needs a check
    in the application or a periodic query.)

    ---
    ## Step 6 — EER: specialization

    Payments come in two kinds that need **different attributes**: a card payment
    has `card_last4` and `auth_code`; a bank transfer has `bank_name` and `iban`.

    ```
                     PAYMENT
              payment_id, order_id, amount
                        │
                        ○  (disjoint, total)
              ┌─────────┴─────────┐
         CARD_PAYMENT        BANK_TRANSFER_PAYMENT
         card_last4          bank_name
         auth_code           iban
    ```

    One common mapping: a **superclass table** with the shared attributes and a
    `kind` discriminator, plus one **subclass table** per kind whose primary key
    is also a foreign key to the superclass.
    """)
    return


@app.cell
def _(con, table_sizes):
    con.execute("""
    DROP TABLE IF EXISTS card_payment;
    DROP TABLE IF EXISTS bank_transfer_payment;
    DROP TABLE IF EXISTS payment;

    CREATE TABLE payment (
        payment_id INTEGER PRIMARY KEY,
        order_id   INTEGER NOT NULL REFERENCES orders(order_id),
        amount     DECIMAL(10,2) NOT NULL CHECK (amount > 0),
        kind       VARCHAR NOT NULL CHECK (kind IN ('card', 'bank_transfer'))
    );
    CREATE TABLE card_payment (
        payment_id INTEGER PRIMARY KEY REFERENCES payment(payment_id),
        card_last4 VARCHAR NOT NULL CHECK (length(card_last4) = 4),
        auth_code  VARCHAR NOT NULL
    );
    CREATE TABLE bank_transfer_payment (
        payment_id INTEGER PRIMARY KEY REFERENCES payment(payment_id),
        bank_name  VARCHAR NOT NULL,
        iban       VARCHAR NOT NULL
    );

    -- each payment pays its order's total: sum(price * quantity)
    INSERT INTO payment
    SELECT oi.order_id, oi.order_id, sum(p.price * oi.quantity),
           CASE WHEN oi.order_id = 2 THEN 'bank_transfer' ELSE 'card' END
    FROM order_item oi JOIN product p USING (product_id)
    GROUP BY oi.order_id;

    INSERT INTO card_payment VALUES
        (1, '4242', 'A1B2'), (3, '1881', 'C3D4'), (4, '4242', 'E5F6');
    INSERT INTO bank_transfer_payment VALUES
        (2, 'Bay Credit Union', 'US00BAYC0000123456');
    """)
    payments = con.execute("""
    SELECT p.payment_id, p.order_id, p.amount, p.kind,
           c.card_last4, b.bank_name
    FROM payment p
    LEFT JOIN card_payment          c USING (payment_id)
    LEFT JOIN bank_transfer_payment b USING (payment_id)
    ORDER BY p.payment_id
    """).df()
    assert [float(a) for a in payments["amount"]] == [1250.0, 800.0, 1050.0, 25.0]
    payments
    return (payments,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Each subclass row **inherits** `order_id` and `amount` through the join on
    `payment_id`.

    The two EER constraints — **disjoint** (no payment is both kinds) and
    **total** (every payment is one of them) — span three tables, so no single
    column constraint can enforce them. Check them with a query; it must return
    zero violations:
    """)
    return


@app.cell
def _(con, payments):
    _eer = con.execute("""
    WITH memberships AS (
      SELECT p.payment_id, p.kind,
             (c.payment_id IS NOT NULL)::INTEGER AS in_card,
             (b.payment_id IS NOT NULL)::INTEGER AS in_bank
      FROM payment p
      LEFT JOIN card_payment          c USING (payment_id)
      LEFT JOIN bank_transfer_payment b USING (payment_id)
    )
    SELECT count(*) FILTER (WHERE in_card + in_bank = 0) AS not_classified,       -- total
           count(*) FILTER (WHERE in_card + in_bank > 1) AS in_both_subclasses,   -- disjoint
           count(*) FILTER (WHERE (kind = 'card') <> (in_card = 1))
                                                       AS kind_disagrees
    FROM memberships
    """).df()
    assert _eer.iloc[0].tolist() == [0, 0, 0] and len(payments) == 4
    _eer
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 7 — Why the flat design hurts: an update anomaly

    Alice changes her name to *Alice Smith*. In the flat file her name is stored
    once **per order line**; a careless update that touches only one line leaves
    the file contradicting itself. In the normalized design the name is stored
    once.
    """)
    return


@app.cell
def _(con, payments):
    con.execute("""
    CREATE OR REPLACE TABLE flat_copy AS SELECT * FROM orders_flat;
    UPDATE flat_copy SET customer_name = 'Alice Smith'
    WHERE order_id = 1 AND product_name = 'Laptop';      -- one line, not both

    CREATE OR REPLACE TABLE customer_copy AS SELECT * FROM customer;
    UPDATE customer_copy SET name = 'Alice Smith' WHERE customer_id = 1;
    """)
    _anomaly = con.execute("""
    SELECT
      (SELECT count(DISTINCT customer_name) FROM flat_copy WHERE order_id = 1)
          AS names_for_order_1_flat,
      (SELECT count(*) FROM customer_copy WHERE name LIKE 'Alice%')
          AS alice_rows_normalized,
      (SELECT count(*) FROM customer_copy WHERE name = 'Alice')
          AS stale_alice_rows_normalized
    """).df()
    assert _anomaly.iloc[0].tolist() == [2, 1, 0] and len(payments) == 4
    _anomaly
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Order 1 now has **two** customer names in the flat file — which is right? The
    normalized `customer` table needed one `UPDATE` of one row, and every order
    sees the new name through the foreign key. Week 2 turns this observation into
    a method: functional dependencies and normal forms.

    ---
    ## 🧪 Try it yourself

    1. Add a `category` to products (Electronics, Accessories). Is it an
       attribute of `product`, or its own entity? What would make it one?
    2. Customers can now save several **shipping addresses**. Draw the new entity
       and its relationship to Customer — cardinality *and* participation.
    3. Add a third payment kind, *gift card* (`gift_card_code`). What changes in
       the EER diagram and in the tables? Re-run the Step 6 check.
    """)
    return


if __name__ == "__main__":
    app.run()
