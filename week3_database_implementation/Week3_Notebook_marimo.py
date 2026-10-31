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
    # 📘 MSIS-2407 — Week 3 Notebook
    ## Database Implementation: Load, Validate, Index, Transact

    Companion to the four Week 3 lecture notes. We take the order export
    `Week3_dataset.csv` (plus two broken rows a real export would contain) into a
    typed, constrained DuckDB schema — then measure indexes and watch
    transactions protect the data.

    | Step | Idea | Notes |
    |---|---|---|
    | 1 | land the raw file as text | Part 2 |
    | 2 | a typed, constrained schema | Part 1 |
    | 3 | cast, quarantine, load | Part 2 |
    | 4 | validate: counts, control totals, rebuild | Part 2 |
    | 5 | an idempotent reload | Part 2 |
    | 6 | constraints at work | Part 1 |
    | 7 | a bigger file: 50,000 orders | Part 2 |
    | 8 | indexes — measured, not assumed | Part 3 |
    | 9 | transactions and ACID | Part 4 |
    | 10 | two writers, one row | Part 4 |
    | 11 | the same work in MySQL | Parts 1–2 |

    Every query cell checks the numbers this text quotes (timings are shown, not
    checked — they depend on your machine).
    """)
    return


@app.cell
def _(mo):
    import time

    import duckdb
    import pandas as pd

    con = duckdb.connect()
    data_dir = mo.notebook_dir()
    return con, data_dir, pd, time


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 1 — Land the raw file as text

    Load every column as `VARCHAR` first. A typed load fails on the first bad
    value; a text landing table lets you **see** the bad values and decide what
    to do with them. Two broken rows are appended, the kind a real export
    contains: a price of `N/A` and a 13th month.
    """)
    return


