---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 26px; }
  section.lead h1 { font-size: 2.2em; }
  table { font-size: 0.75em; }
  pre, code { font-size: 0.75em; }
  h1 { color: #1a3e6f; }
  h2 { color: #1a3e6f; }
---

<!-- _class: lead -->

# Relational Data Modeling
## A Simple, Step-by-Step Introduction Using a Bookstore, in DuckDB

MSIS-2407 — Week 1, Data Modeling (Case Study 2 of 3)

---

# Learning Objectives & Agenda

By the end of this module you will be able to: turn plain-English requirements into **entities, attributes, and relationships**; build a small **conceptual model** (ER diagram); understand **why normalization matters** by watching real anomalies get fixed (flat table → 1NF → 2NF → 3NF); produce a finished **logical schema** with keys and integrity rules; and implement it as a **physical model in DuckDB**.

This is the second of three case studies: it follows the 3-table music-catalog warm-up, and a third, larger case study (an e-commerce platform with 15 tables, many-to-many relationships, and self-referencing hierarchies) builds directly on the vocabulary and steps introduced here.

---

# Learning Objectives & Agenda (cont.)

**Agenda:** 

1. why data modeling
2. the business story — PageTurner Books
3. conceptual modeling
4. normalization
5. the logical schema
6. the physical model in DuckDB
7. sample data and business questions
8. summary and exercises.

---

# Why Data Modeling? Three Models, One Truth

We move through three levels of abstraction, each answering a different question:

| Level | Question it answers | Artifact |
|---|---|---|
| **Conceptual** | *What* things matter to the business, and how do they relate? | Entity-Relationship Diagram |
| **Logical** | *How* do we structure that, independent of any specific product? | Normalized tables, keys, functional dependencies |
| **Physical** | *Where and how exactly* is it stored and enforced? | DDL in a specific engine — here, DuckDB |

A good model is **traceable**: every table, column, and constraint should trace back to a specific business requirement. We'll hold ourselves to that standard throughout.

DuckDB is used as our target engine because it is a fully standards-compliant relational database (`PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, `ENUM`) that needs no server setup — every statement in this deck was actually executed, live, against DuckDB 1.5.

---

# Part 1: The Business Story — Meet PageTurner Books

PageTurner Books is a small independent bookstore that has started selling online. Until now, the owner has tracked everything in a single spreadsheet. As the catalog and order volume grow, she's asked you to design a proper relational database.

**What she's told you, in her own words** — condensed into eight numbered requirements on the next two slides. We'll refer back to these requirement numbers (R1–R8) throughout the rest of this deck, exactly the way you should in your own modeling work: every design decision should be justifiable by pointing at a specific requirement.

---

# Business Requirements — R1 to R4

> **R1.** Every book has a unique ISBN, a title, a price, a publication year, and a genre. A price can never be negative.
>
> **R2.** To keep things simple for this catalog, each book has exactly **one** author on record and is published by exactly **one** publisher. (In real life a book can have several co-authors — we'll model that many-to-many pattern properly in the next case study. For now: one book, one author, one publisher.) The same author can have written several books, and the same publisher can have published several books.
>
> **R3.** Customers register with a unique email address, used to log in.
>
> **R4.** A customer can place many orders over time, but every order must belong to exactly one customer.

---

# Business Requirements — R1 to R4 (cont.)

**Modeling signal:** 

* R1 → a `CHECK` constraint and a natural key (ISBN). 
* R2 → two separate one-to-many relationships (Author→Book, Publisher→Book) — deliberately **not** many-to-many, to keep this first model simple. 
* R3 → a uniqueness constraint. 
* R4 → mandatory participation on one side, optional on the other (a customer can exist with zero orders).

---

# Business Requirements — R5 to R8

> **R5.** An order moves through a simple lifecycle: `PENDING → SHIPPED → DELIVERED`, with `CANCELLED` as a possible side-exit at any point.
>
> **R6.** An order can contain **one or more books**, and the same book can appear on many different orders. Each line of an order records how many copies were purchased and **the price at the moment of that sale** — this must be preserved even if the book's catalog price changes later.
>
> **R7.** Order quantities must be positive whole numbers. No price anywhere (a book's catalog price, or the price recorded on an order line) may be negative.
>
> **R8.** Every order line must point to a real order and a real book — the database should never allow a "floating" line item.

---

# Business Requirements — R5 to R8 (cont.)

**Modeling signal:** 

* R5 → a controlled vocabulary (`ENUM`). 
* R6 → the relationship between Order and Book carries its own data (quantity, historical price), so it needs its own entity. 
* R7 → `CHECK` constraints. 
* R8 → mandatory foreign keys, i.e., referential integrity enforced by the database itself, not just the application.

We now translate R1–R8 into a conceptual model.

---

# Part 2: Conceptual Modeling — Step 1, Identify Entities (Noun Extraction)

> Translate R1–R8 into a conceptual model

The technique: read the requirements and underline every noun that the business describes with attributes and refers to repeatedly. Verbs connecting two nouns are usually relationships.

---

# Part 2: Conceptual Modeling — Step 1, Identify Entities (Noun Extraction) (cont.)

| Entity | Business meaning | Source rule(s) |
|---|---|---|
| Author | A person who writes books | R2 |
| Publisher | A company that publishes books | R2 |
| Book | An item in the catalog | R1, R2 |
| Customer | A registered shopper | R3, R4 |
| Order | A purchase transaction | R4, R5 |
| (Order contains Book) | The relationship itself carries data (quantity, sale price) | R6 |

That last row is a preview of an important idea: when a **relationship has its own attributes**, it becomes its own entity — here, `order_items`.

---

# Step 2 — Identify Attributes (Author, Publisher, Book)

**Author** 

* `author_id` *(surrogate key)*, 
* `first_name`, 
* `last_name`

**Publisher** 

* `publisher_id` *(surrogate key)*, 
* `publisher_name` *(natural, unique)*, 
* `city`

**Book**

- `book_id` *(surrogate key — internal, meaningless, stable)*
- `isbn` *(natural key — meaningful to the business, marked `UNIQUE`, R1)*
- `title`, 
- `publication_year`, 
- `genre`
- `price` *(must be ≥ 0, R1)*
- `owning author`, `owning publisher` *(become foreign keys once relationships are modeled)*

**Design decision:** just like in a larger catalog, we keep **both** a surrogate key (`book_id`) for internal joins and a natural key (`isbn`) preserved as a unique business identifier. This pattern — surrogate for machine use, natural key retained as `UNIQUE` — recurs constantly in real schemas.

---

# Step 2 (cont.) — Identify Attributes (Customer, Order, Order Line)

**Customer** 

— `customer_id` *(surrogate key)*, 
- `first_name`, `last_name`, `email` *(natural, `UNIQUE`, R3)*, `phone`

**Order** 

— `order_id` *(surrogate key)*, 
- `order_date`, `status` *(controlled vocabulary, R5)*, `owning customer` *(FK once modeled)*

---

# Step 2 (cont.) — Identify Attributes (Customer, Order, Order Line) (cont.)

**Order Line** ("what was bought, on which order")

- the order it belongs to, plus a line number *(together: a composite identifier)*
- the book purchased
- `quantity` *(must be > 0, R7)*
- **unit_price at the time of sale** *(R6 — deliberately duplicated from `books.price`!)*

This entity did not appear in our noun list — it emerged because "Order **contains** Book" is a relationship that itself carries facts (`quantity`, historical `unit_price`).

---

# Step 3 — Relationships, Cardinality, and Participation

| Relationship | Cardinality | Participation | Rule |
|---|---|---|---|
| Author **writes** Book | 1 : N | Author optional, Book mandatory | R2 |
| Publisher **publishes** Book | 1 : N | Publisher optional, Book mandatory | R2 |
| Customer **places** Order | 1 : N | Customer optional, Order mandatory | R4 |
| Order **contains** Book (via Order Line) | 1 : N from each side | Both mandatory | R6, R8 |

---

# Step 3 — Relationships, Cardinality, and Participation (cont.)

Notice there is **no many-to-many relationship in this model** — that's a deliberate simplification (R2 explicitly assumes one author and one publisher per book). Every relationship here is a plain one-to-many, which is exactly what makes this a good *first* case study.

**Crow's foot notation, quick reference** (the symbol at each end of a relationship line encodes cardinality *and* participation):

```
ONE, mandatory: ──┤├──("exactly one")   
ONE, optional:  ──○├──("zero or one")   
MANY, mandatory: ──┤<──("one or more")
MANY, optional:  ──○<──("zero or more")
```
Reading **`Customer ──┤├───○<── Order`**: *"each Order relates to exactly one Customer; each Customer relates to zero-or-more Orders."*

---

# The Full Conceptual ERD (Text Form)

```
Author 1───< Book >───1 Publisher
                │
                │ (Book appears on many Order Lines;
                │  an Order Line always names exactly one Book)
                ∨
Customer 1───< Order 1───< OrderItem >───1 Book
```

Reading this: 

---

# The Full Conceptual ERD (Text Form) (cont.)

* an `Author` can write many `Book`s, 
* but each `Book` has exactly one `Author`. 
* A `Publisher` can publish many `Book`s, 
* but each `Book` has exactly one `Publisher`. 
* A `Customer` can place many `Order`s, 
* but each `Order` belongs to exactly one `Customer`. 
* Each `Order` is linked to one or more `Book`s through `OrderItem`, and the same `Book` can appear on many different `OrderItem` rows across many orders.

Every arrow above traces directly back to R1–R8 — nothing here is arbitrary.

---

# Part 3: Normalization — Where It Fits

The ERD tells us *what* entities and relationships exist — but not whether our tables are free of redundancy. **Normalization** is the formal process that:

1. Starts from any table design — even the flat spreadsheet PageTurner was actually using.
2. Identifies **functional dependencies**: "attribute B's value is determined by attribute A's value."
3. Progressively decomposes tables so every non-key attribute depends on the **whole key, and nothing but the key**.

Let's reverse-engineer PageTurner's original spreadsheet export the way you would on a real project.

---

# The Flat Export PageTurner Was Actually Using

```sql
CREATE TABLE orders_flat (
    order_id INTEGER, 
    order_date DATE, 
    customer_name VARCHAR, 
    customer_email VARCHAR,
    isbn VARCHAR, 
    title VARCHAR, 
    author_name VARCHAR, 
    publisher_name VARCHAR,
    price DECIMAL(10,2), 
    quantity INTEGER
);
```

---

# The Flat Export PageTurner Was Actually Using (cont.)

| `order_id` | `order_date` | `customer_name` | `customer_email` | `isbn` | `title` | `author_name` | `publisher_name` | `price` | `qty` |
|---|---|---|---|---|---|---|---|---|---|
| 5001 | 2026-06-01 | Grace Lee | grace.lee@example.com | ISBN-001 | Norwegian Wood | Haruki Murakami | Knopf | 15.99 | 1 |
| 5001 | 2026-06-01 | Grace Lee | grace.lee@example.com | ISBN-002 | The Martian | Andy Weir | Crown Publishing | 12.99 | 1 |
| 5002 | 2026-06-02 | Marcus Reed | marcus.reed@example.com | ISBN-003 | Where the Crawdads Sing | Delia Owens | Putnam | 14.50 | 2 |
| 5003 | 2026-06-05 | Grace Lee | grace.lee@example.com | ISBN-004 | Atomic Habits | James Clear | Crown Publishing | 18.00 | 1 |

This is genuinely how most projects start: a report export, not a design.

---

# Naming the Anomalies

Querying this table live in DuckDB exposes the classic problems:

**Update anomaly** — Grace Lee's email is stored on two separate rows. Fixing a typo means finding and updating *every* row she appears on:

```sql
SELECT order_id, 
       customer_name, 
       customer_email 
FROM orders_flat 
WHERE customer_name = 'Grace Lee';
```

---

# Naming the Anomalies (cont.)

```
 order_id | customer_name | customer_email
   5001   | Grace Lee     | grace.lee@example.com
   5003   | Grace Lee     | grace.lee@example.com    <- both must change together
```

**Insertion anomaly** — we cannot add a new book to the catalog until someone actually orders it; there's no standalone place to record catalog facts.

**Deletion anomaly** — deleting Marcus Reed's only order would silently erase all record that Marcus Reed is a customer.

---

# Identifying the Functional Dependencies (FDs)

```
order_id          →  order_date, customer_name, customer_email
isbn              →  title, author_name, publisher_name, price
(order_id, isbn)  →  quantity     [the only fact truly about the pairing]
```

The **candidate key** of `orders_flat` is `(order_id, isbn)` — the minimal combination that determines each row's `quantity`. But `order_date` and the `customer_*` columns depend on only *part* of that key (`order_id` alone), and `title`, `author_name`, `publisher_name`, `price` depend on only the other part (`isbn` alone). That's a **2NF violation** — the same pattern you'll see again, at larger scale, in the e-commerce case study.

---

# 1NF — Atomicity

**First Normal Form (1NF):** every column holds a single, 
atomic value — no repeating groups, no comma-packed lists.

Our `orders_flat` table is already in 1NF (one book per row). 
The anti-pattern to avoid would be a single row per *order* 
with a packed list of books:

```
 order_id | customer_name | book_list
   5001   | Grace Lee     | ISBN-001:1, ISBN-002:1
```

You cannot write `WHERE isbn = 'ISBN-002'` against a 
column like that without ugly string parsing. 
**1NF is why `order_items` has one row per book per order, 
never one row per order.**

---

# 2NF — Eliminate Partial Dependencies

**Second Normal Form (2NF):** the table is in 1NF, 
*and* every non-key attribute depends on the 
**entire** primary key, not just part of a composite key.

```sql
CREATE TABLE n2_orders (
   order_id PK, 
   order_date, 
   customer_name, 
   customer_email);
   
CREATE TABLE n2_books (
   isbn PK, title, 
   author_name, 
   publisher_name, price);
   
CREATE TABLE n2_order_items (
   order_id FK, 
   isbn FK, 
   quantity, 
   PRIMARY KEY(order_id, isbn));
```

---

# 2NF — Eliminate Partial Dependencies (cont.)

Verified in DuckDB — `n2_order_items` now holds 
only the fact that truly depends on the *whole* 
composite key:

```
 order_id | isbn     | quantity
   5001   | ISBN-001 | 1
   5001   | ISBN-002 | 1
   5002   | ISBN-003 | 2
```

---

# 3NF — Eliminate Transitive Dependencies

**Third Normal Form (3NF):** the table is in 2NF, *and* 
no non-key attribute depends on another non-key attribute 
(a **transitive dependency**).

In `n2_orders`, `customer_email` doesn't really depend 
on `order_id` — it depends on *which customer* placed 
the order. Same story for `author_name` and `publisher_name` 
in `n2_books`: they depend on the book's author/publisher 
identity, not directly on `isbn`. Fix: extract `customers`, 
`authors`, and `publishers`, minting **surrogate keys** since 
names are not safe real-world identifiers (they can collide).

---

# 3NF — Eliminate Transitive Dependencies (cont.)

```sql
CREATE TABLE n3_customers  (
   customer_id PK, 
   customer_name, 
   customer_email UNIQUE);
   
CREATE TABLE n3_authors    (
   author_id PK, 
   author_name UNIQUE);
   
CREATE TABLE n3_publishers (
   publisher_id PK, 
   publisher_name UNIQUE);
   
CREATE TABLE n3_books      (
   book_id PK, 
   isbn UNIQUE, 
   title, 
   author_id FK, 
   publisher_id FK, price);
   
CREATE TABLE n3_orders     (
   order_id PK, 
   order_date, 
   customer_id FK);
   
CREATE TABLE n3_order_items(
   order_id FK, 
   book_id FK, 
   quantity, 
   PRIMARY KEY(order_id, book_id)
);
```

---

# 3NF Result — Verified in DuckDB

```
n3_customers                                n3_authors
 customer_id | customer_name | ...           author_id | author_name
      1      | Grace Lee     | ...                1     | Andy Weir
      2      | Marcus Reed   | ...                2     | Delia Owens
                                                   3     | Haruki Murakami
n3_publishers                                     4     | James Clear
 publisher_id | publisher_name
      1       | Crown Publishing            n3_books
      2       | Knopf                        book_id | isbn     | ... | author_id | publisher_id | price
      3       | Putnam                          1    | ISBN-001 | ... |     3     |      2       | 15.99
                                                  2    | ISBN-002 | ... |     1     |      1       | 12.99
n3_orders                                        3    | ISBN-003 | ... |     2     |      3       | 14.50
 order_id | order_date | customer_id             4    | ISBN-004 | ... |     4     |      1       | 18.00
   5001   | 2026-06-01 |      1
   5002   | 2026-06-02 |      2
   5003   | 2026-06-05 |      1
```

**No data was lost.** A 5-way join of these tables 
reconstructs `orders_flat` exactly, row for row — 
verified live in DuckDB. That reconstruction test 
is the acceptance criterion for any decomposition.

---

# When to Break the Rules: Controlled Denormalization

Recall **R6**: *"the price at the moment of sale must be 
preserved even if the book's catalog price later changes."*

Look at `order_items.unit_price` in the final design — it 
duplicates a value that also lives in `books.price`. Isn't 
that exactly the redundancy 3NF tells us to remove?

This is **intentional, documented denormalization** — the 
two columns represent *different facts* that usually coincide:

---

# When to Break the Rules: Controlled Denormalization (cont.)

- `books.price` = "what we charge **today**."
- `order_items.unit_price` = "what we charged **at the moment of this specific sale**" 
- — a historical fact that must never silently change.

**Rule of thumb:** normalize by default; denormalize only 
when you can name the specific business reason (here: an 
audit/historical-accuracy requirement) — and document it 
in the schema itself.

---

# Part 4: The Logical Schema — Finalized Table List (6 Tables)

| Table | Purpose | Primary Key |
|---|---|---|
| `authors` | people who write books | `author_id` |
| `publishers` | companies that publish books | `publisher_id` |
| `books` | catalog items | `book_id` |
| `customers` | registered shoppers | `customer_id` |
| `orders` | purchase transactions | `order_id` |
| `order_items` | line items within an order | `(order_id, line_number)` |

Compare this to the ERD from Part 2 — every table here corresponds to one box (or one relationship-with-attributes) on that diagram. Six tables, zero many-to-many junctions, by deliberate design (R2).

---

# Keys and Referential Integrity, Formally

- **Candidate key** — any minimal set of attributes that uniquely identifies a row. `books` has two: `book_id` and `isbn`.
- **Primary key (PK)** — the candidate key we chose as the identifier: the surrogate (`book_id`), not the natural key.
- **Alternate key** — a candidate key not chosen as PK, still protected by `UNIQUE` (`isbn`, `customers.email`, `publishers.publisher_name`).
- **Foreign key (FK)** — implements a relationship by requiring a value to match a candidate key elsewhere (or be absent, if optional).

---

# Keys and Referential Integrity, Formally (cont.)

| Child table | Foreign key | Parent table |
|---|---|---|
| books | author_id | authors |
| books | publisher_id | publishers |
| orders | customer_id | customers |
| order_items | order_id | orders |
| order_items | book_id | books |

---

# Three Kinds of Integrity We Must Enforce

1. **Entity integrity** — every table has a primary key; PK values are never `NULL`, never duplicated. (`PRIMARY KEY`.)

2. **Referential integrity** — a foreign key value must match an existing primary key elsewhere, or be absent if the relationship is optional. No order line may point to a book or order that doesn't exist (R8). (`FOREIGN KEY … REFERENCES`.)

3. **Domain / business-rule integrity** — a value must be within its legal domain: `price` and `unit_price` must be ≥ 0 (R7), `quantity` must be > 0 (R7), `status` must be one of four known lifecycle states (R5). (`CHECK` constraints and `ENUM` types.)

The physical model, next, is where we prove the database actually enforces all three — live.

---

# Part 5: The Physical Model in DuckDB — Type Mapping

| Logical domain | DuckDB physical type | Why |
|---|---|---|
| Surrogate ID | `INTEGER` | compact, simple; literal values used here since our sample data is small and curated |
| Money | `DECIMAL(10,2)` | exact decimal arithmetic — never `FLOAT` for currency |
| Free text | `VARCHAR` | unbounded, UTF-8 — no artificial length limits needed |
| Calendar date | `DATE` | `order_date` |
| Fixed vocabulary | `ENUM` | `order_status` — see next slide |
| Quantity / price bounds | `INTEGER` / `DECIMAL` + `CHECK` | the type alone can't stop `quantity = -3`; a constraint can |

This exercise — logical domain → concrete engine type — is the same one you'd repeat for PostgreSQL, MySQL, or any other target engine. Only the specific type names would change.

---

# DuckDB Feature Spotlight: `ENUM` for a Controlled Vocabulary

Rather than a free-text `status VARCHAR` plus an application-level whitelist, we encode R5's fixed lifecycle directly in the schema:

```sql
CREATE TYPE order_status AS ENUM ('PENDING','SHIPPED','DELIVERED','CANCELLED');
```

Benefits over `VARCHAR` + `CHECK IN (...)`: values are stored compactly as integers internally, typos are rejected at `INSERT` time (`'Shiped'` simply fails), and the legal value set is self-documenting. This is the physical-layer expression of the domain-integrity rule from Part 4.

---

# Physical DDL — `authors`, `publishers`, `books`

```sql
CREATE TABLE authors (
    author_id  INTEGER PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name  VARCHAR NOT NULL
);

CREATE TABLE publishers (
    publisher_id   INTEGER PRIMARY KEY,
    publisher_name VARCHAR NOT NULL UNIQUE,
    city           VARCHAR
);

CREATE TABLE books (
    book_id           INTEGER PRIMARY KEY,
    isbn              VARCHAR NOT NULL UNIQUE,          -- R1: natural/alternate key
    title             VARCHAR NOT NULL,
    author_id         INTEGER NOT NULL REFERENCES authors(author_id),      -- R2
    publisher_id      INTEGER NOT NULL REFERENCES publishers(publisher_id),-- R2
    price             DECIMAL(10,2) NOT NULL CHECK (price >= 0),           -- R1, R7
    publication_year  INTEGER,
    genre             VARCHAR
);
```

---

# Physical DDL — `authors`, `publishers`, `books` (cont.)

Executed against DuckDB 1.5 with zero errors.

---

# Physical DDL — `customers`, `orders`, `order_items`

```sql
CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    first_name   VARCHAR NOT NULL,
    last_name    VARCHAR NOT NULL,
    email        VARCHAR NOT NULL UNIQUE,     -- R3
    phone        VARCHAR
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),  -- R4
    order_date   DATE NOT NULL,
    status       order_status NOT NULL DEFAULT 'PENDING'              -- R5
);

CREATE TABLE order_items (
    order_id     INTEGER NOT NULL REFERENCES orders(order_id),   -- R8
    line_number  INTEGER NOT NULL,
    book_id      INTEGER NOT NULL REFERENCES books(book_id),     -- R8
    quantity     INTEGER NOT NULL CHECK (quantity > 0),          -- R7
    unit_price   DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0), -- R6, R7
    PRIMARY KEY (order_id, line_number)
);
```

---

# Verifying the Schema and Its Constraints

```sql
SHOW TABLES;
```
```
 authors  books  customers  order_items  orders  publishers
