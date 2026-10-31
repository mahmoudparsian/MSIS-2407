# Loading a CSV file into MySQL from Python

Two scripts that load `employees.csv` into a MySQL table:

- `create_mysql_table_with_insert.py` — creates the table and inserts the rows
  with parameterized `INSERT` statements.
- `create_mysql_table_load_local.py` — creates the table and bulk-loads the file
  with `LOAD DATA LOCAL INFILE`.

The `.log` files show a sample run of each.

## Before you run them

You need MySQL Community Server running and:

```bash
pip install mysql-connector-python
```

**Set your own connection details in `mysql_config.json`.** It ships with the
placeholder `"password": "your_password"` — replace it with **your** MySQL
password, or delete the `"password"` line and the script will ask for it when
it runs (nothing is stored on disk that way).

Never commit or share a config file that contains a real password.

## Run

From this folder:

```bash
python create_mysql_table_with_insert.py mysql_config.json employees.csv employees
python create_mysql_table_load_local.py  mysql_config.json employees.csv employees2
```

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
