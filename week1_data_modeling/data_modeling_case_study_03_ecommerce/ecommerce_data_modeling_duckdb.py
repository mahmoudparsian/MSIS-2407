import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Relational Data Modeling — Hands-on DuckDB Notebook
    ## Case Study 3 of 3: NorthGate Marketplace (e-commerce)

    Companion notebook to **`relational_data_modeling_duckdb.md`** (the NorthGate
    Marketplace lecture deck). Every table below is built and populated with a single,
    pure-SQL `mo.sql()` cell, in dependency order (parent tables before the children that
    reference them), backed by marimo's embedded in-memory DuckDB connection.

    **Part 1** creates and populates the 15-table e-commerce schema.
    **Part 2** runs sample business-question queries against it.

    Edit any cell — change a price, delete a row, tighten a `CHECK` — and every
    downstream cell that reads that table reactively re-runs.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 1 — Schema & Sample Data
    """)
    return


@app.cell
def _(mo):
    # R1: customer_id is the surrogate PK; email is a unique alternate (natural) key.
    customers = mo.sql(
        f"""
        CREATE TABLE customers (
            customer_id  INTEGER PRIMARY KEY,
            first_name   VARCHAR NOT NULL,
            last_name    VARCHAR NOT NULL,
            email        VARCHAR NOT NULL UNIQUE,
            phone        VARCHAR,
            created_at   TIMESTAMP NOT NULL DEFAULT current_timestamp
        );

        INSERT INTO customers (customer_id, first_name, last_name, email, phone) VALUES
         (1,'Ana','Diaz','ana.diaz@example.com','408-555-0101'),
         (2,'Ben','Ochoa','ben.ochoa@example.com','510-555-0102'),
         (3,'Cy','Nguyen','cy.nguyen@example.com','650-555-0103'),
         (4,'Dana','Kim','dana.kim@example.com','925-555-0104'),
         (5,'Emma','Chen','emma.chen@example.com','415-555-0105');
        -- Emma Chen (5) deliberately has no orders yet: R3 says Order requires a
        -- Customer, but a Customer does not require any Orders (optional participation).

        SELECT * FROM customers;
        """
    )
    return


@app.cell
def _(mo):
    # R2: a customer has many addresses, each typed BILLING or SHIPPING (ENUM = controlled vocabulary).
    addresses = mo.sql(
        f"""
        CREATE TYPE address_type AS ENUM ('BILLING','SHIPPING');

        CREATE TABLE addresses (
            address_id   INTEGER PRIMARY KEY,
            customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
            addr_type    address_type NOT NULL,
            street       VARCHAR NOT NULL,
            city         VARCHAR NOT NULL,
            state_region VARCHAR,
            postal_code  VARCHAR,
            country      VARCHAR NOT NULL,
            is_default   BOOLEAN NOT NULL DEFAULT FALSE
        );

        INSERT INTO addresses VALUES
         (1,1,'SHIPPING','100 Market St','San Jose','CA','95113','USA', TRUE),
         (2,1,'BILLING','100 Market St','San Jose','CA','95113','USA', TRUE),
         (3,2,'SHIPPING','22 Lake Ave','Fremont','CA','94536','USA', TRUE),
         (4,2,'BILLING','22 Lake Ave','Fremont','CA','94536','USA', TRUE),
         (5,3,'SHIPPING','9 Bay Blvd','Oakland','CA','94607','USA', TRUE),
         (6,3,'BILLING','9 Bay Blvd','Oakland','CA','94607','USA', TRUE),
         (7,4,'SHIPPING','5 Ridge Rd','Walnut Creek','CA','94596','USA', TRUE),
         (8,4,'BILLING','5 Ridge Rd','Walnut Creek','CA','94596','USA', TRUE);

        SELECT * FROM addresses;
        """
    )
    return


@app.cell
def _(mo):
    # R5: categories nest via a self-referencing foreign key (Electronics -> Accessories).
    categories = mo.sql(
        f"""
        CREATE TABLE categories (
            category_id        INTEGER PRIMARY KEY,
            category_name      VARCHAR NOT NULL UNIQUE,
            parent_category_id INTEGER REFERENCES categories(category_id)
        );

        -- Root categories first (no parent), then children -- DuckDB validates a
        -- self-referencing FK against the table's state BEFORE the current statement,
        -- so a parent row must be committed in an earlier statement than its child.
        INSERT INTO categories VALUES
         (1,'Electronics', NULL),
         (3,'Fitness', NULL),
         (4,'Home & Kitchen', NULL);

        INSERT INTO categories VALUES
         (2,'Accessories', 1);

        SELECT * FROM categories;
        """
    )
    return


@app.cell
def _(mo):
    suppliers = mo.sql(
        f"""
        CREATE TABLE suppliers (
            supplier_id   INTEGER PRIMARY KEY,
            supplier_name VARCHAR NOT NULL,
            contact_email VARCHAR
        );

        INSERT INTO suppliers VALUES
         (1,'TechSource Inc','sales@techsource.example'),
         (2,'FitGear Co','orders@fitgear.example');

        SELECT * FROM suppliers;
        """
    )
    return


@app.cell
def _(mo):
    # R4: sku is a unique natural key; unit_price is protected by a CHECK (>= 0).
    products = mo.sql(
        f"""
        CREATE TABLE products (
            product_id   INTEGER PRIMARY KEY,
            sku          VARCHAR NOT NULL UNIQUE,
            product_name VARCHAR NOT NULL,
            category_id  INTEGER NOT NULL REFERENCES categories(category_id),
            unit_price   DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
            description  VARCHAR,
            is_active    BOOLEAN NOT NULL DEFAULT TRUE
        );

        INSERT INTO products (product_id, sku, product_name, category_id, unit_price, description) VALUES
         (1,'SKU-100','Wireless Mouse',2,24.99,'Ergonomic 2.4GHz wireless mouse'),
         (2,'SKU-210','USB-C Cable 2m',2,9.99,'Braided USB-C charging cable'),
         (3,'SKU-330','Yoga Mat',3,19.50,'6mm non-slip yoga mat'),
         (4,'SKU-410','French Press',4,29.00,'34oz stainless steel french press'),
         (5,'SKU-500','Mechanical Keyboard',1,89.00,'Hot-swappable mechanical keyboard');

        SELECT * FROM products;
        """
    )
    return


@app.cell
def _(mo):
    # R6: Product <-M:N-> Supplier, resolved with an associative entity carrying supply_price.
    # Wireless Mouse (product 1) is deliberately dual-sourced to demonstrate the M:N shape.
    product_suppliers = mo.sql(
        f"""
        CREATE TABLE product_suppliers (
            product_id   INTEGER NOT NULL REFERENCES products(product_id),
            supplier_id  INTEGER NOT NULL REFERENCES suppliers(supplier_id),
            supply_price DECIMAL(10,2) NOT NULL CHECK (supply_price >= 0),
            PRIMARY KEY (product_id, supplier_id)
        );

        INSERT INTO product_suppliers VALUES
         (1,1,14.00),
         (1,2,15.50),
         (2,1,4.50),
         (5,1,55.00),
         (3,2,11.00);

        SELECT * FROM product_suppliers;
        """
    )
    return


@app.cell
def _(mo):
    warehouses = mo.sql(
        f"""
        CREATE TABLE warehouses (
            warehouse_id   INTEGER PRIMARY KEY,
            warehouse_name VARCHAR NOT NULL,
            city           VARCHAR,
            country        VARCHAR
        );

        INSERT INTO warehouses VALUES
         (1,'West Coast DC','Stockton','USA'),
         (2,'East Coast DC','Columbus','USA');

        SELECT * FROM warehouses;
        """
    )
    return


@app.cell
def _(mo):
    # R8/R9: Product <-M:N-> Warehouse, with quantity_on_hand as an attribute of the
    # relationship itself (not of the product alone) -- another associative entity.
    inventory = mo.sql(
        f"""
        CREATE TABLE inventory (
            product_id       INTEGER NOT NULL REFERENCES products(product_id),
            warehouse_id     INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
            quantity_on_hand INTEGER NOT NULL CHECK (quantity_on_hand >= 0),
            PRIMARY KEY (product_id, warehouse_id)
        );

        INSERT INTO inventory VALUES
         (1,1,150),(1,2,80),(2,1,300),(2,2,120),
         (3,1,60),(4,1,45),(5,1,25),(5,2,10);

        SELECT * FROM inventory;
        """
    )
    return


@app.cell
def _(mo):
    # R10: order lifecycle is a controlled vocabulary (ENUM); three FKs point at customers/addresses.
    orders = mo.sql(
        f"""
        CREATE TYPE order_status AS ENUM ('PENDING','PAID','SHIPPED','DELIVERED','CANCELLED','REFUNDED');

        CREATE TABLE orders (
            order_id            INTEGER PRIMARY KEY,
            customer_id         INTEGER NOT NULL REFERENCES customers(customer_id),
            order_date          TIMESTAMP NOT NULL,
            status              order_status NOT NULL DEFAULT 'PENDING',
            shipping_address_id INTEGER NOT NULL REFERENCES addresses(address_id),
            billing_address_id  INTEGER NOT NULL REFERENCES addresses(address_id)
        );

        INSERT INTO orders VALUES
         (1001,1,'2026-06-01 10:15:00','DELIVERED',1,2),
         (1002,2,'2026-06-02 14:02:00','DELIVERED',3,4),
         (1003,1,'2026-06-03 09:40:00','SHIPPED',1,2),
         (1004,3,'2026-06-04 16:20:00','PAID',5,6),
         (1005,4,'2026-06-10 11:05:00','PENDING',7,8);

        SELECT * FROM orders;
        """
    )
    return


@app.cell
def _(mo):
    # R11: unit_price here is captured AT THE TIME OF SALE -- a deliberate, documented
    # denormalization vs. products.unit_price (the CURRENT catalog price). Compare order
    # 1005 (84.99 here) against the Mechanical Keyboard's current catalog price (89.00).
    order_items = mo.sql(
        f"""
        CREATE TABLE order_items (
            order_id    INTEGER NOT NULL REFERENCES orders(order_id),
            line_number INTEGER NOT NULL,
            product_id  INTEGER NOT NULL REFERENCES products(product_id),
            quantity    INTEGER NOT NULL CHECK (quantity > 0),
            unit_price  DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
            PRIMARY KEY (order_id, line_number)
        );

        INSERT INTO order_items VALUES
         (1001,1,1,2,24.99),
         (1001,2,2,3,9.99),
         (1002,1,1,1,24.99),
         (1003,1,3,1,19.50),
         (1004,1,2,5,9.99),
         (1005,1,5,1,84.99);

        SELECT * FROM order_items;
        """
    )
    return


@app.cell
def _(mo):
    coupons = mo.sql(
        f"""
        CREATE TABLE coupons (
            coupon_id    INTEGER PRIMARY KEY,
            code         VARCHAR NOT NULL UNIQUE,
            discount_pct DECIMAL(5,2) NOT NULL CHECK (discount_pct BETWEEN 0 AND 100),
            valid_from   DATE NOT NULL,
            valid_to     DATE NOT NULL CHECK (valid_to >= valid_from)
        );

        INSERT INTO coupons VALUES
         (1,'WELCOME10',10.00,'2026-01-01','2026-12-31'),
         (2,'SUMMER5',5.00,'2026-06-01','2026-08-31');

        SELECT * FROM coupons;
        """
    )
    return


@app.cell
def _(mo):
    # R13: Order <-M:N-> Coupon, resolved with an associative entity (no extra attributes needed here).
    order_coupons = mo.sql(
        f"""
        CREATE TABLE order_coupons (
            order_id  INTEGER NOT NULL REFERENCES orders(order_id),
            coupon_id INTEGER NOT NULL REFERENCES coupons(coupon_id),
            PRIMARY KEY (order_id, coupon_id)
        );

        INSERT INTO order_coupons VALUES (1005,2);

        SELECT * FROM order_coupons;
        """
    )
    return


@app.cell
def _(mo):
    # R12: an order may have zero or more payments (partial/failed/refunded attempts).
    payments = mo.sql(
        f"""
        CREATE TYPE payment_method AS ENUM ('CREDIT_CARD','PAYPAL','GIFT_CARD','BANK_TRANSFER');
        CREATE TYPE payment_status AS ENUM ('AUTHORIZED','CAPTURED','FAILED','REFUNDED');

        CREATE TABLE payments (
            payment_id INTEGER PRIMARY KEY,
            order_id   INTEGER NOT NULL REFERENCES orders(order_id),
            method     payment_method NOT NULL,
            amount     DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
            paid_at    TIMESTAMP,
            status     payment_status NOT NULL DEFAULT 'AUTHORIZED'
        );

        INSERT INTO payments VALUES
         (1,1001,'CREDIT_CARD',79.95,'2026-06-01 10:16:00','CAPTURED'),
         (2,1002,'PAYPAL',24.99,'2026-06-02 14:03:00','CAPTURED'),
         (3,1003,'CREDIT_CARD',19.50,'2026-06-03 09:41:00','CAPTURED'),
         (4,1004,'GIFT_CARD',49.95,'2026-06-04 16:22:00','CAPTURED');
        -- order 1005 (PENDING) has no payment row yet -- optional participation again.

        SELECT * FROM payments;
        """
    )
    return


@app.cell
def _(mo):
    # R12: an order may have zero or more shipments (order 1005 hasn't shipped; 1004 hasn't either).
    shipments = mo.sql(
        f"""
        CREATE TABLE shipments (
            shipment_id     INTEGER PRIMARY KEY,
            order_id        INTEGER NOT NULL REFERENCES orders(order_id),
            carrier         VARCHAR,
            tracking_number VARCHAR,
            shipped_at      TIMESTAMP,
            delivered_at    TIMESTAMP
        );

        INSERT INTO shipments VALUES
         (1,1001,'UPS','1Z999AA10123456784','2026-06-01 18:00:00','2026-06-03 12:00:00'),
         (2,1002,'FedEx','771234567890','2026-06-02 19:00:00','2026-06-04 09:30:00'),
         (3,1003,'UPS','1Z999AA10123456785','2026-06-03 17:00:00',NULL);
        -- shipment 3 is in transit: shipped but not yet delivered (delivered_at IS NULL).

        SELECT * FROM shipments;
        """
    )
    return


@app.cell
def _(mo):
    # R14/R15: rating is bounded 1-5 by CHECK; both FKs are mandatory (no "floating" reviews).
    reviews = mo.sql(
        f"""
        CREATE TABLE reviews (
            review_id   INTEGER PRIMARY KEY,
            product_id  INTEGER NOT NULL REFERENCES products(product_id),
            customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
            rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review_text VARCHAR,
            created_at  TIMESTAMP NOT NULL DEFAULT current_timestamp
        );

        INSERT INTO reviews (review_id, product_id, customer_id, rating, review_text) VALUES
         (1,1,1,5,'Smooth tracking, great battery life.'),
         (2,1,2,4,'Good value, a bit small for large hands.'),
         (3,3,1,5,'Perfect thickness, no slipping.'),
         (4,2,3,3,'Works but cable is shorter than expected.');

        SELECT * FROM reviews;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Proving the Constraints Fire

    A constraint in the DDL is only a promise until you see it **refuse** bad
    data. Each statement below breaks one business rule; the database must reject
    every one (the cell checks that it does, so none of these rows can leak into
    the queries in Part 2).

    The first two are the deck's tests; the rest cover the other kinds of
    constraint in this schema, including the self-referencing foreign key and
    an M:N pair stored twice.
    """)
    return


@app.cell
def _(categories, customers, order_items, orders, product_suppliers, products, reviews):
    import duckdb as _duckdb
    import pandas as _pd

    _tables_built = (categories, customers, order_items, orders, product_suppliers, products, reviews,)   # run only after Part 1 has built these tables
    _attempts = [
        ("R11", "an order line for order 9999 (does not exist)",
         "INSERT INTO order_items (order_id, line_number, product_id, quantity, unit_price) VALUES (9999, 1, 1, 1, 10.00)"),
        ("R4", "a product priced at -5.00",
         "INSERT INTO products (product_id, sku, product_name, category_id, unit_price) VALUES (99, 'SKU-999', 'Bad Price', 1, -5.00)"),
        ("R1", "a second account with Ana's email",
         "INSERT INTO customers (customer_id, first_name, last_name, email) VALUES (99, 'Ana', 'Twin', 'ana.diaz@example.com')"),
        ("R5", "a sub-category of category 999 (does not exist)",
         "INSERT INTO categories VALUES (99, 'Orphan Category', 999)"),
        ("R10", "an order status typed 'SHIPED'",
         "INSERT INTO orders VALUES (9998, 1, TIMESTAMP '2026-06-11 09:00:00', 'SHIPED', 1, 2)"),
        ("R14", "a 6-star review",
         "INSERT INTO reviews (review_id, product_id, customer_id, rating) VALUES (99, 1, 1, 6)"),
        ("R6", "the same product-supplier pair twice",
         "INSERT INTO product_suppliers SELECT product_id, supplier_id, supply_price FROM product_suppliers LIMIT 1"),
    ]
    _results = []
    for _rule, _what, _sql in _attempts:
        try:
            _duckdb.execute(_sql)
            _results.append((_rule, _what, "ACCEPTED — constraint missing!"))
        except Exception as _e:
            _results.append((_rule, _what, f"rejected: {type(_e).__name__}"))
    _proof = _pd.DataFrame(_results, columns=["rule", "bad data", "outcome"])
    # a missing table would also "reject" -- so accept only constraint / type errors
    assert _proof["outcome"].isin(["rejected: ConstraintException",
                                   "rejected: ConversionException"]).all(), _proof
    _proof
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 2 — Sample Queries

    Fourteen business questions against the schema above, covering inner/outer joins,
    a self-join, aggregation, a correlated grouping subquery, a window function, and
    `NULL`-aware logic — the same query patterns used in Part 6 of the lecture deck.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q1 — Customer order history (inner join)
    """)
    return


