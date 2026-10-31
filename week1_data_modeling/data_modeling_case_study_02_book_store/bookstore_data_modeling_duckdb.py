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
    # Relational Data Modeling — Hands-on DuckDB Notebook (Bookstore)

    Companion notebook to **`relational_data_modeling_bookstore.md`** (the PageTurner
    Books lecture deck — Case Study 2 of 3). Every table below is built and populated with
    a single, pure-SQL `mo.sql()` cell, in dependency order (parent tables before the
    children that reference them), backed by marimo's embedded in-memory DuckDB connection.

    **Part 1** creates and populates the 6-table bookstore schema.
    **Part 2** runs sample business-question queries against it.

    This schema is deliberately simple: every relationship is a plain one-to-many. Order
    and Book are linked through the **Order Line** entity (`order_items`), which is 1:N
    from each side — the shape of a many-to-many, but with its own key and attributes
    (`quantity`, `unit_price`). There is no self-referencing hierarchy — see the
    companion e-commerce notebook (Case Study 3) for that and for true M:N junctions.
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
    # R2: an author can write many books; each book has exactly one author on record
    # (a deliberate simplification -- see the e-commerce case study for many-to-many).
    authors = mo.sql(
        f"""
        CREATE TABLE authors (
            author_id  INTEGER PRIMARY KEY,
            first_name VARCHAR NOT NULL,
            last_name  VARCHAR NOT NULL
        );

        INSERT INTO authors (author_id, first_name, last_name) VALUES
         (1,'Haruki','Murakami'),
         (2,'Andy','Weir'),
         (3,'Delia','Owens'),
         (4,'James','Clear');

        SELECT * FROM authors;
        """
    )
    return


@app.cell
def _(mo):
    # R2: a publisher can publish many books; each book has exactly one publisher.
    publishers = mo.sql(
        f"""
        CREATE TABLE publishers (
            publisher_id   INTEGER PRIMARY KEY,
            publisher_name VARCHAR NOT NULL UNIQUE,
            city           VARCHAR
        );

        INSERT INTO publishers (publisher_id, publisher_name, city) VALUES
         (1,'Knopf','New York'),
         (2,'Crown Publishing','New York'),
         (3,'Putnam','New York');

        SELECT * FROM publishers;
        """
    )
    return


@app.cell
def _(mo):
    # R1: isbn is a unique natural key; price is protected by a CHECK (>= 0).
    books = mo.sql(
        f"""
        CREATE TABLE books (
            book_id           INTEGER PRIMARY KEY,
            isbn              VARCHAR NOT NULL UNIQUE,
            title             VARCHAR NOT NULL,
            author_id         INTEGER NOT NULL REFERENCES authors(author_id),
            publisher_id      INTEGER NOT NULL REFERENCES publishers(publisher_id),
            price             DECIMAL(10,2) NOT NULL CHECK (price >= 0),
            publication_year  INTEGER,
            genre             VARCHAR
        );

        INSERT INTO books (book_id, isbn, title, author_id, publisher_id, price, publication_year, genre) VALUES
         (1,'ISBN-001','Norwegian Wood',1,1,15.99,1987,'Fiction'),
         (2,'ISBN-002','The Martian',2,2,12.99,2011,'Science Fiction'),
         (3,'ISBN-003','Where the Crawdads Sing',3,3,14.50,2018,'Fiction'),
         (4,'ISBN-004','Atomic Habits',4,2,18.00,2018,'Self-Help'),
         (5,'ISBN-005','Kafka on the Shore',1,1,16.99,2002,'Fiction');

        SELECT * FROM books;
        """
    )
    return


@app.cell
def _(mo):
    # R3: email is a unique natural/alternate key, used to log in.
    customers = mo.sql(
        f"""
        CREATE TABLE customers (
            customer_id  INTEGER PRIMARY KEY,
            first_name   VARCHAR NOT NULL,
            last_name    VARCHAR NOT NULL,
            email        VARCHAR NOT NULL UNIQUE,
            phone        VARCHAR
        );

        INSERT INTO customers (customer_id, first_name, last_name, email, phone) VALUES
         (1,'Grace','Lee','grace.lee@example.com','408-555-0201'),
         (2,'Marcus','Reed','marcus.reed@example.com','510-555-0202'),
         (3,'Priya','Shah','priya.shah@example.com','650-555-0203'),
         (4,'Tom','Becker','tom.becker@example.com','925-555-0204');
        -- Tom Becker (4) has registered but hasn't ordered yet -- R4's optional
        -- participation: a Customer does not require any Orders.

        SELECT * FROM customers;
        """
    )
    return