@app.cell
def _(con, data_dir):
    con.execute(f"""
    CREATE OR REPLACE TABLE raw_sales AS
    SELECT * FROM read_csv('{(data_dir / "Week3_dataset.csv").as_posix()}', all_varchar = true);

    INSERT INTO raw_sales VALUES
        ('4', 'Dana', 'dana@gmail.com', 'Laptop', 'N/A', '1', '2025-01-04'),
        ('5', 'Evan', 'evan@gmail.com', 'Mouse',  '25',  '2', '2025-13-05');
    """)
    raw = con.execute("SELECT * FROM raw_sales").df()
    assert len(raw) == 7
    raw
    return (raw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 2 — A typed, constrained schema

    Week 2's design, implemented. Note the choices:

    * `DECIMAL(10,2)` for money — `DOUBLE` cannot store 0.10 exactly
    * surrogate `INTEGER` keys; the email is `UNIQUE` but is not the key
    * every relationship is a `FOREIGN KEY`; every rule we know is a `CHECK`
    """)
    return


@app.cell
def _(con, raw):
    con.execute("""
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS product;
    DROP TABLE IF EXISTS customer;

    CREATE TABLE customer (
        customer_id INTEGER PRIMARY KEY,
        name        VARCHAR NOT NULL,
        email       VARCHAR NOT NULL UNIQUE
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
    CREATE TABLE order_items (
        order_id   INTEGER NOT NULL REFERENCES orders(order_id),
        product_id INTEGER NOT NULL REFERENCES product(product_id),
        quantity   INTEGER NOT NULL CHECK (quantity > 0),
        PRIMARY KEY (order_id, product_id)
    );
    """)
    schema = con.execute("""
    SELECT table_name, count(*) AS columns
    FROM information_schema.columns
    WHERE table_name IN ('customer', 'product', 'orders', 'order_items')
    GROUP BY table_name ORDER BY table_name
    """).df()
    assert schema["columns"].tolist() == [3, 3, 3, 3] and len(raw) == 7
    schema
    return (schema,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 3 — Cast, quarantine, load

    `TRY_CAST` returns `NULL` instead of failing. Any row where a cast fails goes
    to a **quarantine** table — kept, with a reason, for someone to fix — and only
    clean rows are loaded.
    """)
    return


@app.cell
def _(con, schema):
    con.execute("""
    CREATE OR REPLACE VIEW sales_typed AS
    SELECT TRY_CAST(order_id AS INTEGER)       AS order_id,
           customer_name, customer_email, product_name,
           TRY_CAST(price    AS DECIMAL(10,2)) AS price,
           TRY_CAST(quantity AS INTEGER)       AS quantity,
           TRY_CAST(order_date AS DATE)        AS order_date,
           price AS raw_price, order_date AS raw_order_date
    FROM raw_sales;

    CREATE OR REPLACE TABLE quarantine AS
    SELECT *, CASE WHEN price IS NULL      THEN 'bad price ' || raw_price
                   WHEN order_date IS NULL THEN 'bad date ' || raw_order_date
                   ELSE 'bad number' END AS reason
    FROM sales_typed
    WHERE order_id IS NULL OR price IS NULL OR quantity IS NULL OR order_date IS NULL;

    CREATE OR REPLACE VIEW sales_clean AS
    SELECT * EXCLUDE (raw_price, raw_order_date) FROM sales_typed
    WHERE order_id IS NOT NULL AND price IS NOT NULL
      AND quantity IS NOT NULL AND order_date IS NOT NULL;
    """)
    quarantined = con.execute(
        "SELECT order_id, customer_name, reason FROM quarantine ORDER BY order_id").df()
    assert quarantined["reason"].tolist() == ["bad price N/A", "bad date 2025-13-05"]
    assert len(schema) == 4
    quarantined
    return (quarantined,)


@app.cell
def _(con, quarantined):
    load_sql = """
    INSERT INTO customer
    SELECT row_number() OVER (ORDER BY customer_email), customer_name, customer_email
    FROM (SELECT DISTINCT customer_name, customer_email FROM sales_clean) {conflict};

    INSERT INTO product
    SELECT row_number() OVER (ORDER BY product_name), product_name, price
    FROM (SELECT DISTINCT product_name, price FROM sales_clean) {conflict};

    INSERT INTO orders
    SELECT DISTINCT s.order_id, c.customer_id, s.order_date
    FROM sales_clean s JOIN customer c ON c.email = s.customer_email {conflict};

    INSERT INTO order_items
    SELECT s.order_id, p.product_id, s.quantity
    FROM sales_clean s JOIN product p ON p.name = s.product_name {conflict};
    """
    con.execute(load_sql.format(conflict=""))
    loaded = con.execute("""
    SELECT (SELECT count(*) FROM customer)    AS customer,
           (SELECT count(*) FROM product)     AS product,
           (SELECT count(*) FROM orders)      AS orders,
           (SELECT count(*) FROM order_items) AS order_items
    """).df()
    assert loaded.iloc[0].tolist() == [3, 5, 3, 5] and len(quarantined) == 2
    loaded
    return load_sql, loaded


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 4 — Validate the load

    "It ran without errors" is not validation. Three checks:

    1. **Row count** — every clean source line is an `order_items` row
    2. **Control total** — the money adds up to the same cent
    3. **Rebuild** — joining the tables back reproduces the source exactly
    """)
    return


@app.cell
def _(con, loaded):
    validation = con.execute("""
    WITH rebuilt AS (
      SELECT o.order_id, c.name AS customer_name, c.email AS customer_email,
             p.name AS product_name, p.price, oi.quantity, o.order_date
      FROM order_items oi
      JOIN orders   o ON o.order_id    = oi.order_id
      JOIN customer c ON c.customer_id = o.customer_id
      JOIN product  p ON p.product_id  = oi.product_id)
    SELECT
      (SELECT count(*) FROM sales_clean)                    AS source_rows,
      (SELECT count(*) FROM order_items)                    AS loaded_rows,
      (SELECT sum(price * quantity) FROM sales_clean)       AS source_total,
      (SELECT sum(p.price * oi.quantity)
         FROM order_items oi JOIN product p USING (product_id)) AS loaded_total,
      (SELECT count(*) FROM (SELECT * FROM sales_clean EXCEPT SELECT * FROM rebuilt))
                                                            AS rows_not_rebuilt
    """).df()
    _v = validation.iloc[0]
    assert (_v["source_rows"], _v["loaded_rows"]) == (5, 5)
    assert float(_v["source_total"]) == float(_v["loaded_total"]) == 4425.0
    assert _v["rows_not_rebuilt"] == 0 and len(loaded) == 1
    validation
    return (validation,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 5 — An idempotent reload

    Loads get re-run — after a crash, by a scheduler, by a colleague. Running the
    same load twice must not duplicate data. A naive re-run is **rejected** by
    the primary keys (good: the constraints caught it). An idempotent load skips
    rows that already exist, so running it any number of times gives the same
    result:
    """)
    return


