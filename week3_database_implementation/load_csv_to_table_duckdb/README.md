# Loading a CSV file into DuckDB from Python

`create_duckdb_table.py` reads `employees.csv` (20 employees, using only Python's
built-in `csv` module) and creates an `employees` table in a DuckDB database file.

## Run it

From this folder:

```bash
python3 create_duckdb_table.py employees.csv employees.duckdb
```

The script creates `employees.duckdb` (or replaces the table if the file already
exists) and prints the loaded rows. The database file is **not** in the
repository — running the script builds it.

## Look at the result

```bash
duckdb employees.duckdb -c "SELECT department, COUNT(*) FROM employees GROUP BY department;"
```

Compare with the MySQL version of the same load in
[`../load_csv_to_table_mysql/`](../load_csv_to_table_mysql/README.md).

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
