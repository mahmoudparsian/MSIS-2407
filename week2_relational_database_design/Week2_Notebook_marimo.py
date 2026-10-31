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
    # 📘 MSIS-2407 — Week 2 Notebook
    ## Relational Design and Normalization, Tested with SQL

    Companion to `lecture_notes_01_Relational_Design.md` and
    `lecture_notes_02_Normalization.md`. We take the wide order export
    `Week2_dataset.csv` and normalize it step by step — and at every step we
    let **SQL** supply the evidence: anomalies you can watch happen, functional
    dependencies you can test, and a decomposition you can prove is lossless.

    | Step | Idea |
    |---|---|
    | 1 | the wide table and its key |
    | 2 | three anomalies, demonstrated |
    | 3 | functional dependencies: testing them, and attribute closure |
    | 4 | 1NF — atomic values |
    | 5 | 2NF and 3NF — the decomposition, in DuckDB |
    | 6 | proving the decomposition lossless |
    | 7 | BCNF — when 3NF is not enough |
    | 8 | 4NF — independent multivalued facts |

    Every query cell checks the numbers this text quotes.
    """)
    return


@app.cell
def _(mo):
    import duckdb
    import pandas as pd

    con = duckdb.connect()
    data_file = mo.notebook_dir() / "Week2_dataset.csv"
    return con, data_file, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 1 — The wide table

    One row per order line. The natural key is **(order_id, product_name)** — one
    line per product per order — so we declare it.
    """)
    return


@app.cell
def _(con, data_file):
    con.execute(f"""
    CREATE OR REPLACE TABLE orders_wide (
        order_id       INTEGER NOT NULL,
        customer_name  VARCHAR NOT NULL,
        customer_email VARCHAR NOT NULL,
        product_name   VARCHAR NOT NULL,
        category       VARCHAR NOT NULL,
        price          DECIMAL(10,2) NOT NULL,
        quantity       INTEGER NOT NULL,
        order_date     DATE    NOT NULL,
        PRIMARY KEY (order_id, product_name)
    );
    INSERT INTO orders_wide SELECT * FROM read_csv('{data_file.as_posix()}');
    """)
    wide = con.execute("SELECT * FROM orders_wide ORDER BY order_id, product_name").df()
    assert len(wide) == 5
    wide
    return (wide,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 2 — Three anomalies

    **Update anomaly.** Every fact about a customer is repeated once per order
    line, so changing it means changing several rows:
    """)
    return


@app.cell
def _(con, wide):
    _copies = con.execute("""
    SELECT customer_name, customer_email, count(*) AS copies_of_this_email
    FROM orders_wide
    GROUP BY customer_name, customer_email
    ORDER BY customer_name
    """).df()
    assert _copies["copies_of_this_email"].tolist() == [2, 1, 2] and len(wide) == 5
    _copies
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Insert anomaly.** The shop starts selling a *Keyboard*. There is nowhere to
    record its price until somebody orders one — every row needs an `order_id`,
    because it is part of the key:
    """)
    return


@app.cell
def _(con, wide):
    try:
        con.execute("""
        INSERT INTO orders_wide (order_id, customer_name, customer_email,
                                 product_name, category, price, quantity, order_date)
        VALUES (NULL, NULL, NULL, 'Keyboard', 'Electronics', 45, NULL, NULL)
        """)
        insert_outcome = "accepted"
    except Exception as _e:
        insert_outcome = "rejected: " + type(_e).__name__
    assert insert_outcome.startswith("rejected") and len(wide) == 5
    insert_outcome
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Delete anomaly.** Bob cancels order 2. Deleting its only line also deletes
    the only record that a *Phone* costs 800 — and Bob's email:
    """)
    return


@app.cell
def _(con, wide):
    con.execute("""
    CREATE OR REPLACE TABLE wide_copy AS SELECT * FROM orders_wide;
    DELETE FROM wide_copy WHERE order_id = 2;
    """)
    _lost = con.execute("""
    SELECT (SELECT count(*) FROM wide_copy WHERE product_name  = 'Phone') AS phone_price_rows_left,
           (SELECT count(*) FROM wide_copy WHERE customer_name = 'Bob')   AS bob_email_rows_left
    """).df()
    assert _lost.iloc[0].tolist() == [0, 0] and len(wide) == 5
    _lost
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    All three have one cause: the table stores facts about **customers**,
    **orders** and **products** in the same row.

    ---
    ## Step 3 — Functional dependencies

    `X → Y` means: any two rows that agree on `X` agree on `Y`. In SQL, a
    *violation* is an `X` value with more than one `Y`:

    ```sql
    SELECT X FROM t GROUP BY X HAVING count(DISTINCT Y) > 1
    ```

    Zero violations means the data is **consistent with** the rule — it cannot
    prove the rule (five rows never can). One violation **disproves** it.
    """)
    return