```

All 6 tables, executed and confirmed live — every `CREATE TYPE` and `CREATE TABLE` ran without error, in dependency order (parents before children).

We then tested the constraints directly, not just trusted the DDL:

```sql
INSERT INTO order_items (order_id, line_number, book_id, quantity, unit_price)
VALUES (9999, 1, 1, 1, 10.00);
-- ConstraintException: Violates foreign key constraint ("order_id: 9999" does not exist)

INSERT INTO books (book_id, isbn, title, author_id, publisher_id, price)
VALUES (99, 'ISBN-999', 'Bad Book', 1, 1, -5.00);
-- ConstraintException: CHECK constraint failed on table books: CHECK((price >= 0))
```

Both failures are exactly what we want: the database itself rejects bad data.

---

# Part 6: Sample Data & Business Questions — Populating the Model

We inserted representative rows into all six tables: 4 authors, 3 publishers, 5 books, 4 customers (one, **Tom Becker**, has registered but placed no orders yet — testing optional participation, R4), 4 orders across the status lifecycle, and 6 order lines.

```
authors 4   publishers 3   books 5
customers 4   orders 4   order_items 6
```

Every row satisfied every constraint on the first attempt — good evidence the schema faithfully reflects R1–R8.

---

# Query 1 & 3 — Customer Order History and Order Totals

```sql
SELECT c.first_name || ' ' || c.last_name AS customer, o.order_id, o.order_date, o.status
FROM customers c JOIN orders o ON o.customer_id = c.customer_id ORDER BY c.customer_id, o.order_date;
```
```
   customer  | order_id | order_date | status
  Grace Lee  |   5001   | 2026-06-01 | DELIVERED     Tom Becker doesn't appear: an inner join
  Grace Lee  |   5003   | 2026-06-05 | DELIVERED     excludes him since he has no matching order
 Marcus Reed |   5002   | 2026-06-02 | SHIPPED        (optional participation, from our ERD).
  Priya Shah |   5004   | 2026-06-08 | PENDING