@app.cell
def _(customers, mo, orders):
    q1_customer_order_history = mo.sql(
        f"""
        SELECT c.first_name || ' ' || c.last_name AS customer,
               o.order_id, o.order_date::DATE AS order_date, o.status
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        ORDER BY c.customer_id, o.order_date;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q2 — Order line detail (three-way join)
    """)
    return


@app.cell
def _(mo, order_items, orders, products):
    q2_order_line_detail = mo.sql(
        f"""
        SELECT o.order_id, p.product_name, oi.quantity, oi.unit_price,
               (oi.quantity * oi.unit_price)::DECIMAL(10,2) AS line_total
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        ORDER BY o.order_id, oi.line_number;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q3 — Order totals (aggregation)
    """)
    return


@app.cell
def _(customers, mo, order_items, orders):
    q3_order_totals = mo.sql(
        f"""
        SELECT o.order_id, c.first_name || ' ' || c.last_name AS customer,
               SUM(oi.quantity * oi.unit_price)::DECIMAL(10,2) AS order_total
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, customer
        ORDER BY o.order_id;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q4 — Revenue by category (marketing's ask)
    """)
    return


@app.cell
def _(categories, mo, order_items, products):
    q4_revenue_by_category = mo.sql(
        f"""
        SELECT cat.category_name,
               SUM(oi.quantity * oi.unit_price)::DECIMAL(10,2) AS revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        GROUP BY cat.category_name
        ORDER BY revenue DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q5 — Average rating per product
    """)
    return


