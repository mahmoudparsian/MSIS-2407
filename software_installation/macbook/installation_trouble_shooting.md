# MSIS-2407 <br> Installation Troubleshooting (Mac)

[← Setup guide](README.md) · **Troubleshooting**

**Course:** MSIS-2407 — DBMS - Design, Development & Administration  
**Quarter:** Winter 2027  
**Author:** Dr. Mahmoud Parsian

---

## What This Document Is

This document collects fixes for the problems Mac students actually
hit on the first day of class, beyond what's already covered in
[`step_1_install_python.md`](step_1_install_python.md)
and [`step_4_install_mysql.md`](step_4_install_mysql.md). Start
there first — come here when something still isn't working.

If your problem isn't listed here, take a screenshot of the error and
bring it to office hours (see the end of this document).

---

## 1. Installing Homebrew (Only for the Optional Steps)

Homebrew is a package manager for Mac — a tool that installs other
software from the Terminal. You only need it for the **optional Step 4
(MySQL)** and the optional DuckDB command-line tool; the required steps (Python, the four Python packages, and
the Marimo check) don't use it. If `brew --version` already prints a
version number, skip this section.

### Step 1 — Install Homebrew

1. Open **Terminal** (press `Cmd + Space`, type `Terminal`, press Enter)
2. Paste this command and press Enter:

   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. You may be asked for your Mac password. Type it (nothing will show
   on screen as you type — that's normal) and press Enter
4. If a popup asks to install the "Command Line Developer Tools,"
   click **Install** and wait for it to finish before continuing
5. Wait for the install to finish — it can take a few minutes

> **What does that command actually do?** It downloads Homebrew's
> official install script from GitHub and runs it. This is the
> standard, documented way to install Homebrew (see
> [brew.sh](https://brew.sh)) — you are not running a random script
> from a stranger.

### Step 2 — Add Homebrew to Your PATH

Right after Homebrew finishes installing, it prints a message that
looks like **"Next steps"** with 1–2 commands under it. **Run those
commands** — this step is what makes the `brew` command actually work.
If you already closed that message, here's what it says, depending on
your Mac:

**Apple Silicon Mac (M1 / M2 / M3 / M4 — most Macs sold since late 2020):**

```
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Intel Mac (older):**

```
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

> **Not sure which kind of Mac you have?** Click the Apple menu →
> **About This Mac**. If it says "Chip: Apple M1/M2/M3/M4," use the
> Apple Silicon commands. If it says "Processor: Intel," use the Intel
> commands.

**Close Terminal completely** (`Cmd + Q`), reopen it, and type:

```
brew --version
```

If you see a version number (e.g., `Homebrew 4.x.x`), Homebrew is
installed and on your PATH.

---

## 2. Putting Homebrew, Python, Marimo, and DuckDB on Your PATH

**What is PATH?** PATH is a list of folders your Mac's Terminal
searches through when you type a command name. If a program's folder
isn't in that list, Terminal says `command not found` — even though
the program is installed and sitting right there on your disk.

You mostly won't need to do this by hand — the installers in this
course add themselves to PATH automatically. But here's what to do if
one of them doesn't, and where each tool normally lives:

| Tool | Normally added to PATH by | Typical folder |
|------|---------------------------|-----------------|
| Homebrew (`brew`) | Step 2 above | `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/bin` (Intel) |
| Python (`python3`, `pip3`) | the python.org installer | `/usr/local/bin` or `/Library/Frameworks/Python.framework/...` |
| Marimo (`marimo`) | `pip3 install marimo` (Step 2 of the main setup) | wherever `pip3` installs command-line scripts for your Python |
| DuckDB (Python package) | `pip3 install "duckdb>=2.0"` | not a command — it's a Python import, no PATH needed |

**If a command still says "not found" after installing it:**

1. Find out where it actually is:

   ```
   python3 -m site --user-base
   ```

   This prints a folder. The missing command is usually inside a
   `bin` subfolder there.

2. Add that `bin` folder to your PATH by appending an `export` line to
   your shell's startup file. Most Macs today use `zsh`, so edit
   `~/.zprofile`:

   ```
   echo 'export PATH="$HOME/Library/Python/3.12/bin:$PATH"' >> ~/.zprofile
   ```

   (Replace `3.12` with your actual Python version from
   `python3 --version`.)

3. Close Terminal completely (`Cmd + Q`), reopen it, and try the
   command again.

**To check where a command is currently coming from:**

```
which python3
which brew
```

Each should print a file path. If it prints nothing, that tool is not
on your PATH yet.

---

## 3. Getting `step_2_setup_software.py` and `step_3_verification.py` Onto Your Mac

These two files live inside the course's GitHub repository, in this
`macbook` folder (inside `software_installation`). **Step 0** in
[`README.md`](README.md) covers this in full — here's the short
version:

1. Go to **https://github.com/mahmoudparsian/MSIS-2407**
2. Click the green **`< > Code`** button, then **Download ZIP**
3. Find the ZIP in your **Downloads** folder and double-click it to unzip
4. Open the unzipped folder, then open **`software_installation`**,
   then open **`macbook`** — both files are inside

If you only need to re-download these two files specifically (for
example, you deleted them by accident but still have the rest):

1. Go to **https://github.com/mahmoudparsian/MSIS-2407/tree/main/software_installation/macbook**
2. Click on `step_2_setup_software.py`
3. Click the **Download raw file** button (a download-arrow icon
   near the top right of the file view)
4. Repeat for `step_3_verification.py`
5. Move both downloaded files into your `macbook` folder

> **Already comfortable with Git?** `git clone` or `git pull` also
> works, and makes future weeks easier. If that's unfamiliar, ignore
> it — the ZIP is simpler for now.

---

## 4. MySQL Problems (Optional Step 4)

**Symptom:** `mysql: command not found`, or
`ERROR 2002 (HY000): Can't connect to local MySQL server`.

This is almost always one of two things: MySQL's command-line tools
aren't on your PATH, or the server isn't running.

### `mysql: command not found`

Homebrew installs MySQL's command-line tools without always adding
them to PATH:

```
echo 'export PATH="/opt/homebrew/opt/mysql/bin:$PATH"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

(Intel Mac: use `/usr/local/opt/mysql/bin` instead.) Close Terminal
completely, reopen it, and try `mysql --version` again.

### `Can't connect to local MySQL server`

The server process isn't running. Start it:

```
brew services start mysql
```

Check it took effect:

```
brew services list
```

You should see `mysql` listed as `started`. If it shows `error` or
`none`, try `brew services restart mysql` and check
`brew services info mysql` for details.

### Forgot the root password

See the "I set a root password and forgot it" section in
[`step_4_install_mysql.md`](step_4_install_mysql.md#troubleshooting) —
it walks through resetting it with `--skip-grant-tables`.

For this course, an empty root password (the Homebrew default) is
fine — you don't need to set one at all unless you want the practice.

### `ModuleNotFoundError: No module named 'mysql'` when running the Week 3 walkthrough

The MySQL server is fine — Python just doesn't have the connector
package yet. Install it with the same Python you use for the course:

```
python3 -m pip install mysql-connector-python
```

If you get `externally-managed-environment`, add
`--break-system-packages` to that command, just as
`step_2_setup_software.py` does for the other packages.

### `Access denied for user 'root'@'localhost'` from the Week 3 walkthrough

The walkthrough's `mysql_config.json` still has the placeholder
password `your_password`. Put your own MySQL password there, or delete
the `"password"` line and the script will ask you for it when it runs.

---

## Other Common Problems

### A popup interrupted the Homebrew install asking about "Command Line Developer Tools"

This is normal and expected the first time you install Homebrew on a
Mac. Click **Install**, wait for the small installer to finish (a few
minutes), then re-run the Homebrew command from Step 1 above if it
didn't continue on its own.

### "zsh: command not found: brew" right after installing Homebrew

You installed Homebrew but skipped the PATH step. Go back to **Step 2**
above and run the two commands Homebrew printed for you.

### "xcrun: error: invalid active developer path" when running `brew` or `pip3`

This means the Xcode Command Line Tools are missing or broke, often
after a macOS update. Fix it by reinstalling them:

```
xcode-select --install
```

Click **Install** in the popup that appears and wait for it to finish.
If that command says the tools are "already installed" but the error
keeps happening, reset and reinstall:

```
sudo xcode-select --reset
xcode-select --install
```

### Homebrew (or a PATH change) fails with a permissions error, and this is a school-managed laptop

If your Mac is managed by SCU IT (an MDM profile, or you don't know
your own admin password), Homebrew and some PATH changes need admin
rights you may not have. This isn't something you can fix from the
Terminal — bring it to office hours so Dr. Parsian can help you find a
workaround or get an IT exception.

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
sandboxed. Look at the Terminal output — Marimo prints a line like
`http://localhost:2718/?access_token=...`. Copy that whole address and
paste it into any browser's address bar by hand.

### The unzipped folder looks empty, or I can't find `macbook` inside it

Make sure you fully unzipped the file rather than just previewing it —
double-clicking a `.zip` on a Mac should extract it automatically into
a real folder sitting next to the `.zip`. If you see a folder with a
zipper icon, it isn't extracted yet; double-click it again. The real
folder is named **`MSIS-2407-main`**, and `macbook` is inside its
`software_installation` folder.

### Marimo says "The following packages are required to execute sql: sqlglot"

Marimo needs a package called **sqlglot** to run SQL cells — it's
separate from DuckDB and doesn't get installed automatically with it.
Fix it from Terminal:

```
pip3 install sqlglot
```

If that fails with an `externally-managed-environment` error, add the
same flag `step_2_setup_software.py` uses:

```
pip3 install --break-system-packages sqlglot
```

Then close Marimo completely and reopen it. This should already be
installed if you ran `step_2_setup_software.py` (Step 2) — if you see
this error, run that script again to confirm all four packages show
`[+] PASS`.

### macOS says an app (such as the lock-down browser) is from an "unidentified developer"

This is Gatekeeper, a macOS security feature — not a broken download.

1. Go to **System Settings → Privacy & Security**
2. Scroll down to the message about the blocked app
3. Click **"Open Anyway"**
4. Click **Open** in the confirmation dialog

### `curl` or `pip3 install` fails with an SSL / certificate error

This usually happens on school or coffee-shop Wi-Fi that intercepts
secure connections (common on eduroam-style networks with a captive
portal or security software). Try:

- Switching to a different network (phone hotspot works well to test)
- If you're on a VPN, temporarily turning it off
- Retrying — some campus networks are just briefly unreliable

### My terminal doesn't show the `macbook` folder when I run `ls`

Your Terminal isn't pointed at the right folder. Redo the drag-and-drop
trick in **Step 0** of [`README.md`](README.md) — type `cd ` (with a
trailing space), drag the `macbook` folder from Finder onto the
Terminal window, then press Enter.

### I have more than one Python installed and things behave inconsistently

Check which one you're actually using:

```
which python3
```

If it doesn't point at the Python you installed in Step 1 (usually
under `/Library/Frameworks/Python.framework/` or `/usr/local/bin/`),
see the "I installed packages but Python can't find them" section in
[`step_1_install_python.md`](step_1_install_python.md#troubleshooting).

### Everything from Step 1/Step 2 troubleshooting

Package install errors (`externally-managed-environment`, permission
denied, `pip3` not found, Marimo not launching) are covered in
[`step_1_install_python.md`](step_1_install_python.md#troubleshooting)
— check there first if your problem is about Python packages rather
than Homebrew or MySQL.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Install Homebrew | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Add Homebrew to PATH (Apple Silicon) | `eval "$(/opt/homebrew/bin/brew shellenv)"` |
| Add Homebrew to PATH (Intel) | `eval "$(/usr/local/bin/brew shellenv)"` |
| Check Homebrew is on PATH | `brew --version` |
| Check where a command lives | `which <command>` |
| Fix broken Xcode Command Line Tools | `xcode-select --install` |
| Fix Marimo's "sqlglot" error | `pip3 install sqlglot` |
| Start the MySQL server | `brew services start mysql` |
| Check MySQL server status | `brew services list` |
| Install the MySQL Python connector | `python3 -m pip install mysql-connector-python` |
| Add MySQL's CLI tools to PATH | `echo 'export PATH="/opt/homebrew/opt/mysql/bin:$PATH"' >> ~/.zprofile` |

---

## Getting Help

If you've tried the steps above and are still stuck:

1. Take a **screenshot** of the error message
2. Note your **macOS version** (Apple menu → About This Mac) and
   whether your Mac is **Apple Silicon or Intel**
3. Bring both to **office hours** (see
   [`course_information/QUESTIONS_and_OFFICE_HOURS.md`](../../course_information/QUESTIONS_and_OFFICE_HOURS.md))
   or post on **Camino Discussions**

---

*MSIS-2407 — DBMS - Design, Development & Administration — Winter 2027*