```

```sql
SELECT o.order_id, c.first_name||' '||c.last_name AS customer,
       SUM(oi.quantity*oi.unit_price)::DECIMAL(10,2) AS order_total
FROM orders o JOIN customers c ON c.customer_id=o.customer_id
JOIN order_items oi ON oi.order_id=o.order_id GROUP BY o.order_id, customer ORDER BY o.order_id;
```
```
 order_id |  customer   | order_total     Derived, never stored: no stored total
   5001   |  Grace Lee  |   28.98         can ever fall out of sync with its line
   5002   | Marcus Reed |   29.00         items (a direct benefit of normalization).
   5003   |  Grace Lee  |   18.00
   5004   | Priya Shah  |   28.98
```

---

# Query 2 — Order Line Detail

```sql
SELECT o.order_id, b.title, oi.quantity, oi.unit_price,
       (oi.quantity*oi.unit_price)::DECIMAL(10,2) AS line_total
FROM order_items oi JOIN orders o ON o.order_id=oi.order_id JOIN books b ON b.book_id=oi.book_id
ORDER BY o.order_id, oi.line_number;
```
```
 order_id | title                    | quantity | unit_price | line_total
   5001   | Norwegian Wood           |    1     |   15.99    |   15.99
   5001   | The Martian              |    1     |   12.99    |   12.99
   5002   | Where the Crawdads Sing  |    2     |   14.50    |   29.00
   5003   | Atomic Habits            |    1     |   18.00    |   18.00
   5004   | Kafka on the Shore       |    1     |   16.99    |   16.99
   5004   | The Martian              |    1     |   11.99    |   11.99