@app.cell
def _(mo, products, reviews):
    q5_avg_rating_per_product = mo.sql(
        f"""
        SELECT p.product_name, ROUND(AVG(r.rating),2) AS avg_rating, COUNT(*) AS num_reviews
        FROM reviews r
        JOIN products p ON p.product_id = r.product_id
        GROUP BY p.product_name
        ORDER BY avg_rating DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q6 — Low stock alert (warehouse ops' ask)
    """)
    return


@app.cell
def _(inventory, mo, products, warehouses):
    q6_low_stock_products = mo.sql(
        f"""
        SELECT p.product_name, w.warehouse_name, i.quantity_on_hand
        FROM inventory i
        JOIN products p ON p.product_id = i.product_id
        JOIN warehouses w ON w.warehouse_id = i.warehouse_id
        WHERE i.quantity_on_hand < 50
        ORDER BY i.quantity_on_hand;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q7 — Running revenue (window function)
    """)
    return


@app.cell
def _(mo, order_items, orders):
    q7_running_revenue = mo.sql(
        f"""
        SELECT o.order_id, o.order_date::DATE AS order_date,
               SUM(oi.quantity*oi.unit_price)::DECIMAL(10,2) AS order_total,
               SUM(SUM(oi.quantity*oi.unit_price)) OVER (ORDER BY o.order_date)::DECIMAL(10,2) AS running_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, o.order_date
        ORDER BY o.order_date;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q8 — Customers with no orders yet (anti-join via LEFT JOIN)
    """)
    return