@app.cell
def _(con, pd, wide):
    def fd_violations(table, lhs, rhs):
        """Number of lhs values that map to more than one rhs value."""
        return con.execute(f"""
        SELECT count(*) FROM (
            SELECT {lhs} FROM {table} GROUP BY {lhs}
            HAVING count(DISTINCT {rhs}) > 1)
        """).fetchone()[0]

    _candidates = [
        ("order_id", "order_date"),
        ("order_id", "customer_name"),
        ("customer_name", "customer_email"),
        ("product_name", "price"),
        ("product_name", "category"),
        ("customer_name", "product_name"),   # not a rule: Alice bought two products
        ("category", "price"),               # not a rule: one category, many prices
    ]
    fd_tests = pd.DataFrame(
        [(f"{l} → {r}", fd_violations("orders_wide", l, r)) for l, r in _candidates],
        columns=["dependency", "violations"])
    assert fd_tests["violations"].tolist() == [0, 0, 0, 0, 0, 2, 1] and len(wide) == 5
    fd_tests
    return (fd_violations,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We adopt the first five as **business rules**:

    ```
    order_id      → order_date, customer_name
    customer_name → customer_email
    product_name  → price, category
    ```

    **Attribute closure** `X⁺` is everything `X` determines, following the rules
    transitively. If `X⁺` is every column, `X` is a **superkey**.
    """)
    return


@app.cell
def _(pd):
    rules = [
        ({"order_id"}, {"order_date", "customer_name"}),
        ({"customer_name"}, {"customer_email"}),
        ({"product_name"}, {"price", "category"}),
        ({"order_id", "product_name"}, {"quantity"}),
    ]
    all_columns = {"order_id", "customer_name", "customer_email", "product_name",
                   "category", "price", "quantity", "order_date"}

    def closure(attrs):
        result = set(attrs)
        changed = True
        while changed:
            changed = False
            for lhs, rhs in rules:
                if lhs <= result and not rhs <= result:
                    result |= rhs
                    changed = True
        return result

    _rows = []
    for _x in [{"order_id"}, {"product_name"}, {"order_id", "product_name"}]:
        _c = closure(_x)
        _rows.append((", ".join(sorted(_x)), ", ".join(sorted(_c)), _c == all_columns))
    closures = pd.DataFrame(_rows, columns=["X", "X⁺", "superkey?"])
    assert closures["superkey?"].tolist() == [False, False, True]
    assert closure({"order_id"}) == {"order_id", "order_date", "customer_name", "customer_email"}
    closures
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So **(order_id, product_name)** is the key, and the dependencies on *part* of
    it (`order_id → …`, `product_name → …`) are **partial** — a 2NF violation —
    while `order_id → customer_name → customer_email` is **transitive** — a 3NF
    violation.

    ---
    ## Step 4 — 1NF: atomic values

    The wide table is already in 1NF. Here is what a 1NF violation looks like —
    one row per order with the products packed into a string — and how to undo it:
    """)
    return


