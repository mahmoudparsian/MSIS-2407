# MSIS-2407 <br> Installation Troubleshooting (Windows)

[← Setup guide](README.md) · **Troubleshooting**

**Course:** MSIS-2407 — DBMS - Design, Development & Administration  
**Quarter:** Winter 2027  
**Author:** Dr. Mahmoud Parsian

---

## What This Document Is

This document collects fixes for the problems Windows students
actually hit on the first day of class, beyond what's already covered
in [`step_1_install_python.md`](step_1_install_python.md)
and [`step_4_install_mysql.md`](step_4_install_mysql.md). Start
there first — come here when something still isn't working.

If your problem isn't listed here, take a screenshot of the error and
bring it to office hours (see the end of this document).

---

## 1. Putting Python, Marimo, and DuckDB on Your PATH

**What is PATH?** PATH is a list of folders Windows searches through
when you type a command name. If a program's folder isn't in that
list, Command Prompt says `'x' is not recognized as an internal or
external command` — even though the program is installed and sitting
right there on your disk.

You mostly won't need to do this by hand — the installers in this
course add themselves to PATH automatically **if you check the right
box during install**. But here's what to do if one of them didn't,
and where each tool normally lives:

| Tool | Added to PATH by | Typical folder |
|------|-------------------|-----------------|
| Python (`python`, `pip`) | checking **"Add python.exe to PATH"** during install (Step 1 of the main setup) | `C:\Users\YourName\AppData\Local\Programs\Python\Python312\` |
| Marimo (`marimo`) | `pip install marimo` (Step 2 of the main setup) | `...\Python312\Scripts\` |
| DuckDB (Python package) | `pip install "duckdb>=2.0"` | not a command — it's a Python import, no PATH needed |

**If a command still says "not recognized" after installing it,** add
its folder to PATH by hand:

1. Press `Win`, type **"environment variables"**, and open **"Edit
   environment variables for your account"**
2. Under the top box ("User variables"), click **Path**, then **Edit**
3. Click **New** and paste in the folder that's missing (for example,
   `C:\Users\YourName\AppData\Local\Programs\Python\Python312\Scripts\`)
4. Click **OK** on all three windows
5. **Close Command Prompt completely and reopen it** — PATH changes
   only take effect in new windows

**To check where a command is currently coming from:**

```
where python
where marimo
```

Each should print a file path. If it prints nothing, that tool is not
on your PATH yet.

---

## 2. Getting `step_2_setup_software.py` and `step_3_verification.py` Onto Your Windows Laptop

These two files live inside the course's GitHub repository, in this
`windows` folder (inside `software_installation`). **Step 0** in
[`README.md`](README.md) covers this in full — here's the short
version:

1. Go to **https://github.com/mahmoudparsian/MSIS-2407**
2. Click the green **`< > Code`** button, then **Download ZIP**
3. Find the ZIP in your **Downloads** folder, right-click it, and
   choose **Extract All...**
4. Open the extracted folder, then open **`software_installation`**,
   then open **`windows`** — both files are inside

> **Extract the ZIP somewhere outside OneDrive if you can** (for
> example, `C:\MSIS-2407\` instead of your OneDrive Desktop or
> Documents). See the OneDrive note under "Other Common Problems"
> below — it explains why this avoids a common Windows-specific
> problem.

If you only need to re-download these two files specifically (for
example, you deleted them by accident but still have the rest):

1. Go to **https://github.com/mahmoudparsian/MSIS-2407/tree/main/software_installation/windows**
2. Click on `step_2_setup_software.py`
3. Click the **Download raw file** button (a download-arrow icon
   near the top right of the file view)
4. Repeat for `step_3_verification.py`
5. Move both downloaded files into your `windows` folder

> **Already comfortable with Git?** `git clone` or `git pull` also
> works, and makes future weeks easier. If that's unfamiliar, ignore
> it — the ZIP is simpler for now.

---

## 3. MySQL Problems (Optional Step 4)

**Symptom:** `'mysql' is not recognized as an internal or external
command`, or `ERROR 2003 (HY000): Can't connect to MySQL server on
'localhost'`.

This is almost always one of two things: MySQL's `bin` folder isn't
on your PATH, or the MySQL Windows service isn't running.

### `'mysql' is not recognized`

Add MySQL's `bin` folder to PATH by hand:

1. Press `Win`, type **"environment variables"**, and open **"Edit
   environment variables for your account"**
2. Under **User variables**, click **Path**, then **Edit**
3. Click **New** and paste in:

   ```
   C:\Program Files\MySQL\MySQL Server 8.4\bin
   ```

   (Check File Explorer if your installed version number differs.)
4. Click **OK** on all three windows, then **close Command Prompt
   completely and reopen it**

### `Can't connect to MySQL server on 'localhost'`

The MySQL Windows service isn't running:

1. Press `Win`, type **"services"**, and open **Services**
2. Find **MySQL84** (or similar) in the list
3. Right-click it and choose **Start**

Right-click it and choose **Properties** to set **Startup type** to
**Automatic** so it starts on its own from now on.

### Forgot the root password

