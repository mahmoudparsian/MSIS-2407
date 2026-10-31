"""
create_mysql_table.py

Reads a CSV of employees (using only Python's built-in 
csv module -- no pandas) and creates/loads a table in 
MySQL, using connection credentials from an external 
JSON config file.

Setup:
    pip install mysql-connector-python
    Create a JSON file with your connection settings, e.g. mysql_config.json:
        {
          "host": "127.0.0.1",
          "port": 3306,
          "user": "root",
          "password": "your_password",
          "database": "week3_db"
        }
    (Omit "password" from the JSON to be prompted for it securely instead.)
    The target database must already exist (CREATE DATABASE week3_db; if needed).

Usage:
    python create_mysql_table_with_insert.py <json-file> <csv-file> <table-name>

Example:
    python create_mysql_table_with_insert.py mysql_config.json employees.csv employees
"""

import argparse
import csv
import getpass
import json
import re
import sys

import mysql.connector
from mysql.connector import Error as MySQLError

# Only allow safe SQL identifiers for the table name (it gets interpolated
# into DDL/DML text below, since MySQL does not support parameterized
# identifiers the way it supports parameterized values).
VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_config(config_path):
    """Load MySQL connection settings from an external JSON file (no pandas,
    no hard-coded credentials in source code)."""
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    required = {"host", "port", "user", "database"}
    missing = required - config.keys()
    if missing:
        raise ValueError(f"{config_path} is missing required keys: {sorted(missing)}")
    return config


def read_csv_rows(csv_path):
    """Read the employees CSV with the standard library csv module and
    return a list of tuples ready for a parameterized INSERT (no pandas)."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((
                int(row["employee_id"]),
                row["first_name"],
                row["last_name"],
                row["department"],
                row["hire_date"],           # 'YYYY-MM-DD' string; MySQL casts to DATE
                float(row["salary"]),
            ))
    return rows


def build_sql(table_name):
    """Build the CREATE TABLE / INSERT statements for the given table name."""
    if not VALID_IDENTIFIER.match(table_name):
        raise ValueError(
            f"Invalid table name {table_name!r}: must start with a letter or "
            "underscore and contain only letters, digits, and underscores."
        )

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        employee_id INT PRIMARY KEY,
        first_name  VARCHAR(50)  NOT NULL,
        last_name   VARCHAR(50)  NOT NULL,
        department  VARCHAR(50)  NOT NULL,
        hire_date   DATE         NOT NULL,
        salary      DECIMAL(10,2) NOT NULL CHECK (salary >= 0)
    );
    """

    insert_sql = f"""
    INSERT INTO `{table_name}` (employee_id, first_name, last_name, department, hire_date, salary)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        first_name = VALUES(first_name),
        last_name  = VALUES(last_name),
        department = VALUES(department),
        hire_date  = VALUES(hire_date),
        salary     = VALUES(salary);
    """

    return create_table_sql, insert_sql


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("json_file", help="Path to a JSON file with MySQL connection settings")
    parser.add_argument("csv_file", help="Path to the employees CSV file to load")
    parser.add_argument("table_name", help="Name of the MySQL table to create/load")
    args = parser.parse_args()

    config = load_config(args.json_file)
    create_table_sql, insert_sql = build_sql(args.table_name)

    password = config.get("password")
    if password is None:
        password = getpass.getpass(f"MySQL password for {config['user']}@{config['host']}: ")

    rows = read_csv_rows(args.csv_file)
    print(f"Read {len(rows)} rows from {args.csv_file}")

    conn = None
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=password,
            database=config["database"],
        )
        cursor = conn.cursor()

        cursor.execute(create_table_sql)
        print(f"Table '{args.table_name}' created (or already existed).")

        cursor.executemany(insert_sql, rows)
        conn.commit()
        print(f"Loaded/updated {cursor.rowcount} row-affecting operations.")

        cursor.execute(f"SELECT COUNT(*) FROM `{args.table_name}`")
        (count,) = cursor.fetchone()
        print(f"Table '{args.table_name}' now has {count} rows.")

        print("\nSample rows:")
        cursor.execute(f"SELECT * FROM `{args.table_name}` ORDER BY employee_id LIMIT 5")
        for r in cursor.fetchall():
            print(r)

        cursor.close()
    except MySQLError as e:
        print(f"MySQL error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    main()