@app.cell
def _(customers, mo, orders):
    q8_customers_no_orders = mo.sql(
        f"""
        SELECT c.first_name || ' ' || c.last_name AS customer
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id
        WHERE o.order_id IS NULL;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q9 — Category hierarchy (self-join)
    """)
    return


@app.cell
def _(categories, mo):
    q9_category_hierarchy = mo.sql(
        f"""
        SELECT child.category_name AS category, parent.category_name AS parent_category
        FROM categories child
        LEFT JOIN categories parent ON parent.category_id = child.parent_category_id
        ORDER BY parent_category NULLS FIRST, category;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q10 — Products sourced from more than one supplier
    """)
    return


@app.cell
def _(mo, product_suppliers, products):
    q10_multi_sourced_products = mo.sql(
        f"""
        SELECT p.product_name, COUNT(*) AS supplier_count
        FROM product_suppliers ps
        JOIN products p ON p.product_id = ps.product_id
        GROUP BY p.product_name
        HAVING COUNT(*) > 1;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q11 — Total inventory per product across all warehouses
    """)
    return


@app.cell
def _(inventory, mo, products):
    q11_total_inventory_per_product = mo.sql(
        f"""
        SELECT p.product_name, SUM(i.quantity_on_hand) AS total_units_on_hand
        FROM inventory i
        JOIN products p ON p.product_id = i.product_id
        GROUP BY p.product_name
        ORDER BY total_units_on_hand DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q12 — Orders with an applied coupon (subquery + join)
    """)
    return


