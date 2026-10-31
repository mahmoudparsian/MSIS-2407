"""
create_mysql_table_load_local.py

Creates a table in MySQL and bulk-loads a CSV file into it using
`LOAD DATA LOCAL INFILE` -- MySQL's native bulk-load statement, which has
the server (not Python) parse and insert every row in one shot. This is
dramatically faster than row-by-row INSERTs for large files, because the
CSV never round-trips through Python row objects at all -- no pandas, and
barely any Python involved beyond opening the connection and issuing SQL.

Connection settings come from an external JSON config file (same shape as
create_mysql_table.py's). See mysql_config.json for the expected format.

Requirements:
    pip install mysql-connector-python

Two switches must BOTH be on for LOCAL INFILE to work, because it lets a
client tell the server "read this file off of MY disk" -- a feature MySQL
disables by default for security reasons:
    1. Client side: this script passes allow_local_infile=True when it
       connects (handled for you below).
    2. Server side: the server's `local_infile` system variable must be
       enabled. This script attempts `SET GLOBAL local_infile = 1`
       automatically, which requires a privileged account (e.g. root with
       SUPER / SYSTEM_VARIABLES_ADMIN). If your account isn't privileged
       enough, ask your DBA to run that statement once, or add
       `local_infile=1` under [mysqld] in my.cnf and restart the server.

Usage:
    python create_mysql_table_load_local.py <json-file> <csv-file> <table-name>

Example:
    python create_mysql_table_load_local.py mysql_config.json employees.csv employees
"""

import argparse
import getpass
import json
import os
import re
import sys

import mysql.connector
from mysql.connector import Error as MySQLError

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


def build_create_table_sql(table_name):
    if not VALID_IDENTIFIER.match(table_name):
        raise ValueError(
            f"Invalid table name {table_name!r}: must start with a letter or "
            "underscore and contain only letters, digits, and underscores."
        )
    return f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        employee_id INT PRIMARY KEY,
        first_name  VARCHAR(50)  NOT NULL,
        last_name   VARCHAR(50)  NOT NULL,
        department  VARCHAR(50)  NOT NULL,
        hire_date   DATE         NOT NULL,
        salary      DECIMAL(10,2) NOT NULL CHECK (salary >= 0)
    );
    """


def build_load_data_sql(csv_path, table_name):
    """Build a LOAD DATA LOCAL INFILE statement for our 6-column employees CSV.

    The file path is not a normal bind parameter in LOAD DATA syntax, so it is
    embedded directly in the SQL text -- we escape backslashes and single
    quotes ourselves (backslashes matter on Windows paths) and always use an
    absolute path to avoid ambiguity about the client's working directory.
    """
    abs_path = os.path.abspath(csv_path)
    escaped_path = abs_path.replace("\\", "\\\\").replace("'", "\\'")

    return f"""
    LOAD DATA LOCAL INFILE '{escaped_path}'
    INTO TABLE `{table_name}`
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\\n'
    IGNORE 1 ROWS
    (employee_id, first_name, last_name, department, hire_date, salary);
    """


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("json_file", help="Path to a JSON file with MySQL connection settings")
    parser.add_argument("csv_file", help="Path to the employees CSV file to bulk-load")
    parser.add_argument("table_name", help="Name of the MySQL table to create/load")
    args = parser.parse_args()

    config = load_config(args.json_file)
    create_table_sql = build_create_table_sql(args.table_name)
    load_data_sql = build_load_data_sql(args.csv_file, args.table_name)

    password = config.get("password")
    if password is None:
        password = getpass.getpass(f"MySQL password for {config['user']}@{config['host']}: ")

    conn = None
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=password,
            database=config["database"],
            allow_local_infile=True,   # client-side switch (see module docstring)
        )
        cursor = conn.cursor()

        cursor.execute(create_table_sql)
        print(f"Table '{args.table_name}' created (or already existed).")

        try:
            cursor.execute("SET GLOBAL local_infile = 1")  # server-side switch
        except MySQLError as e:
            print(
                f"Warning: could not set GLOBAL local_infile=1 automatically ({e}). "
                "If the LOAD DATA step below fails, ask your DBA to enable "
                "local_infile on the server, or set it in my.cnf and restart.",
                file=sys.stderr,
            )

        cursor.execute(load_data_sql)
        conn.commit()
        print(f"LOAD DATA LOCAL INFILE affected {cursor.rowcount} rows.")

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
