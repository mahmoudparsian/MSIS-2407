# MSIS-2407 <br> How to Install MySQL (Mac)

[← Setup guide](README.md) · **Step 4 (optional)**

**Course:** MSIS-2407 — DBMS - Design, Development & Administration  
**Quarter:** Winter 2027  
**Author:** Dr. Mahmoud Parsian  

---

## What Is MySQL?

MySQL is a **client–server** relational database — a real database
*server* runs in the background on your computer, and you connect to
it as a client, the same way you'd connect to a database on a company
server. This is different from DuckDB, which runs entirely inside
Python with no server at all.

> **This step is optional.** No lab and no exam question needs MySQL —
> every lab runs on DuckDB. You only need MySQL to run the **Week 3
> walkthrough** yourself
> ([`week3_database_implementation/load_csv_to_table_mysql/`](../../week3_database_implementation/load_csv_to_table_mysql/README.md)),
> which loads a CSV file into MySQL from Python.
>
> **Already installed MySQL for MSIS-2402?** Skip to **Step 2** below to
> check the server still runs, then do the **Python connector** step —
> that part is new for MSIS-2407.

Week 3 compares DuckDB with MySQL: multi-user concurrency, locking,
user accounts, and a real client–server architecture — see the
DuckDB-vs-MySQL table in
[`course_information/REQUIRED_SOFTWARE.md`](../../course_information/REQUIRED_SOFTWARE.md).

| Item | Requirement |
|------|-------------|
| Software | MySQL Community Server (free, open-source) |
| Operating system | macOS |
| Internet connection | Required for download |
| Disk space | ~500 MB |

---

## Step 1 — Install MySQL with Homebrew

1. Open **Terminal** (press `Cmd + Space`, type `Terminal`, press Enter)
2. If you don't already have Homebrew (check with `brew --version`),
   install it:

   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. Install MySQL:

   ```
   brew install mysql
   ```

4. Start the MySQL server:

   ```
   brew services start mysql
   ```

   This starts MySQL now **and** sets it to start automatically every
   time you log in, so you won't need to repeat this step.

---

## Step 2 — Verify the Server Is Running

```
mysql --version
```

You should see something like `mysql  Ver 9.x.x for macos ...`.

A fresh Homebrew install of MySQL has **no root password set yet** —
you can connect right away:

```
mysql -u root
```

You should land at a `mysql>` prompt. That prompt **is** the
verification — it means the server is running and accepting
connections.

---

## Step 3 — Quick Test

At the `mysql>` prompt, type:

```sql
SELECT 'Hello, MSIS-2407!' AS greeting, 42 AS answer;
```

Press Enter. You should see a small result table containing
`Hello, MSIS-2407!` and `42`.

Now try one that actually stores something:

```sql
CREATE DATABASE IF NOT EXISTS sample_db;
USE sample_db;

CREATE TABLE test_students (
    student_id INT,
    name       VARCHAR(50),
    gpa        DECIMAL(3,2)
);

INSERT INTO test_students VALUES
    (1, 'Alice', 3.80),
    (2, 'Bob',   3.20);

SELECT * FROM test_students;
```

You should see Alice and Bob. Type `exit` to leave the `mysql>` prompt.

---

## Step 4 — Install the Python Connector

The Week 3 walkthrough talks to MySQL from Python, so it needs one more
package. In Terminal, type:

```
python3 -m pip install mysql-connector-python
```

Check it:

```
python3 -c "import mysql.connector; print(mysql.connector.__version__)"
```

You should see a version number such as `9.x.x`. Before you run the
walkthrough, put **your** MySQL password into its `mysql_config.json`
(or delete the `"password"` line and the script will ask for it) — its
`README.md` explains how.

---

## Troubleshooting

### `mysql: command not found`

Homebrew installs MySQL's command-line tools without always adding
them to your PATH. Add them by hand:

```
echo 'export PATH="/opt/homebrew/opt/mysql/bin:$PATH"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

(On an Intel Mac, use `/usr/local/opt/mysql/bin` instead of
`/opt/homebrew/opt/mysql/bin`.) Close Terminal completely, reopen it,
and try `mysql --version` again.

### `ERROR 2002 (HY000): Can't connect to local MySQL server`

The server isn't running. Start it:

```
brew services start mysql
```

Check its status with:

```
brew services list
```

You should see `mysql` listed as `started`.

### I set a root password and forgot it, or `mysql -u root` now asks for one I never set

Reset it:

```
brew services stop mysql
mysqld_safe --skip-grant-tables &
mysql -u root
```

(If `mysql -u root` says it can't connect, wait a few seconds and run it
again — the temporary server takes a moment to start.)

At the `mysql>` prompt:

```sql
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';
exit
```

Then shut down the temporary server — it asks for the **new** password —
and start MySQL normally:

```
mysqladmin -u root -p shutdown
brew services start mysql
```

For this course, an empty root password is fine — you don't need to
set one unless you want the practice.

### Port 3306 is already in use

Something else (an old MySQL install, XAMPP, Docker, etc.) is already
using MySQL's default port. Bring this to office hours rather than
guessing — the fix depends on what's already running.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Install MySQL | `brew install mysql` |
| Start the server | `brew services start mysql` |
| Stop the server | `brew services stop mysql` |
| Check server status | `brew services list` |
| Check MySQL version | `mysql --version` |
| Connect as root | `mysql -u root` |
| Exit the `mysql>` prompt | `exit` |
| Install the Python connector | `python3 -m pip install mysql-connector-python` |

---

## Getting Help

If you've tried the troubleshooting steps above and are still stuck:

1. Take a **screenshot** of the error message
2. Note your **macOS version**
3. Bring both to **office hours** or post on **Camino Discussions**

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