```

Order 5004's copy of *The Martian* sold at **11.99**, below the current catalog price of **12.99** — exactly the historical-price scenario R6 protects.

---

# Query 4 & 5 — Revenue by Author, Catalog by Publisher

```sql
SELECT a.first_name || ' ' || a.last_name AS author,
       SUM(oi.quantity*oi.unit_price)::DECIMAL(10,2) AS revenue
FROM order_items oi JOIN books b ON b.book_id=oi.book_id JOIN authors a ON a.author_id=b.author_id
GROUP BY author ORDER BY revenue DESC;
```
```
      author       | revenue          publisher_name    | num_books | avg_price
 Haruki Murakami    |  32.98           Knopf              |     2     |  16.49
 Delia Owens         |  29.00          Crown Publishing   |     2     |  15.50
 Andy Weir           |  24.98          Putnam             |     1     |  14.50
 James Clear         |  18.00
```

Both queries are only possible because `authors` and `publishers` are separate, normalized tables rather than repeated text baked into every `books` row (exactly the redundancy 3NF eliminated in Part 3).

---

# Query 6 — Customers With No Orders Yet (Anti-Join)

```sql
SELECT c.first_name || ' ' || c.last_name AS customer
FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;
```
```
 customer
 Tom Becker
```

This confirms, with a live query, the optional-participation rule designed back in Part 2: the schema *allows* a customer to exist with zero orders, and here we find one. If this query ever returned a customer you *expected* to have ordered, that would be a data-quality signal — not a schema bug.

---

# Part 7: Summary — The Journey, Recapped

```
Business Requirements (R1–R8, plain English)
        │  noun/verb extraction
        ▼