@app.cell
def _(con, load_sql, pd, validation):
    try:
        con.execute(load_sql.format(conflict=""))
        _naive = "accepted (duplicates!)"
    except Exception as _e:
        _naive = "rejected: " + type(_e).__name__
    con.execute(load_sql.format(conflict="ON CONFLICT DO NOTHING"))
    con.execute(load_sql.format(conflict="ON CONFLICT DO NOTHING"))
    _counts = con.execute("""
    SELECT (SELECT count(*) FROM customer), (SELECT count(*) FROM product),
           (SELECT count(*) FROM orders),   (SELECT count(*) FROM order_items)
    """).fetchone()
    reload_check = pd.DataFrame(
        [("naive re-run", _naive), ("idempotent re-run ×2, row counts", str(list(_counts)))],
        columns=["attempt", "result"])
    assert _naive.startswith("rejected") and list(_counts) == [3, 5, 3, 5]
    assert len(validation) == 1
    reload_check
    return (reload_check,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 6 — Constraints at work

    Each of these is a mistake an application could make. The schema refuses
    every one:
    """)
    return


@app.cell
def _(con, pd, reload_check):
    _attempts = []
    for _label, _sql in [
        ("quantity of 0",            "INSERT INTO order_items VALUES (2, 1, 0)"),
        ("negative price",           "INSERT INTO product VALUES (9, 'Cable', -1)"),
        ("order for customer 99",    "INSERT INTO orders VALUES (9, 99, DATE '2025-02-01')"),
        ("a second account, same email",
                                     "INSERT INTO customer VALUES (9, 'Al', 'alice@gmail.com')"),
        ("order line for order 99",  "INSERT INTO order_items VALUES (99, 1, 1)"),
    ]:
        try:
            con.execute(_sql)
            _attempts.append((_label, "accepted"))
        except Exception as _e:
            _attempts.append((_label, "rejected: " + type(_e).__name__))
    constraint_tests = pd.DataFrame(_attempts, columns=["mistake", "outcome"])
    assert all(constraint_tests["outcome"].str.startswith("rejected"))
    assert len(reload_check) == 2
    constraint_tests
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 7 — A bigger file: 50,000 orders

    `Week3_orders_dataset.csv` has 50,000 orders (order, customer, amount,
    country, product). Same discipline at scale: declare the types and the key,
    load, then check the count and the control total against the file.
    """)
    return


@app.cell
def _(con, data_dir):
    _file = (data_dir / "Week3_orders_dataset.csv").as_posix()
    con.execute(f"""
    CREATE OR REPLACE TABLE orders_50k (
        order_id    INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        amount      DECIMAL(10,2) NOT NULL CHECK (amount > 0),
        country     VARCHAR NOT NULL,
        product     VARCHAR NOT NULL
    );
    INSERT INTO orders_50k SELECT * FROM read_csv('{_file}');
    """)
    big_check = con.execute(f"""
    SELECT (SELECT count(*)    FROM read_csv('{_file}')) AS file_rows,
           (SELECT count(*)    FROM orders_50k)          AS loaded_rows,
           (SELECT sum(amount) FROM read_csv('{_file}')) AS file_total,
           (SELECT sum(amount) FROM orders_50k)          AS loaded_total
    """).df()
    _b = big_check.iloc[0]
    assert (_b["file_rows"], _b["loaded_rows"]) == (50_000, 50_000)
    assert float(_b["file_total"]) == float(_b["loaded_total"]) == 50_048_888.0
    big_check
    return (big_check,)