@app.cell
def _(coupons, mo, order_coupons, order_items, orders):
    q12_orders_with_coupons = mo.sql(
        f"""
        SELECT o.order_id, c.code AS coupon_code, c.discount_pct,
               ot.order_total,
               (ot.order_total * (1 - c.discount_pct / 100))::DECIMAL(10,2) AS total_after_discount
        FROM order_coupons oc
        JOIN orders o ON o.order_id = oc.order_id
        JOIN coupons c ON c.coupon_id = oc.coupon_id
        JOIN (
            SELECT order_id, SUM(quantity * unit_price) AS order_total
            FROM order_items
            GROUP BY order_id
        ) ot ON ot.order_id = o.order_id;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q13 — Payment reconciliation: order total vs. amount captured
    """)
    return


@app.cell
def _(mo, order_items, orders, payments):
    q13_payment_reconciliation = mo.sql(
        f"""
        SELECT o.order_id,
               ot.order_total,
               COALESCE(SUM(pay.amount), 0)::DECIMAL(10,2) AS amount_paid,
               (ot.order_total - COALESCE(SUM(pay.amount), 0))::DECIMAL(10,2) AS balance_due
        FROM orders o
        JOIN (
            SELECT order_id, SUM(quantity * unit_price) AS order_total
            FROM order_items
            GROUP BY order_id
        ) ot ON ot.order_id = o.order_id
        LEFT JOIN payments pay ON pay.order_id = o.order_id AND pay.status = 'CAPTURED'
        GROUP BY o.order_id, ot.order_total
        ORDER BY o.order_id;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q14 — Shipment transit time (NULL-aware date arithmetic)
    """)
    return


