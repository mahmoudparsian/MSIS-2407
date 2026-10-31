# MSIS-2407 <br> How to Install MySQL (Windows)

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
> **Already installed MySQL for MSIS-2402?** Skip to **Step 4** below to
> check the server still runs, then do the **Python connector** step —
> that part is new for MSIS-2407.

Week 3 compares DuckDB with MySQL: multi-user concurrency, locking,
user accounts, and a real client–server architecture — see the
DuckDB-vs-MySQL table in
[`course_information/REQUIRED_SOFTWARE.md`](../../course_information/REQUIRED_SOFTWARE.md).

| Item | Requirement |
|------|-------------|
| Software | MySQL Community Server **8.4 LTS** (free, open-source) |
| Operating system | Windows 10 or Windows 11 |
| Internet connection | Required for download |
| Disk space | ~500 MB |

> **Why 8.4?** It is a *Long-Term Support* (LTS) release — stable and
> supported for years. A newer LTS (such as 9.7) also works; just
> replace `8.4` / `84` with your version in the folder and service
> names below.

---

## Step 1 — Download the MySQL Installer

1. Open your web browser and go to:
   **https://dev.mysql.com/downloads/mysql/**
2. In the version list, choose **8.4.x LTS**
3. Under **Microsoft Windows**, find **Windows (x86, 64-bit), MSI
   Installer** and click **Download**
4. If prompted to sign in or create an Oracle account, look for a
   small link near the bottom that says **"No thanks, just start my
   download."** — no account is required

> **Don't use the older "MySQL Installer" page.** That tool only
> installs MySQL 8.0, which is no longer supported. The MSI above is
> the current way to install MySQL on Windows.

---

## Step 2 — Run the Installer

1. Open the downloaded `.msi` file
2. If you see **"Windows protected your PC,"** click **"More info,"**
   then **"Run anyway"** — this is normal for installers from smaller
   vendors, not a sign of a broken download
3. Accept the license, choose the **Typical** setup type, and click
   **Install**. If Windows asks *"Do you want to allow this app to make
   changes to your device?"*, click **Yes**
4. On the last screen, leave **"Run MySQL Configurator"** checked and
   click **Finish** — the server won't start until it has been
   configured

## Step 3 — Configure the Server (MySQL Configurator)

MySQL Configurator opens automatically. Its pages appear in this order;
the defaults are right for this course unless noted:

1. **Type and Networking** — keep the defaults (port `3306`) and click
   **Next**
2. **Accounts and Roles** — enter a **root password** in both boxes and
   **write it down** somewhere you won't lose it. Something simple like
   `msis2407` is fine for this course
3. **Windows Service** — keep **"Configure MySQL Server as a Windows
   Service"** and **"Start the MySQL Server at System Startup"** checked.
   The service name defaults to **`MySQL84`**
4. Click **Next** through the remaining pages, then **Execute** on
   **Apply Configuration**
5. Click **Finish** when every item shows a green check

---

## Step 4 — Verify the Server Is Running

MySQL is now a Windows **service** that starts automatically every time
you log in — you don't need to start it by hand.

1. Open **Command Prompt** (press `Win`, type `cmd`, press Enter)
2. Type:

   ```
   mysql --version
   ```

   You should see something like `mysql  Ver 8.4.x for Win64 ...`.

3. Connect as root:

   ```
   mysql -u root -p
   ```

   Type the password you set in Step 3 and press Enter. You should
   land at a `mysql>` prompt — that prompt **is** the verification.

> **`mysql` is not recognized?** The MSI doesn't always add MySQL to
> PATH — see Troubleshooting below.

---

## Step 5 — Quick Test

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

## Step 6 — Install the Python Connector

The Week 3 walkthrough talks to MySQL from Python, so it needs one more
package. In Command Prompt, type:

```
python -m pip install mysql-connector-python
```

Check it:

```
python -c "import mysql.connector; print(mysql.connector.__version__)"
```

You should see a version number such as `9.x.x`. Before you run the
walkthrough, put **your** MySQL password into its `mysql_config.json`
(or delete the `"password"` line and the script will ask for it) — its
`README.md` explains how.

---

## Troubleshooting

### `'mysql' is not recognized as an internal or external command`

MySQL's `bin` folder isn't on your PATH. Add it by hand:

1. Press `Win`, type **"environment variables"**, and open **"Edit
   environment variables for your account"**
2. Under **User variables**, click **Path**, then **Edit**
3. Click **New** and paste in:

   ```
   C:\Program Files\MySQL\MySQL Server 8.4\bin
   ```

   (Check **File Explorer** if your version number differs.)
4. Click **OK** on all three windows
5. **Close Command Prompt completely and reopen it**, then try
   `mysql --version` again

### `ERROR 2003 (HY000): Can't connect to MySQL server on 'localhost'`

The MySQL service isn't running. Start it:

1. Press `Win`, type **"services"**, and open **Services**
2. Find **MySQL84** (or similar) in the list
3. Right-click it and choose **Start**

To make sure it always starts automatically, right-click it, choose
**Properties**, and set **Startup type** to **Automatic**.

If **MySQL84** isn't in the list at all, the configuration step didn't
finish: open **MySQL Configurator** from the Start menu and complete
Step 3.

### I forgot my root password

This uses MySQL's documented reset method. It's easier in person —
bring it to office hours if it feels like a lot to follow alone.

1. Open **Services** (see above) and **Stop** the **MySQL84** service
2. Open **Notepad** and type this one line, with your new password:

   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';
   ```

   Save it as `C:\mysql-init.txt` (in **Save as type**, choose **All
   Files** so Notepad doesn't add `.txt` twice)
3. Open Command Prompt **as Administrator** and go to the MySQL `bin`
   folder:

   ```
   cd "C:\Program Files\MySQL\MySQL Server 8.4\bin"
   ```

4. Start the server once with the reset file:

   ```
   mysqld --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.4\my.ini" --init-file=C:\mysql-init.txt --console
   ```

   Wait until it prints `ready for connections`, then press `Ctrl + C`
   to stop it
5. **Delete** `C:\mysql-init.txt` — it contains your password
6. **Start** the **MySQL84** service again from **Services**, and log in
   with `mysql -u root -p` and the new password

### Port 3306 is already in use

Something else (an old MySQL install, XAMPP, Docker, etc.) is already
using MySQL's default port. Bring this to office hours rather than
guessing — the fix depends on what's already running.

---

## Quick Reference Card

| Task | How |
|------|-----|
| Check MySQL version | `mysql --version` |
| Connect as root | `mysql -u root -p` |
| Exit the `mysql>` prompt | `exit` |
| Install the Python connector | `python -m pip install mysql-connector-python` |
| Start/stop the server | **Services** app → `MySQL84` → Start/Stop |
| Change server settings later | Start menu → **MySQL Configurator** |
| MySQL `bin` folder (typical) | `C:\Program Files\MySQL\MySQL Server 8.4\bin` |

---

## Getting Help

If you've tried the troubleshooting steps above and are still stuck:

1. Take a **screenshot** of the error message
2. Note your **Windows version** (Settings → System → About)
3. Bring both to **office hours** or post on **Camino Discussions**

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