@app.cell
def _(con, wide):
    con.execute("""
    CREATE OR REPLACE TABLE orders_packed AS
    SELECT order_id, string_agg(product_name, ', ' ORDER BY product_name) AS products
    FROM orders_wide GROUP BY order_id
    """)
    _packed = con.execute("SELECT * FROM orders_packed ORDER BY order_id").df()
    _unpacked = con.execute("""
    SELECT order_id, unnest(string_split(products, ', ')) AS product_name
    FROM orders_packed ORDER BY order_id, product_name
    """).df()
    assert _packed["products"].tolist()[0] == "Laptop, Mouse" and len(_unpacked) == len(wide)
    _packed
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You cannot index, constrain, or join on "Laptop, Mouse"; `unnest` turns it
    back into one product per row — five rows, the same as the 1NF table.

    ---
    ## Step 5 — 2NF and 3NF: the decomposition

    * **2NF** — move each partial dependency to its own table:
      `product(product_name → price, category)` and
      `orders(order_id → order_date, customer_name)`; what remains is
      `order_line(order_id, product_name, quantity)`.
    * **3NF** — move the transitive dependency out of `orders`:
      `customer(customer_name → customer_email)`.
    """)
    return


@app.cell
def _(con, wide):
    con.execute("""
    DROP TABLE IF EXISTS order_line;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS product;
    DROP TABLE IF EXISTS customer;

    CREATE TABLE customer (
        customer_name  VARCHAR PRIMARY KEY,
        customer_email VARCHAR NOT NULL UNIQUE
    );
    CREATE TABLE product (
        product_name VARCHAR PRIMARY KEY,
        category     VARCHAR NOT NULL,
        price        DECIMAL(10,2) NOT NULL CHECK (price >= 0)
    );
    CREATE TABLE orders (
        order_id      INTEGER PRIMARY KEY,
        customer_name VARCHAR NOT NULL REFERENCES customer(customer_name),
        order_date    DATE    NOT NULL
    );
    CREATE TABLE order_line (
        order_id     INTEGER NOT NULL REFERENCES orders(order_id),
        product_name VARCHAR NOT NULL REFERENCES product(product_name),
        quantity     INTEGER NOT NULL CHECK (quantity > 0),
        PRIMARY KEY (order_id, product_name)
    );

    INSERT INTO customer   SELECT DISTINCT customer_name, customer_email FROM orders_wide;
    INSERT INTO product    SELECT DISTINCT product_name, category, price FROM orders_wide;
    INSERT INTO orders     SELECT DISTINCT order_id, customer_name, order_date FROM orders_wide;
    INSERT INTO order_line SELECT order_id, product_name, quantity FROM orders_wide;
    """)
    normalized_sizes = con.execute("""
    SELECT (SELECT count(*) FROM customer)   AS customer,
           (SELECT count(*) FROM orders)     AS orders,
           (SELECT count(*) FROM product)    AS product,
           (SELECT count(*) FROM order_line) AS order_line
    """).df()
    assert normalized_sizes.iloc[0].tolist() == [3, 3, 5, 5] and len(wide) == 5
    normalized_sizes
    return (normalized_sizes,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Each fact is now stored once: three emails, five prices, three order dates.

    (This keeps the dataset's names as keys so the dependencies stay readable. In
    production, use surrogate keys such as `customer_id` — names change and
    collide; see the "Is `product_name` a good key?" slide.)

    ---
    ## Step 6 — Proving the decomposition lossless

    A decomposition is **lossless** if joining the pieces gives back exactly the
    original rows — no row lost, no spurious row added. `EXCEPT` in both
    directions must return nothing:
    """)
    return


@app.cell
def _(con, normalized_sizes):
    con.execute("""
    CREATE OR REPLACE VIEW rejoined AS
    SELECT ol.order_id, c.customer_name, c.customer_email, p.product_name,
           p.category, p.price, ol.quantity, o.order_date
    FROM order_line ol
    JOIN orders   o USING (order_id)
    JOIN customer c USING (customer_name)
    JOIN product  p USING (product_name)
    """)
    _lossless = con.execute("""
    SELECT (SELECT count(*) FROM (SELECT * FROM orders_wide EXCEPT SELECT * FROM rejoined)) AS lost_rows,
           (SELECT count(*) FROM (SELECT * FROM rejoined EXCEPT SELECT * FROM orders_wide)) AS spurious_rows,
           (SELECT count(*) FROM rejoined)                                                  AS rejoined_rows
    """).df()
    assert _lossless.iloc[0].tolist() == [0, 0, 5] and len(normalized_sizes) == 1
    _lossless
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And the update anomaly is gone — Alice's new email is one `UPDATE` of one
    row, and every order sees it:
    """)
    return


@app.cell
def _(con, normalized_sizes):
    con.execute("""
    CREATE OR REPLACE TABLE customer_copy AS SELECT * FROM customer;
    """)
    _changed = con.execute("""
    UPDATE customer_copy SET customer_email = 'alice@newmail.com'
    WHERE customer_name = 'Alice'
    """).fetchone()[0]
    assert _changed == 1 and len(normalized_sizes) == 1
    f"rows updated: {_changed}"
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 7 — BCNF: when 3NF is not enough

    **BCNF:** every determinant must be a superkey. The classic 3NF-but-not-BCNF
    case, from the notes:

    `advising(student_id, subject, instructor)` — a student has one instructor
    per subject, and each instructor teaches exactly one subject. So
    `instructor → subject`, but `instructor` is **not** a key.
    """)
    return