@app.cell
def _(mo, orders, shipments):
    q14_shipment_transit_time = mo.sql(
        f"""
        SELECT o.order_id, s.carrier, s.shipped_at, s.delivered_at,
               DATE_DIFF('day', s.shipped_at, s.delivered_at) AS transit_days
        FROM shipments s
        JOIN orders o ON o.order_id = s.order_id
        ORDER BY o.order_id;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part 3 — Extending the Model with EER (R16)

    > **R16.** A customer may open a **business account** (company name, a unique
    > tax ID, a credit limit ≥ 0) and may join the **loyalty program** (a tier and a
    > points balance ≥ 0). A customer can be in **both, either, or neither**.

    Both are **subtypes** of `Customer` — an EER specialization that is
    **overlapping** (a customer can be in both) and **partial** (a customer can be
    in neither). Compare the Week 1 notebook's payment example, which is *disjoint*
    and *total*.

    Each subtype gets **its own table** whose primary key is also a foreign key to
    `customers`. A single `customer_type` column could not work here: it holds one
    value per row, so it would force the specialization to be disjoint.
    """)
    return


@app.cell
def _(customers, mo):
    # R16: business accounts -- subtype of Customer; PK = FK to the supertype.
    business_accounts = mo.sql(
        f"""
        CREATE TABLE business_accounts (
            customer_id   INTEGER PRIMARY KEY REFERENCES customers(customer_id),
            company_name  VARCHAR NOT NULL,
            tax_id        VARCHAR NOT NULL UNIQUE,
            credit_limit  DECIMAL(10,2) NOT NULL CHECK (credit_limit >= 0)
        );

        INSERT INTO business_accounts VALUES
         (2, 'Ochoa Design LLC',     '94-1234567',  5000.00),
         (3, 'Nguyen Robotics Inc.', '77-7654321', 12000.00);

        SELECT * FROM business_accounts;
        """
    )
    return (business_accounts,)