@app.cell
def _(big_check, con):
    by_country = con.execute("""
    SELECT country, count(*) AS orders, sum(amount) AS revenue
    FROM orders_50k GROUP BY country ORDER BY country
    """).df()
    assert by_country["orders"].tolist() == [12_667, 12_222, 12_516, 12_595]
    assert len(big_check) == 1
    by_country
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Step 8 — Indexes: measured, not assumed

    In a row store like MySQL, an index on a filtered column usually turns a full
    scan into a quick lookup. DuckDB is **columnar** and keeps **zone maps**
    (min/max per block), so it skips data without any index — and an index may
    buy little. The only honest answer is to **measure**.

    We build 2,000,000 rows, time a lookup by an unsorted column before and after
    an index (best of five runs), and time a range filter on a **sorted** column
    with no index at all.
    """)
    return


@app.cell
def _(con, pd, time):
    con.execute("""
    DROP INDEX IF EXISTS idx_events_customer;
    CREATE OR REPLACE TABLE events AS
    SELECT i AS event_id,
           (hash(i) % 100000)::INTEGER AS customer_id,
           (i % 997)::DECIMAL(10,2)    AS amount
    FROM range(2000000) t(i);
    """)

    def best_of(sql, runs=5):
        _times, _result = [], None
        for _ in range(runs):
            _t0 = time.perf_counter()
            _result = con.execute(sql).fetchall()
            _times.append(time.perf_counter() - _t0)
        return min(_times) * 1000, _result

    _lookup = "SELECT count(*), sum(amount) FROM events WHERE customer_id = 4242"
    _range = "SELECT count(*), sum(amount) FROM events WHERE event_id BETWEEN 1500000 AND 1500999"

    _no_index_ms, _no_index_result = best_of(_lookup)
    _t0 = time.perf_counter()
    con.execute("CREATE INDEX idx_events_customer ON events(customer_id)")
    _build_ms = (time.perf_counter() - _t0) * 1000
    _index_ms, _index_result = best_of(_lookup)
    _range_ms, _range_result = best_of(_range)

    index_timings = pd.DataFrame([
        ("lookup customer_id = 4242, no index",       round(_no_index_ms, 2)),
        ("build the index (once)",                    round(_build_ms, 2)),
        ("lookup customer_id = 4242, with index",     round(_index_ms, 2)),
        ("range on sorted event_id, no index",        round(_range_ms, 2)),
    ], columns=["operation", "milliseconds"])
    assert _no_index_result == _index_result          # same answer either way
    assert _range_result[0][0] == 1000
    index_timings
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Read your numbers, then ask: did the index pay for its build time and for
    slowing down every future `INSERT`? The range on the sorted column was fast
    with **no** index — that is the zone map at work. In DuckDB, keep an index
    when it enforces a rule (`PRIMARY KEY`, `UNIQUE`) or when *measurement* shows
    it helps. (Session 9's Lab 1b measures this more carefully.)

    ---
    ## Step 9 — Transactions and ACID

    A transfer is two updates that must happen together or not at all. The
    account table forbids negative balances.
    """)
    return