See the "I forgot my root password" section in
[`step_4_install_mysql.md`](step_4_install_mysql.md#troubleshooting) —
it walks through resetting it with MySQL's `--init-file` method. This is
easier to do in person; bring it to office hours if it feels like a
lot to follow alone.

### `ModuleNotFoundError: No module named 'mysql'` when running the Week 3 walkthrough

The MySQL server is fine — Python just doesn't have the connector
package yet. Install it with the same Python you use for the course:

```
python -m pip install mysql-connector-python
```

### `Access denied for user 'root'@'localhost'` from the Week 3 walkthrough

The walkthrough's `mysql_config.json` still has the placeholder
password `your_password`. Put your own MySQL password there, or delete
the `"password"` line and the script will ask you for it when it runs.

---

## Other Common Problems

### Files behave strangely, won't save, or give permission errors inside a OneDrive folder

If your Desktop or Documents folder is synced with OneDrive (common on
school-managed laptops), OneDrive can lock files while it's syncing
them, which shows up as confusing "permission denied" or "file in
use" errors while Python or pip is working. If you keep hitting
unexplained errors, move the `software_installation` folder to a
non-synced location, such as `C:\MSIS-2407\`, and work from there.

### "python" is not recognized, or the Microsoft Store opens instead

These are Python PATH issues — see the full fix in
[`step_1_install_python.md`](step_1_install_python.md#troubleshooting).

### "pip" is not recognized

Same root cause as "python is not recognized" above — Python (and the
`Scripts` folder pip lives in) isn't on PATH, usually from skipping
"Add python.exe to PATH" during install. If `python` itself works but
`pip` doesn't, you can also sidestep it with
`python -m pip install <package>` instead of `pip install <package>`.
Full fix: [`step_1_install_python.md`](step_1_install_python.md#troubleshooting).

### `winget` command not found

Open the **Microsoft Store**, search for **"App Installer"**, and
install or update it — this is what provides `winget`. Restart
Command Prompt afterward. (`winget` is only used for the optional
DuckDB command-line tool; nothing required depends on it.)

### "Windows protected your PC" (SmartScreen) when opening an installer

This appears on the Python, MySQL, or lock-down browser installer because
it isn't from one of the handful of vendors Windows recognizes by
default — it doesn't mean the file is unsafe. Click **"More info"**,
then click **"Run anyway"**.

### My antivirus / school-managed laptop is blocking an installer

Some school-managed Windows laptops restrict running `.exe` or `.msi`
installers, or flag them for review. If an installer silently does
nothing, or is blocked with a message from your antivirus or IT
department, you may need administrator rights you don't have on a
managed machine. Bring this to office hours — Dr. Parsian can help you
find an alternative (e.g., a portable install, or IT help).

### Marimo says "The following packages are required to execute sql: sqlglot"

Marimo needs a package called **sqlglot** to run SQL cells — it's
separate from DuckDB and doesn't get installed automatically with it.
Fix it from Command Prompt:

```
pip install sqlglot
```

Then close Marimo completely and reopen it. This should already be
installed if you ran `step_2_setup_software.py` (Step 2) — if you see
this error, run that script again to confirm all four packages show
`[+] PASS`.

### Downloaded a new Python and package installs suddenly fail to build

If you installed the very newest Python version (released within the
last few weeks), some packages this course needs may not have a
ready-made install for it yet, and `pip` tries to compile it from
scratch — which fails without extra developer tools. Simplest fix:
uninstall it and install **Python 3.12** instead (still meets the
3.11+ requirement, and everything has ready-made installs for it). See
[`step_1_install_python.md`](step_1_install_python.md).

### `marimo edit` doesn't open a browser tab by itself

This can happen if your default browser is unusual or the app is
sandboxed. Look at the Command Prompt output — Marimo prints a line
like `http://localhost:2718/?access_token=...`. Copy that whole
address and paste it into any browser's address bar by hand.

### The folder looks empty, or I can't find `windows` inside it

Make sure you used **Extract All** (right-click the `.zip` →
**Extract All...**) rather than just double-clicking to peek inside —
double-clicking opens a "compressed folder" preview that *looks* like
a real folder but isn't, and running scripts from inside it fails in
confusing ways. The real, extracted folder is named
**`MSIS-2407-main`**, and `windows` is inside its `software_installation`
folder.

### `curl` or `pip install` fails with an SSL / certificate error

This usually happens on school or coffee-shop Wi-Fi that intercepts
secure connections (common on eduroam-style networks with a captive
portal or security software). Try:

- Switching to a different network (phone hotspot works well to test)
- If you're on a VPN, temporarily turning it off
- Retrying — some campus networks are just briefly unreliable

### My Command Prompt doesn't show the `windows` folder when I run `dir`

Your Command Prompt isn't pointed at the right folder. Redo the
address-bar trick in **Step 0** of [`README.md`](README.md) — click
the address bar in File Explorer while inside the `windows` folder,
type `cmd`, and press Enter.

### A path is "too long" error while installing or unzipping

Older Windows versions can fail on file paths longer than 260
characters. Extract the ZIP closer to your drive root (for example,
`C:\MSIS-2407\` instead of several folders deep inside Downloads) to
keep the full path short.

### Everything from Step 1/Step 2 troubleshooting

Package install errors (permission denied, `pip` not found, Marimo not
launching, multiple Python installs) are covered in
[`step_1_install_python.md`](step_1_install_python.md#troubleshooting)
— check there first if your problem is about Python packages rather
than MySQL.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Check where a command lives / list every copy on PATH | `where python` / `where marimo` |
| Open environment variables editor | `Win` key → search "environment variables" |
| Fix Marimo's "sqlglot" error | `pip install sqlglot` |
| Start the MySQL service | **Services** app → `MySQL84` → Start |
| Install the MySQL Python connector | `python -m pip install mysql-connector-python` |
| MySQL `bin` folder (typical) | `C:\Program Files\MySQL\MySQL Server 8.4\bin` |

---

## Getting Help

If you've tried the steps above and are still stuck:

1. Take a **screenshot** of the error message
2. Note your **Windows version** (Settings → System → About)
3. Bring both to **office hours** (see
   [`course_information/QUESTIONS_and_OFFICE_HOURS.md`](../../course_information/QUESTIONS_and_OFFICE_HOURS.md))
   or post on **Camino Discussions**

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
