"""
create_duckdb_table.py

Reads employees.csv (using only Python's built-in csv module -- no pandas)
and creates/loads an `employees` table in a DuckDB database file.

Usage:
    python create_duckdb_table.py <employees.csv> <employees.duckdb>
"""

import sys
import csv
import os
import duckdb


CREATE_TABLE_SQL = """
CREATE OR REPLACE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name  VARCHAR NOT NULL,
    last_name   VARCHAR NOT NULL,
    department  VARCHAR NOT NULL,
    hire_date   DATE NOT NULL,
    salary      DECIMAL(10,2) NOT NULL CHECK (salary >= 0)
);
"""

INSERT_SQL = """
INSERT INTO employees (employee_id, first_name, last_name, department, hire_date, salary)
VALUES (?, ?, ?, ?, ?, ?);
"""


def read_csv_rows(csv_path):
    """Read employees.csv with the standard library csv module and return a
    list of tuples ready for parameterized INSERT (no pandas involved)."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((
                int(row["employee_id"]),
                row["first_name"],
                row["last_name"],
                row["department"],
                row["hire_date"],          # 'YYYY-MM-DD' string; DuckDB casts to DATE
                float(row["salary"]),
            ))
    return rows


def main():

    CSV_PATH = sys.argv[1]
    print("CSV_PATH=", CSV_PATH)

    DB_PATH = sys.argv[2]
    print("DB_PATH=", DB_PATH)

    rows = read_csv_rows(CSV_PATH)
    print(f"Read {len(rows)} rows from {CSV_PATH}")

    con = duckdb.connect(DB_PATH)
    con.execute(CREATE_TABLE_SQL)
    con.executemany(INSERT_SQL, rows)

    count = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    print(f"Loaded {count} rows into 'employees' table in {DB_PATH}")

    print("\nSample rows:")
    for r in con.execute("SELECT * FROM employees ORDER BY employee_id LIMIT 5").fetchall():
        print(r)

    con.close()


if __name__ == "__main__":
    main()