@app.cell
def _(con, pd):
    con.execute("""
    CREATE OR REPLACE TABLE account (
        account_id INTEGER PRIMARY KEY,
        owner      VARCHAR NOT NULL,
        balance    DECIMAL(10,2) NOT NULL CHECK (balance >= 0)
    );
    INSERT INTO account VALUES (1, 'Alice', 100), (2, 'Bob', 50);
    """)

    def balances():
        return [float(b) for (b,) in con.execute(
            "SELECT balance FROM account ORDER BY account_id").fetchall()]

    _steps = []

    # 1. a good transfer: Alice → Bob, 30
    con.execute("BEGIN")
    con.execute("UPDATE account SET balance = balance - 30 WHERE account_id = 1")
    con.execute("UPDATE account SET balance = balance + 30 WHERE account_id = 2")
    con.execute("COMMIT")
    _steps.append(("transfer 30 Alice → Bob, committed", balances()))

    # 2. a bad transfer inside a transaction: Bob → Alice, 200 (Bob has 80)
    con.execute("BEGIN")
    try:
        con.execute("UPDATE account SET balance = balance + 200 WHERE account_id = 1")
        con.execute("UPDATE account SET balance = balance - 200 WHERE account_id = 2")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
    _steps.append(("transfer 200 Bob → Alice in a transaction: failed, rolled back", balances()))

    # 3. the same bad transfer WITHOUT a transaction (autocommit)
    try:
        con.execute("UPDATE account SET balance = balance + 200 WHERE account_id = 1")
        con.execute("UPDATE account SET balance = balance - 200 WHERE account_id = 2")
    except Exception:
        pass
    _steps.append(("same transfer in autocommit: half of it stuck", balances()))

    transactions = pd.DataFrame(_steps, columns=["what happened", "balances [Alice, Bob]"])
    assert [s[1] for s in _steps] == [[70.0, 80.0], [70.0, 80.0], [270.0, 80.0]]
    transactions
    return (balances,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Inside a transaction the failed transfer left **no trace** (atomicity). In
    autocommit, the first `UPDATE` committed on its own and $200 appeared from
    nowhere — the total went from $150 to $350. Any change of more than one
    statement belongs in `BEGIN … COMMIT`.

    ---
    ## Step 10 — Two writers, one row

    Two sessions open transactions and both try to change Alice's balance. MySQL
    (InnoDB) would make the second one **wait** for a lock. DuckDB is
    **optimistic**: the second writer gets an error immediately and must retry.
    """)
    return


@app.cell
def _(balances, con):
    con.execute("UPDATE account SET balance = 100 WHERE account_id = 1")   # reset Alice
    _session_a = con.cursor()
    _session_b = con.cursor()
    _session_a.execute("BEGIN")
    _session_b.execute("BEGIN")
    _session_a.execute("UPDATE account SET balance = balance - 10 WHERE account_id = 1")
    try:
        _session_b.execute("UPDATE account SET balance = balance - 20 WHERE account_id = 1")
        second_writer = "succeeded"
    except Exception as _e:
        second_writer = str(_e)
    _session_a.execute("COMMIT")
    _session_b.execute("ROLLBACK")
    _alice = balances()[0]
    assert "Conflict" in second_writer and _alice == 90.0
    {"second writer": second_writer, "Alice's balance afterwards": _alice}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Session A's withdrawal of 10 committed; session B's withdrawal of 20 was
    refused rather than silently overwriting it (no **lost update**). A real
    application catches that error and re-runs B's transaction.

    ---
    ## Step 11 — The same work in MySQL

    | | DuckDB (this notebook) | MySQL |
    |---|---|---|
    | open a database | `duckdb.connect("shop.duckdb")` | `CREATE DATABASE shop; USE shop;` |
    | bulk load a CSV | `INSERT INTO t SELECT * FROM read_csv('f.csv')` | `LOAD DATA LOCAL INFILE 'f.csv' INTO TABLE t …` |
    | text-first landing | `read_csv(…, all_varchar = true)` | load into `VARCHAR` columns |
    | safe cast | `TRY_CAST(x AS DATE)` | `STR_TO_DATE(x, '%Y-%m-%d')` (returns `NULL`) |
    | idempotent insert | `… ON CONFLICT DO NOTHING` | `INSERT IGNORE …` / `ON DUPLICATE KEY UPDATE` |
    | second writer on one row | error: *Conflict on update!* | waits for the row lock |
    | users and `GRANT` | none (embedded) | full account system |

    To run a real MySQL load from Python, see `load_csv_to_table_mysql/` (needs
    MySQL Server and `pip install mysql-connector-python`).

    ---
    ## 🧪 Try it yourself

    1. Add a third broken row with a quantity of `two`. Which reason does the
       quarantine give it? Change the `CASE` so it says `bad quantity`.
    2. In Step 8, index `amount` instead (only 997 distinct values). Is the
       lookup faster or slower? Why?
    3. In Step 9, move the debit *before* the credit in the autocommit case. What
       do the balances show now — and is that any better?
    """)
    return


if __name__ == "__main__":
    app.run()