@app.cell
def _(mo):
    # R4/R5: every order requires a customer; status is a fixed lifecycle (ENUM).
    orders = mo.sql(
        f"""
        CREATE TYPE order_status AS ENUM ('PENDING','SHIPPED','DELIVERED','CANCELLED');

        CREATE TABLE orders (
            order_id     INTEGER PRIMARY KEY,
            customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
            order_date   DATE NOT NULL,
            status       order_status NOT NULL DEFAULT 'PENDING'
        );

        INSERT INTO orders (order_id, customer_id, order_date, status) VALUES
         (5001,1,'2026-06-01','DELIVERED'),
         (5002,2,'2026-06-02','SHIPPED'),
         (5003,1,'2026-06-05','DELIVERED'),
         (5004,3,'2026-06-08','PENDING');

        SELECT * FROM orders;
        """
    )
    return


@app.cell
def _(mo):
    # R6: unit_price is captured AT THE TIME OF SALE -- a deliberate, documented
    # denormalization vs. books.price (the CURRENT catalog price). Compare order 5004's
    # copy of "The Martian" (11.99 here) against its current catalog price (12.99).
    # R7/R8: quantity > 0, unit_price >= 0, and both FKs are mandatory (no orphan lines).
    order_items = mo.sql(
        f"""
        CREATE TABLE order_items (
            order_id     INTEGER NOT NULL REFERENCES orders(order_id),
            line_number  INTEGER NOT NULL,
            book_id      INTEGER NOT NULL REFERENCES books(book_id),
            quantity     INTEGER NOT NULL CHECK (quantity > 0),
            unit_price   DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
            PRIMARY KEY (order_id, line_number)
        );

        INSERT INTO order_items (order_id, line_number, book_id, quantity, unit_price) VALUES
         (5001,1,1,1,15.99),
         (5001,2,2,1,12.99),
         (5002,1,3,2,14.50),
         (5003,1,4,1,18.00),
         (5004,1,5,1,16.99),
         (5004,2,2,1,11.99);

        SELECT * FROM order_items;
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
    constraint in this schema.
    """)
    return


@app.cell
def _(books, customers, order_items, orders):
    import duckdb as _duckdb
    import pandas as _pd

    _tables_built = (books, customers, order_items, orders,)   # run only after Part 1 has built these tables
    _attempts = [
        ("R7/R8", "an order line for order 9999 (does not exist)",
         "INSERT INTO order_items (order_id, line_number, book_id, quantity, unit_price) VALUES (9999, 1, 1, 1, 10.00)"),
        ("R1", "a book priced at -5.00",
         "INSERT INTO books (book_id, isbn, title, author_id, publisher_id, price) VALUES (99, 'ISBN-999', 'Bad Book', 1, 1, -5.00)"),
        ("R3", "a second account with Grace's email",
         "INSERT INTO customers (customer_id, first_name, last_name, email) VALUES (99, 'Grace', 'Twin', 'grace.lee@example.com')"),
        ("R5", "an order status typed 'SHIPED'",
         "INSERT INTO orders (order_id, customer_id, order_date, status) VALUES (9998, 1, DATE '2026-06-09', 'SHIPED')"),
        ("R4", "an order with no customer",
         "INSERT INTO orders (order_id, customer_id, order_date, status) VALUES (9997, NULL, DATE '2026-06-09', 'PENDING')"),
        ("R7", "an order line with quantity 0",
         "INSERT INTO order_items (order_id, line_number, book_id, quantity, unit_price) VALUES (5001, 99, 1, 0, 10.00)"),
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

    Six business questions against the schema above: an inner join, a detail join,
    aggregation, two more joins grouping by a different dimension each, and an
    anti-join — the same query patterns used in Part 6 of the lecture deck.
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
               o.order_id, o.order_date, o.status
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
def _(books, mo, order_items, orders):
    q2_order_line_detail = mo.sql(
        f"""
        SELECT o.order_id, b.title, oi.quantity, oi.unit_price,
               (oi.quantity * oi.unit_price)::DECIMAL(10,2) AS line_total
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN books b ON b.book_id = oi.book_id
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
    ### Q4 — Revenue by author
    """)
    return


@app.cell
def _(authors, books, mo, order_items):
    q4_revenue_by_author = mo.sql(
        f"""
        SELECT a.first_name || ' ' || a.last_name AS author,
               SUM(oi.quantity * oi.unit_price)::DECIMAL(10,2) AS revenue
        FROM order_items oi
        JOIN books b ON b.book_id = oi.book_id
        JOIN authors a ON a.author_id = b.author_id
        GROUP BY author
        ORDER BY revenue DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q5 — Catalog size and average price by publisher
    """)
    return


@app.cell
def _(books, mo, publishers):
    q5_books_per_publisher = mo.sql(
        f"""
        SELECT p.publisher_name, COUNT(*) AS num_books, ROUND(AVG(b.price), 2) AS avg_price
        FROM books b
        JOIN publishers p ON p.publisher_id = b.publisher_id
        GROUP BY p.publisher_name
        ORDER BY num_books DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q6 — Customers with no orders yet (anti-join via LEFT JOIN)
    """)
    return


@app.cell
def _(customers, mo, orders):
    q6_customers_no_orders = mo.sql(
        f"""
        SELECT c.first_name || ' ' || c.last_name AS customer
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id
        WHERE o.order_id IS NULL;
        """
    )
    return


if __name__ == "__main__":
    app.run()