@app.cell
def _(con, fd_violations):
    con.execute("""
    CREATE OR REPLACE TABLE advising (
        student_id VARCHAR NOT NULL,
        subject    VARCHAR NOT NULL,
        instructor VARCHAR NOT NULL,
        PRIMARY KEY (student_id, subject)
    );
    INSERT INTO advising VALUES
        ('S1', 'Databases', 'Dr. Chen'),
        ('S2', 'Databases', 'Dr. Chen'),
        ('S3', 'AI',        'Dr. Patel'),
        ('S1', 'AI',        'Dr. Patel');
    """)
    bcnf_check = con.execute("""
    SELECT count(*)                   AS advising_rows,
           count(DISTINCT instructor) AS distinct_instructors
    FROM advising
    """).df()
    bcnf_check["instructor → subject violations"] = fd_violations("advising", "instructor", "subject")
    assert bcnf_check.iloc[0].tolist() == [4, 2, 0]
    bcnf_check
    return (bcnf_check,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `instructor → subject` holds, yet `instructor` repeats (2 instructors, 4
    rows), so "Dr. Chen teaches Databases" is stored once per student she
    advises. **Fix:** split on the offending dependency, and check it is lossless:
    """)
    return


@app.cell
def _(bcnf_check, con):
    con.execute("""
    CREATE OR REPLACE TABLE instructor AS
        SELECT DISTINCT instructor, subject FROM advising;
    CREATE OR REPLACE TABLE student_instructor AS
        SELECT DISTINCT student_id, instructor FROM advising;
    """)
    _bcnf = con.execute("""
    WITH back AS (
      SELECT si.student_id, i.subject, si.instructor
      FROM student_instructor si JOIN instructor i USING (instructor))
    SELECT (SELECT count(*) FROM instructor)                                        AS instructor_rows,
           (SELECT count(*) FROM (SELECT * FROM advising EXCEPT SELECT * FROM back)) AS lost_rows,
           (SELECT count(*) FROM (SELECT * FROM back EXCEPT SELECT * FROM advising)) AS spurious_rows
    """).df()
    assert _bcnf.iloc[0].tolist() == [2, 0, 0] and len(bcnf_check) == 1
    _bcnf
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    "Dr. Chen teaches Databases" is now stored once. **The trade-off:** the rule
    "one instructor per student per subject" — `(student_id, subject) →
    instructor` — no longer lives inside any single table's key, so the database
    cannot enforce it with a constraint. That is why 3NF is sometimes the
    deliberate stopping point.

    ---
    ## Step 8 — 4NF: independent multivalued facts

    Claim C1 has two document types and two adjusters, **independently**. In one
    table, every combination must be stored:
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE OR REPLACE TABLE claim_docs_adjusters AS
    SELECT 'C1' AS claim_id, d.document_type, a.adjuster
    FROM (VALUES ('Police Report'), ('Photos'), ('Repair Estimate')) d(document_type),
         (VALUES ('Maria'), ('Tom'), ('Lee')) a(adjuster);
    CREATE OR REPLACE TABLE claim_documents AS
        SELECT DISTINCT claim_id, document_type FROM claim_docs_adjusters;
    CREATE OR REPLACE TABLE claim_adjusters AS
        SELECT DISTINCT claim_id, adjuster FROM claim_docs_adjusters;
    """)
    _fournf = con.execute("""
    SELECT (SELECT count(*) FROM claim_docs_adjusters) AS combined_rows,
           (SELECT count(*) FROM claim_documents)
         + (SELECT count(*) FROM claim_adjusters)      AS split_rows
    """).df()
    assert _fournf.iloc[0].tolist() == [9, 6]
    _fournf
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    3 document types × 3 adjusters = **9** rows, versus 3 + 3 = **6** after the
    split — and the gap grows with every new document or adjuster. Split whenever
    two independent multivalued facts share one table.

    ---
    ## 🧪 Try it yourself

    1. Add `customer_city` and `customer_country` to the wide table. Which
       functional dependencies would you expect? Which normal form does the new
       design violate, and how do you fix it?
    2. Use `fd_violations` to test `order_date → order_id`. Does zero violations
       make it a rule? Why not?
    3. Add a rule `(order_id, product_name) → discount`. Extend `rules`, re-run
       `closure`, and decide which table `discount` belongs in.
    """)
    return


if __name__ == "__main__":
    app.run()