Conceptual Model  (6 entities, plain 1:N relationships, ERD)
        │  normalize (1NF → 2NF → 3NF)
        ▼
Logical Model  (6 tables, keys, FK map, 3 kinds of integrity)
        │  choose engine-specific types, ENUM
        ▼
Physical Model  (DuckDB DDL — executed, verified, constraint-tested)
        │  load data, query
        ▼
Answers to real business questions, with data quality guaranteed by the schema
```

Every step was demonstrated live against a running DuckDB database — not just described. The next case study (a 15-table e-commerce platform) follows this exact same pipeline, adding many-to-many relationships, self-referencing hierarchies, and a richer set of constraints.

---

# Key Takeaways

- **Requirements drive design** — every table and constraint traces back to R1–R8.
- **Normalization eliminates real redundancy and anomalies** — we watched Grace Lee's duplicated email, and the insertion/deletion anomalies, disappear after decomposition.
- **A relationship with its own attributes becomes its own table** — that single rule produced `order_items` from "Order contains Book."
- **Denormalization is a deliberate, documented exception** (order-line price), never a default.
- **The database itself enforces integrity** — our live constraint tests caught bad data that application code might have missed.
- **Keeping every relationship 1:N (no M:N) was a deliberate simplification** for this case study — real catalogs usually need many-to-many, which is exactly where the next case study picks up.

---

# Exercises for Further Practice

1. **Relax R2:** suppose PageTurner now wants to support books with **multiple co-authors**. What changes about the schema? (Hint: this is the many-to-many pattern from the second case study.)
2. **Add reviews:** customers want to rate books 1–5 stars with optional text. Design the new entity, its keys, and its constraints.
3. **Normalize this:** given a flat table `(student_id, student_name, course_name, instructor_name, grade)`, find the functional dependencies and decompose to 3NF.
4. **Query practice:** write a query that finds every book that has never been ordered.
5. **Constraint design:** write a `CHECK` (or small redesign) that prevents an order's `status` from being `'DELIVERED'` if it has zero order lines.

---

<!-- _class: lead -->

# Questions?