@app.cell
def _(customers, mo):
    # R16: loyalty members -- the second subtype; tier is a controlled vocabulary (ENUM).
    loyalty_members = mo.sql(
        f"""
        CREATE TYPE loyalty_tier AS ENUM ('SILVER','GOLD','PLATINUM');

        CREATE TABLE loyalty_members (
            customer_id  INTEGER PRIMARY KEY REFERENCES customers(customer_id),
            tier         loyalty_tier NOT NULL,
            points       INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
            joined_on    DATE NOT NULL
        );

        INSERT INTO loyalty_members VALUES
         (1, 'GOLD',   1200, DATE '2025-03-14'),
         (2, 'SILVER',  300, DATE '2026-01-09');

        SELECT * FROM loyalty_members;
        """
    )
    return (loyalty_members,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Q15 — Which customers are in which subtype?

    Ben (2) is in **both** — the specialization is overlapping. Dana (4) and Emma
    (5) are in **neither** — it is partial.
    """)
    return


@app.cell
def _(business_accounts, customers, loyalty_members, mo):
    q15_customer_subtypes = mo.sql(
        f"""
        SELECT c.customer_id, c.first_name,
               b.customer_id IS NOT NULL AS business_account,
               l.customer_id IS NOT NULL AS loyalty_member
        FROM customers AS c
        LEFT JOIN business_accounts AS b ON b.customer_id = c.customer_id
        LEFT JOIN loyalty_members   AS l ON l.customer_id = c.customer_id
        ORDER BY c.customer_id;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Q16 — Auditing disjointness and completeness

    One query audits both constraints: under a **disjoint** rule `in_both` must be
    0; under a **total** rule `in_neither` must be 0. R16 allows both, so here they
    are 1 and 2.
    """)
    return


@app.cell
def _(business_accounts, customers, loyalty_members, mo):
    q16_specialization_audit = mo.sql(
        f"""
        WITH roles AS (
            SELECT c.customer_id,
                   b.customer_id IS NOT NULL AS is_business,
                   l.customer_id IS NOT NULL AS is_loyalty
            FROM customers AS c
            LEFT JOIN business_accounts AS b ON b.customer_id = c.customer_id
            LEFT JOIN loyalty_members   AS l ON l.customer_id = c.customer_id
        )
        SELECT COUNT(*) FILTER (WHERE is_business AND is_loyalty)         AS in_both,
               COUNT(*) FILTER (WHERE NOT is_business AND NOT is_loyalty) AS in_neither,
               COUNT(*)                                                   AS customers
        FROM roles;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Proving the R16 Constraints Fire

    The subtype tables must refuse a business account for a customer who doesn't
    exist, a negative credit limit, a reused tax ID, a customer joining the loyalty
    program twice, and a tier outside the `ENUM`.
    """)
    return


@app.cell
def _(business_accounts, loyalty_members):
    import duckdb as _duckdb
    import pandas as _pd

    _tables_built = (business_accounts, loyalty_members,)   # run only after both subtype tables exist
    _audit = _duckdb.execute("""
        SELECT COUNT(*) FILTER (WHERE b.customer_id IS NOT NULL AND l.customer_id IS NOT NULL),
               COUNT(*) FILTER (WHERE b.customer_id IS NULL AND l.customer_id IS NULL)
        FROM customers AS c
        LEFT JOIN business_accounts AS b ON b.customer_id = c.customer_id
        LEFT JOIN loyalty_members   AS l ON l.customer_id = c.customer_id
    """).fetchone()
    assert _audit == (1, 2), _audit   # overlapping: Ben; partial: Dana and Emma
    _attempts = [
        ("R16 FK", "a business account for customer 99 (does not exist)",
         "INSERT INTO business_accounts VALUES (99, 'Ghost Co', '11-1111111', 100.00)"),
        ("R16 CHECK", "a credit limit of -5.00",
         "INSERT INTO business_accounts VALUES (4, 'Kim LLC', '22-2222222', -5.00)"),
        ("R16 UNIQUE", "Ochoa Design's tax ID reused",
         "INSERT INTO business_accounts VALUES (4, 'Kim LLC', '94-1234567', 100.00)"),
        ("R16 PK", "Ana joining the loyalty program a second time",
         "INSERT INTO loyalty_members VALUES (1, 'SILVER', 0, DATE '2026-02-01')"),
        ("R16 ENUM", "a 'BRONZE' tier",
         "INSERT INTO loyalty_members VALUES (4, 'BRONZE', 0, DATE '2026-02-01')"),
        ("R16 CHECK", "a points balance of -10",
         "INSERT INTO loyalty_members VALUES (4, 'SILVER', -10, DATE '2026-02-01')"),
    ]
    _results = []
    for _rule, _what, _sql in _attempts:
        try:
            _duckdb.execute(_sql)
            _results.append((_rule, _what, "ACCEPTED — constraint missing!"))
        except Exception as _e:
            _results.append((_rule, _what, f"rejected: {type(_e).__name__}"))
    _proof = _pd.DataFrame(_results, columns=["rule", "bad data", "outcome"])
    assert _proof["outcome"].isin(["rejected: ConstraintException",
                                   "rejected: ConversionException"]).all(), _proof
    _proof
    return


if __name__ == "__main__":
    app.run()
