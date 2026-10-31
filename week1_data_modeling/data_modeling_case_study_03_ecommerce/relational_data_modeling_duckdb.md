---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 25px; }
  section.lead h1 { font-size: 2.2em; }
  table { font-size: 0.72em; }
  pre, code { font-size: 0.72em; }
  h1 { color: #1a3e6f; }
  h2 { color: #1a3e6f; }
---

<!-- _class: lead -->

# Relational Data Modeling
## A Step-by-Step Journey from Business Requirements to a Physical Database in DuckDB

MSIS-2407 — Week 1, Data Modeling (Case Study 3 of 3)

---

# Learning Objectives

By the end of this module you will be able to:

1. Translate ambiguous business requirements into precise **entities, attributes, and relationships**.
2. Build a **conceptual model** (ER diagram) and justify every design decision against a business rule.
3. Apply **normalization theory** (1NF → 2NF → 3NF → BCNF) to eliminate redundancy and anomalies, and know when to deliberately denormalize.
4. Produce a complete **logical schema** with keys and integrity constraints.
5. Implement that schema as a **physical model in DuckDB**, using real DDL, constraints, sequences, and enumerations.
6. Query the resulting model to answer real business questions, and understand how DuckDB enforces the rules you designed.

---

# Agenda

1. Why data modeling — and why three models, not one
2. The business story: **NorthGate Marketplace** (an e-commerce platform)
3. Conceptual modeling — entities, attributes, relationships, ERD
4. Normalization — from a flat spreadsheet to a clean relational design
5. The logical schema — keys and integrity, finalized
6. The physical model in DuckDB — DDL, types, constraints, verification
7. Loading data and answering business questions with SQL
8. Design considerations, pitfalls, and best practices
9. Summary and exercises

---

# Why Data Modeling? Three Models, One Truth

Data modeling is the disciplined process of translating **how the business talks about its world** into **how a database stores and enforces that world**. We move through three levels of abstraction, each answering a different question:

| Level | Question it answers | Audience | Artifact |
|---|---|---|---|
| **Conceptual** | *What* things matter to the business and how do they relate? | Business + analysts | Entity-Relationship Diagram |
| **Logical** | *How* do we structure that, independent of any product? | Data architects | Normalized relational schema (tables, keys, FDs) |
| **Physical** | *Where and how exactly* is it stored and enforced? | DBAs / engineers | DDL in a specific engine (here: DuckDB) |

A good model is **traceable**: every table, column, and constraint in the physical model should trace back to a sentence in the business requirements.

---

# Why This Matters: The Cost of Skipping Steps

Teams that jump straight from a requirements doc to `CREATE TABLE` statements typically ship a database with:

- **Redundant data** that drifts out of sync (a customer's email stored in five tables, updated in only one).
- **Update, insert, and delete anomalies** — the classic symptoms of an unnormalized design.
- **Missing or wrong constraints**, so bad data (negative prices, orphaned orders) enters silently and is discovered in production.
- **No shared vocabulary** between business stakeholders and engineers, so requirements get re-litigated during implementation.

The conceptual → logical → physical pipeline is how we catch these problems on a whiteboard instead of in an incident report.

---

# Why DuckDB for This Exercise?

DuckDB is an **in-process, columnar, OLAP-oriented relational database** — think "SQLite for analytics." We use it here because:

- It is a **fully standards-compliant relational engine**: `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `CHECK`, `ENUM` types, sequences — everything we need to enforce a relational design faithfully.
- It requires **zero server setup** — a single file (or in-memory database) is enough to run every example in this deck and verify it live.
- It has excellent SQL ergonomics (window functions, `SELECT * EXCLUDE`, native `ENUM`, friendly error messages) that make constraint violations easy to *demonstrate*, not just describe.
- The relational modeling principles you learn here transfer directly to PostgreSQL, MySQL, SQL Server, Snowflake, or any other relational engine.

Every SQL statement in this deck was **actually executed against DuckDB 1.5** and the output shown is real, not illustrative.

---

<!-- _class: lead -->

# Part 1
## The Business Story: NorthGate Marketplace

---

# Meet the Business: NorthGate Marketplace

NorthGate Marketplace is a mid-sized online retailer selling electronics, fitness gear, and home goods directly to consumers. The founders have been running the business on spreadsheets and a shared CSV export from their storefront tool. As the company grows, they've hired a data team (you) to design a proper relational database.

**Stakeholders you interviewed:**

- **Customers** — browse products, place orders, track shipments, leave reviews.
- **Catalog & Merchandising team** — manage products, categories, and supplier relationships.
- **Warehouse Operations** — track inventory across multiple warehouses.
- **Finance** — reconcile payments against orders.
- **Marketing** — run coupon campaigns and needs revenue-by-category reporting.

Your job: turn their interviews into a relational database.

---

# Functional Requirement Set 1 — Customers & Identity

> **R1.** The business must uniquely identify every customer by an internal ID; email address must also be unique since it's used to log in.
>
> **R2.** A customer can have multiple addresses (home, work, gift addresses) and each address is tagged as **billing** or **shipping**. A customer must be able to mark one address as their default.
>
> **R3.** We must be able to record a customer in the system *before* they ever place an order (e.g., they signed up for the newsletter). An order, however, must always belong to exactly one customer.

**Modeling signal:** 

* `R1 → uniqueness constraint`. 
* `R2 → one-to-many relationship` <br>
  (Customer → Addresses) with a categorical attribute. 
* `R3 → the Customer/Order relationship is` <br>
**optional on the "many" side going one way, mandatory going the other** 
* a customer may have zero orders, but every order requires a customer.

---

# Functional Requirement Set 2 — Product Catalog

> **R4.** Every product has a unique SKU (a business/natural key used in the warehouse) as well as a name, description, and current price. Prices must never be negative.
>
> **R5.** Products are organized into categories (Electronics, Fitness, Home & Kitchen…). Categories can be nested — "Accessories" is a sub-category of "Electronics."
>
> **R6.** A product can be sourced from multiple suppliers, each supplier potentially offering a different supply (wholesale) cost for the same product. A supplier, in turn, supplies many products.
>
> **R7.** Products can be discontinued (`is_active = false`) without deleting their historical sales data.

**Modeling signal:** 

* R5 is a **self-referencing (recursive) relationship**. 
* R6 is a classic **many-to-many** relationship requiring a junction/associative entity.

---

# Functional Requirement Set 3 — Inventory & Warehouses

> **R8.** The company operates multiple warehouses. Each warehouse holds a quantity of each product it stocks; a product may be stocked in zero, one, or several warehouses.
>
> **R9.** Stock quantity can never go negative — this is a hard business rule, not just a UI validation.

**Modeling signal:** 

* R8 describes another **many-to-many relationship** (Product ↔ Warehouse) that carries an attribute of its own (`quantity_on_hand`) — this attribute belongs to the *relationship*, not to either entity alone, so it needs its own associative table (`inventory`).

---

# Functional Requirement Set 4 — Orders & Fulfillment

> **R10.** An order is placed by one customer, has one shipping address and one billing address (which may or may not be the same physical address), and moves through a lifecycle: `PENDING → PAID → SHIPPED → DELIVERED`, with possible `CANCELLED` / `REFUNDED` side-exits.
>
> **R11.** An order contains one or more line items. Each line item references a product, a quantity, and — critically — **the price at the time of purchase**, which must be preserved even if the catalog price later changes.
>
> **R12.** An order may have zero or more shipments (a large order might ship in multiple boxes on different days) and zero or more payments (partial payments, refund reversals).
>
> **R13.** Coupons can be applied to orders. A coupon has a discount percentage and a validity window; one order may use multiple coupons, and a coupon may be used on multiple orders.

---

# Functional Requirement Set 4 — Orders & Fulfillment (cont.)

**Modeling signal:** 

* R11 is the single most important lesson in this deck — see the normalization section for why line-item price must be **duplicated on purpose**.

---

# Functional Requirement Set 5 — Reviews & Feedback

> **R14.** A customer can leave at most one review per product per purchase occasion, with a star rating from 1–5 and optional free text. Ratings outside 1–5 are invalid data and must be rejected by the database, not just the UI.
>
> **R15.** Reviews must reference a real customer and a real product — we never want a review "floating" without an owner or a subject.

**Modeling signal:** 

* R14 → a `CHECK` constraint. 
* R15 → mandatory foreign keys (`NOT NULL REFERENCES …`), i.e., **referential integrity** enforced at the database layer, not the application layer.

---

# Consolidated Business Rules Checklist

We will hold ourselves accountable to every one of these as we model:

| # | Rule (paraphrased) | Modeling concept it drives |
|---|---|---|
| R1 | Customer ID + email unique | Primary key, alternate/unique key |
| R2 | Customer 1—N Addresses, typed | One-to-many, categorical attribute |
| R3 | Order requires customer, customer doesn't require orders | Mandatory vs. optional participation |
| R4 | SKU unique, price ≥ 0 | Natural key, `CHECK` constraint |
| R5 | Categories nest | Recursive (self-referencing) relationship |
| R6 | Product ↔ Supplier, many-to-many | Associative entity |
| R8 | Product ↔ Warehouse with quantity | Associative entity with its own attribute |
| R11 | Line-item price fixed at sale time | Controlled denormalization |
| R13 | Order ↔ Coupon, many-to-many | Associative entity |
| R14 | Rating 1–5 | `CHECK` constraint |

We now translate this into a conceptual model.

---

<!-- _class: lead -->

# Part 2
## Conceptual Data Modeling

---

# What Is Conceptual Modeling?

* Conceptual modeling captures **what matters to the business**, using vocabulary the business itself would recognize - before we worry about data types, keys, or any specific database engine.

Three building blocks:

- **Entity** — a distinguishable *thing* the business tracks (`Customer`, `Product`, `Order`). Becomes a table.
- **Attribute** — a property of an entity (`Customer.email`, `Product.unit_price`). Becomes a column.
- **Relationship** — an association between entities, described by **cardinality** (1:1, 1:N, M:N) and **participation** (mandatory/optional).

The technique for finding entities is simple but powerful: **read the requirements and underline every noun**. Nouns that are described (have attributes) and are referenced repeatedly are usually entities. Verbs connecting two nouns are usually relationships.

> A noun is a part of speech that names a person, place, thing, or abstract idea. Nouns act as the building blocks of sentences and frequently serve as subjects or objects.

---

# Step 1 — Identify Entities (Noun Extraction)

Applying noun-extraction to our 15 requirements yields:

---

# Step 1 — Identify Entities (Noun Extraction) (cont.)

| Entity | Business meaning | Source rule(s) |
|---|---|---|
| Customer | A registered shopper | R1–R3 |
| Address | A postal address owned by a customer | R2 |
| Category | A grouping of products, possibly nested | R5 |
| Product | An item for sale | R4–R7 |
| Supplier | A vendor who supplies products | R6 |
| Warehouse | A physical stocking location | R8 |
| Order | A customer's purchase transaction | R10–R13 |
| Coupon | A discount code | R13 |
| Payment | Money received against an order | R12 |
| Shipment | A physical delivery of an order | R12 |
| Review | Customer feedback on a product | R14–R15 |

Two relationships turned out to need entities of their own (associative entities) — we'll surface those next.

---

# Step 2 — Identify Attributes (Customer, Address)

For each entity, list attributes and mark candidate identifiers.

**Customer**

- `customer_id` *(candidate key — surrogate, business has no natural identifier)*
- `first_name`, `last_name`
- `email` *(candidate key — natural, must be unique per R1)*
- `phone`
- `created_at`

---

# Step 2 — Identify Attributes (Customer, Address) (cont.)

**Address**

- `address_id` *(surrogate key)*
- `street`, `city`, `state/region`, `postal_code`, `country`
- `addr_type` *(BILLING / SHIPPING — a controlled vocabulary, R2)*
- `is_default` *(boolean flag, R2)*
- `owning customer` *(this becomes a foreign key once we model the relationship)*

Note we already have **two kinds of keys** in play: a **surrogate key** (`customer_id`, meaningless but stable) and a **natural key candidate** (`email`, meaningful to the business but shouldn't be the primary key because business identifiers can change).

---

# Step 2 (cont.) — Identify Attributes (Category, Product)

**Category**

- `category_id` *(surrogate key)*
- `category_name` *(natural, unique per R5)*
- `parent_category` *(self-referencing — recursive relationship, R5)*

**Product**

---

# Step 2 (cont.) — Identify Attributes (Category, Product) (cont.)

- `product_id` *(surrogate key)*
- `sku` *(natural key, unique per R4 — this is what the warehouse actually uses)*
- `product_name`
- `unit_price` *(must be ≥ 0, R4)*
- `description`
- `is_active` *(R7)*
- `owning category` *(foreign key once relationship is modeled)*

**Design decision:** 

* We keep **both** `product_id` (surrogate, used internally for joins) and `sku` (natural, used by the business and external systems, marked `UNIQUE`). 
* This is a very common real-world pattern — surrogate keys for machine efficiency, natural keys preserved as unique business identifiers.

---

# Step 2 (cont.) — Identify Attributes (Order, Order Line)

**Order**

- `order_id` *(surrogate key)*
- `order_date`
- `status` *(controlled vocabulary: PENDING/PAID/SHIPPED/DELIVERED/CANCELLED/REFUNDED, R10)*
- owning customer, shipping address, billing address *(three foreign keys once relationships are modeled)*

**Order Line ("what was purchased in this order")**

---

# Step 2 (cont.) — Identify Attributes (Order, Order Line) (cont.)

- `order it belongs to` + `a line number` *(together they form a composite identifier)*
- `the product purchased`
- `quantity`
- **`unit_price` at the time of sale** *(R11 — deliberately duplicated from `Product.unit_price`!)*

* This entity didn't appear in our noun list directly — it emerges because the relationship "Order **contains** Product" itself carries data (`quantity`, historical `unit_price`). 
* Whenever a **relationship has its own attributes**, it must become its own entity.

---

# Step 3 — Identify Relationships & Cardinality

| Relationship | Cardinality | Participation | Rule |
|---|---|---|---|
| Customer **has** Address | 1 : N | Customer optional, Address mandatory | R2 |
| Customer **places** Order | 1 : N | Customer optional, Order mandatory | R3 |
| Category **contains** Category (self) | 1 : N | Both optional (root has no parent) | R5 |
| Category **classifies** Product | 1 : N | Category optional, Product mandatory | R5 |
| Product ↔ Supplier **supplies** | M : N | Both optional | R6 |
| Product ↔ Warehouse **stocks** | M : N | Both optional | R8 |
| Order **contains** Product (via Order Line) | M : N | Both mandatory | R11 |
| Order ↔ Coupon **applies** | M : N | Both optional | R13 |
| Order **has** Payment | 1 : N | Order optional*, Payment mandatory | R12 |
| Order **has** Shipment | 1 : N | Order optional*, Payment mandatory | R12 |
| Product **receives** Review | 1 : N | Product optional, Review mandatory | R14 |
| Customer **writes** Review | 1 : N | Customer optional, Review mandatory | R14–15 |

---

# Step 3 — Identify Relationships & Cardinality (cont.)

*"Order optional" here means an order can exist with zero payments/shipments so far (e.g., still `PENDING`).

---

# Cardinality & Participation Notation (Crow's Foot)

We use **crow's foot notation** to draw relationships. The symbol at each end of a line encodes both cardinality and participation:

```
  ONE, mandatory:      ──┤├──        ("exactly one")
  ONE, optional:        ──○├──        ("zero or one")
  MANY, mandatory:      ──┤<──        ("one or more")
  MANY, optional:       ──○<──        ("zero or more")
```

Reading a relationship line: 

`Customer ──┤├───○<── Order`

reads as *"each Order relates to exactly one Customer; each Customer relates to zero-or-more Orders."*

This is the notation used in the ERD on the following slides. (Other common notations — Chen's original diagrams with diamonds for relationships, or UML class diagrams — express the same facts; crow's foot is the industry default for relational schemas.)

---

# Handling Many-to-Many: Associative Entities

A relational model **cannot directly express M:N relationships** — a table row can only point to one parent per foreign key. 

Whenever we found an `M:N` relationship (`Product ↔ Supplier`, `Product ↔ Warehouse`, `Order ↔ Coupon`, and `Order ↔ Product` itself), we resolve it with an **associative entity** (a.k.a. junction/bridge table):

```
Product (1) ──< product_suppliers >── (1) Supplier
                     │
           supply_price  (attribute of the RELATIONSHIP)
```

---

# Handling Many-to-Many: Associative Entities (cont.)

The associative entity's primary key is typically 
the **composite of both foreign keys** (`product_id, supplier_id`), and it's the natural home for any attribute that describes the *pairing* rather than 
either party alone (`supply_price`, `quantity_on_hand`, `unit_price` at time of sale).

This single idea — "relationships with attributes, 
or `M:N` relationships, become tables" — is the 
bridge between conceptual and logical modeling.

---

# Self-Referencing Relationships: Category Hierarchy

Categories nest ("Accessories" is under "Electronics"). We model this with a **foreign key from Category back to Category**:

```
categories
┌─────────────┬───────────────┬─────────────────────┐
│ category_id │ category_name │ parent_category_id  │
├─────────────┼───────────────┼─────────────────────┤
│      1      │ Electronics   │        NULL         │
│      2      │ Accessories   │         1           │
│      3      │ Fitness       │        NULL         │
└─────────────┴───────────────┴─────────────────────┘
```

`NULL` in `parent_category_id` means "top-level category" — a perfectly valid use of `NULL` to represent "not applicable," distinct from the anomaly cases we'll see next.

---

# The Full Conceptual ERD (Text Form)

```
Customer 1───< Address                Category 1───< Category (self, parent/child)
   │                                          │
   1                                          1
   │                                          │
   ∨                                          ∨
 Order >───1 (ship addr)          Product >───1 Category
 Order >───1 (bill addr)             │  │
   │                                 │  └──< Review >───1 Customer
   1                                 │
   │                          Product ──M:N── Supplier   (via product_suppliers)
  ┌┴──────────┬───────────┐   Product ──M:N── Warehouse  (via inventory)
  ∨           ∨           ∨
Payment    Shipment   OrderItem >───1 Product
                            
 Order ──M:N── Coupon        (via order_coupons)
```

Every arrow above corresponds to a row in the cardinality table two slides back — nothing here is arbitrary; it is a direct translation of R1–R15.

---

<!-- _class: lead -->

# Part 3
## Normalization: From a Flat Spreadsheet to a Clean Design

---

# Where Normalization Fits

The ERD tells us *what* entities and relationships exist — but it doesn't, by itself, guarantee our tables are free of redundancy. **Normalization** is the formal process (built on *functional dependency* theory) that:

1. Starts from any table design (even a bad one — like a single denormalized spreadsheet export).
2. Identifies **functional dependencies**: "attribute B's value is determined by attribute A's value."
3. Progressively decomposes tables so that **every non-key attribute depends on the whole key, and nothing but the key** — the informal mantra for 3NF.

We'll demonstrate this the way it happens in practice: an analyst hands you a flat CSV, and you must reverse-engineer the entities hiding inside it.

---

# The Flat Export NorthGate Actually Handed Us

```sql
CREATE TABLE orders_flat (
    order_id INTEGER, 
    order_date DATE,
    customer_name VARCHAR, 
    customer_email VARCHAR, 
    customer_city VARCHAR,
    product_sku VARCHAR, 
    product_name VARCHAR, 
    category_name VARCHAR,
    unit_price DECIMAL(10,2), 
    quantity INTEGER
);
```

---

# The Flat Export NorthGate Actually Handed Us (cont.)

| order_id | order_date | customer_name | customer_email | customer_city | product_sku | product_name | category_name | unit_price | quantity |
|---|---|---|---|---|---|---|---|---|---|
| 1001 | 2026-06-01 | Ana Diaz | ana@example.com | San Jose | SKU-100 | Wireless Mouse | Electronics | 24.99 | 2 |
| 1001 | 2026-06-01 | Ana Diaz | ana@example.com | San Jose | SKU-210 | USB-C Cable | Electronics | 9.99 | 3 |
| 1002 | 2026-06-02 | Ben Ochoa | ben@example.com | Fremont | SKU-100 | Wireless Mouse | Electronics | 24.99 | 1 |
| 1003 | 2026-06-03 | Ana Diaz | ana@example.com | San Jose | SKU-330 | Yoga Mat | Fitness | 19.50 | 1 |
| 1004 | 2026-06-04 | Cy Nguyen | cy@example.com | Oakland | SKU-210 | USB-C Cable | Electronics | 9.99 | 5 |

This is genuinely how many real projects start — a report export, not a design.

---

# Naming the Anomalies

Querying this table live in DuckDB exposes three classic problems:

**Update anomaly** — Ana Diaz's email is stored on two separate rows. Fixing a typo means updating *every row she appears on*, and it is trivial to update one and miss the other, leaving contradictory data:

---

# Naming the Anomalies (cont.)

```sql
SELECT order_id, 
       customer_name, 
       customer_email 
FROM orders_flat 
WHERE customer_name = 'Ana Diaz';
```
```
 order_id | customer_name | customer_email
     1001 | Ana Diaz      | ana@example.com
     1003 | Ana Diaz      | ana@example.com     <- both must change together
```

**Insertion anomaly** — We cannot record a new product in the catalog until someone actually orders it, because there is no standalone place to put product facts.

**Deletion anomaly** — If we delete order 1002 (Ben Ochoa's only order), we silently lose *all* record that Ben Ochoa is a customer.

---

# Identifying the Functional Dependencies (FDs)

Before decomposing, we write down every FD we can 
observe — this is the actual engineering work of 
normalization, and it's what the rest of the process 
mechanically follows from:

```
order_id                  →  order_date, customer_name, customer_email, customer_city
customer_name             →  customer_email, customer_city
product_sku               →  product_name, category_name, unit_price
(order_id, product_sku)   →  quantity  [the only fact truly about the pairing]
```

The **candidate key** of `orders_flat` as given is 
`(order_id, product_sku)` — that's the minimal combination 
that determines every row's `quantity`. But look how many 
attributes (`order_date`, `customer_*`, `product_name`, 
`category_name`, `unit_price`) depend on only *part* of 
that key. That's the textbook definition of a **2NF violation**.

---

# 1NF — Atomicity (and a Warning Anti-Pattern)

**First Normal Form (1NF):** every column holds a single, 
atomic value — no repeating groups, no comma-packed lists.

Our `orders_flat` table, as given, is already in 1NF 
(one product per row). But it's instructive to see the 
violation an analyst might have handed us instead:

```sql
CREATE TABLE orders_flat_1nf_violation (
    order_id INTEGER, 
    customer_name VARCHAR,
    product_list VARCHAR   -- 'SKU-100:2, SKU-210:3'
);
```

---

# 1NF — Atomicity (and a Warning Anti-Pattern) (cont.)

```
 order_id | customer_name | product_list
     1001 | Ana Diaz      | SKU-100:2, SKU-210:3
```

You cannot write `WHERE product_sku = 'SKU-210'` 
against this table without ugly string parsing — 
the fix is exactly the row-per-line-item shape we 
already have. **1NF is why `order_items` has one 
row per product per order, not one row per order.**

---

# 2NF — Eliminate Partial Dependencies

**Second Normal Form (2NF):** the table is in 1NF, 
*and* every non-key attribute depends on the **entire** 
primary key — not just part of a composite key.

`order_date`, `customer_*` depend only on `order_id` 
(part of the key). `product_name`, `category_name`, 
`unit_price` depend only on `product_sku` (the other part). 
Both are **partial dependencies** — a 2NF violation. 

Fix: split them out.

---

# 2NF — Eliminate Partial Dependencies (cont.)

```sql
CREATE TABLE n2_orders (
   order_id PK, 
   order_date, 
   customer_name, 
   customer_email, 
   customer_city
);

CREATE TABLE n2_products (
   product_sku PK, 
   product_name, 
   category_name, 
   unit_price
);

CREATE TABLE n2_order_items (
   order_id FK, 
   product_sku FK,
   quantity, 
   PRIMARY KEY(order_id, product_sku)
);
```

---

# 2NF — Eliminate Partial Dependencies (cont.)

Verified in DuckDB — `n2_order_items` now holds 
*only* the fact that truly depends on the whole 
composite key:

```
 order_id | product_sku | quantity
     1001 | SKU-100     | 2
     1001 | SKU-210     | 3
```

---

# 3NF — Eliminate Transitive Dependencies

**Third Normal Form (3NF):** the table is in 2NF, 
*and* no non-key attribute depends on another non-key 
attribute (a **transitive dependency**).

In `n2_orders`, the key is `order_id`, but `customer_email` 
and `customer_city` don't really depend on `order_id` 
directly — they depend on **which customer** placed the 
order, i.e., on `customer_name`. 

That's transitive: `order_id → customer_name → customer_email`. 
Same story for `category_name` depending on the product's 
category identity inside `n2_products`. Fix: extract `customers` 
and `categories`, and mint **surrogate keys** since 
"`customer_name`" is not a safe real-world identifier 
(names collide!).

---

# 3NF — Eliminate Transitive Dependencies (cont.)

```sql
CREATE TABLE n3_customers  (
   customer_id PK, 
   customer_name, 
   customer_email UNIQUE, 
   customer_city
);

CREATE TABLE n3_categories (
   category_id PK, 
   category_name UNIQUE);

CREATE TABLE n3_products   (
   product_id PK, 
   product_sku UNIQUE, 
   product_name, 
   category_id FK, 
   unit_price
);

CREATE TABLE n3_orders (
   order_id PK, 
   order_date, 
   customer_id FK
);

CREATE TABLE n3_order_items(
   order_id FK, 
   product_id FK, 
   quantity, 
   PRIMARY KEY(order_id, product_id)
);
```

---

# 3NF Result — Verified in DuckDB

```
n3_customers                              n3_categories
 customer_id | customer_name | ...         category_id | category_name
      1      | Ana Diaz      | ...              1       | Electronics
      2      | Ben Ochoa     | ...              2       | Fitness
      3      | Cy Nguyen     | ...

n3_products                                              n3_orders
 product_id | product_sku | ... | category_id | price     order_id | order_date | customer_id
      1     | SKU-100     | ... |      1      | 24.99         1002 | 2026-06-02 |      2
      2     | SKU-210     | ... |      1      |  9.99         1003 | 2026-06-03 |      1
      3     | SKU-330     | ... |      2      | 19.50         1001 | 2026-06-01 |      1
                                                               1004 | 2026-06-04 |      3
```

**No data was lost.** Re-joining all five tables 
reconstructs the original flat report exactly — 
that's the acceptance test for a correct decomposition 
(verified with a 5-way join in DuckDB, matching the
original `orders_flat` row-for-row).

---

# BCNF and a Quick Sanity Check

**Boyce-Codd Normal Form (BCNF):** a slightly stronger 
version of 3NF — for *every* functional dependency 
`X → Y` in the table, `X` must be a candidate key 
(a "superkey"), full stop, even when `Y` is part of 
another candidate key. This matters mainly for tables 
with **multiple overlapping candidate keys**.

---

# BCNF and a Quick Sanity Check (cont.)

Checking our decomposed tables: `n3_customers` 
(key: `customer_id`, determinant `customer_id` only), 
`n3_products` (key: `product_id`), `n3_orders` (key: 
`order_id`), `n3_order_items` (key: `(order_id, product_id)`, 
and the only FD, `(order_id,product_id) → quantity`, has 
the *whole* key as its determinant). **Every determinant 
is a candidate key — our design is already in BCNF.** 
For most operational schemas (as opposed to specially 
contrived textbook examples), reaching 3NF with well-chosen 
surrogate keys reaches BCNF for free.

---

# When to Break the Rules: Controlled Denormalization

Recall requirement **R11**: *"the price at the time of purchase must be preserved even if the catalog price later changes."*

Look again at `order_items.unit_price` in our final design — it stores a **copy** of a value that also lives in `products.unit_price`. Strictly, that looks like the exact kind of redundancy 3NF tells us to eliminate!

This is **intentional, documented denormalization** — the two columns represent *different facts* that happen to often coincide:
- `products.unit_price` = "what we charge **today**."
- `order_items.unit_price` = "what we charged **at the moment of this specific sale**," a historical fact that must never change even as the catalog price moves.

**Rule of thumb:** normalize by default; denormalize only when you can name the specific business reason and the specific query/audit requirement that demands it — and document it right in the schema (a comment on the column).

---

<!-- _class: lead -->

# Part 4
## The Logical Schema

---

# From Conceptual to Logical: What Changes

* The **conceptual model** told us *what* exists. 
* The **logical model** commits to the exact table shape, keys, and constraints — still independent of any specific database product, but precise enough that translating it to DDL is mechanical.

Translation rules we've now applied throughout:

| Conceptual concept | Logical/relational construct |
|---|---|
| Entity | Table |
| Attribute | Column, with a domain (data type + allowed values) |
| Entity identifier | Primary key (often a surrogate) |
| 1:N relationship | Foreign key on the "many" side |
| M:N relationship | Associative table with a composite key (two FKs) |
| Relationship with its own attributes | Associative table with extra columns |
| Recursive relationship | Self-referencing foreign key |
| Categorical attribute w/ fixed values | Enumerated domain / `CHECK IN (...)` |

---

# The Finalized Table List (15 Tables)

| Table | Purpose | Primary Key |
|---|---|---|
| `customers` | registered shoppers | `customer_id` |
| `addresses` | billing/shipping addresses | `address_id` |
| `categories` | product taxonomy (self-referencing) | `category_id` |
| `suppliers` | vendors | `supplier_id` |
| `products` | catalog items | `product_id` |
| `product_suppliers` | M:N: who supplies what, at what cost | `(product_id, supplier_id)` |
| `warehouses` | stocking locations | `warehouse_id` |
| `inventory` | M:N: stock levels per product per warehouse | `(product_id, warehouse_id)` |
| `orders` | purchase transactions | `order_id` |
| `order_items` | line items within an order | `(order_id, line_number)` |
| `coupons` | discount codes | `coupon_id` |
| `order_coupons` | M:N: coupons applied to orders | `(order_id, coupon_id)` |
| `payments` | money received against orders | `payment_id` |
| `shipments` | physical deliveries | `shipment_id` |
| `reviews` | customer feedback on products | `review_id` |

---

# Keys, Formally

- **Candidate key** — any minimal set of attributes that uniquely identifies a row. `products` has *two* candidate keys: `product_id` and `sku`.
- **Primary key (PK)** — the candidate key we choose as *the* identifier. We consistently choose the **surrogate** (`product_id`) as PK and demote the natural key (`sku`) to an **alternate key** enforced via `UNIQUE`.
- **Alternate key** — a candidate key not chosen as PK (`customers.email`, `products.sku`, `categories.category_name`, `coupons.code`).
- **Foreign key (FK)** — an attribute (or set) that must match a candidate key value in another table (or be `NULL`, if optional), implementing a relationship.
- **Composite key** — a PK made of multiple columns, typical of associative entities (`order_items`, `inventory`, `product_suppliers`, `order_coupons`).

---

# Keys, Formally (cont.)

**Why surrogate keys as PK?** Natural keys can change (a company can rebrand a SKU), can be reused, or can be composite and unwieldy to reference from many other tables. Surrogates are immutable, compact, and DBMS-generated.

---

# Referential Integrity — The Relationship Map

| Child table | Foreign key | Parent table | Cardinality |
|---|---|---|---|
| `addresses` | `customer_id` | `customers` | `N : 1` |
| `categories` | `parent_category_id` | `categories (self)` | `N : 1` |
| `products` | `category_id` | `categories` | `N : 1` |
| `product_suppliers` | `product_id`, `supplier_id` | `products`, `suppliers` | `N : 1`, `N : 1` |
| `inventory` | `product_id`, `warehouse_id` | `products`, `warehouses` | `N : 1`, `N : 1` |
| `orders` | `customer_id`, `shipping_address_id`, `billing_address_id` | `customers`, `addresses`, `addresses` | `N : 1 (×3)` |
| `order_items` | `order_id`, `product_id` | `orders`, `products` | `N : 1`, `N : 1` |
| `order_coupons` | `order_id`, `coupon_id` | `orders`, `coupons` | `N : 1`, `N : 1` |
| `payments` | `order_id` | `orders` | `N : 1` |
| `shipments` | `order_id` | `orders` | `N : 1` |
| `reviews` | `product_id`, `customer_id` | `products`, `customers` | `N : 1`, `N : 1` |

Every row in this table becomes a `REFERENCES` clause in the physical DDL — the mapping is direct.

---

# Three Kinds of Integrity We Must Enforce

1. **Entity integrity** — every table has a primary key, and primary key values are never `NULL` and never duplicated. (Guaranteed by `PRIMARY KEY`.)

2. **Referential integrity** — a foreign key value must either be `NULL` (if the relationship is optional) or match an existing primary key value in the referenced table. No order may point to a customer that doesn't exist; no order line may point to a nonexistent product. (Guaranteed by `FOREIGN KEY … REFERENCES`.)

3. **Domain / business-rule integrity** — a column's value must be within its legal domain: `rating` must be 1–5, `unit_price` must be ≥ 0, `status` must be one of six known lifecycle states. (Guaranteed by `CHECK` constraints and enumerated types.)

The logical model specifies *all three* — the physical model is where we prove the database actually enforces them, which we do later with live constraint-violation tests.

---

<!-- _class: lead -->

# Part 5
## The Physical Model in DuckDB

---

# From Logical to Physical: Type Mapping

| Logical domain | DuckDB physical type | Why |
|---|---|---|
| Surrogate ID | `INTEGER` + `SEQUENCE` | compact, ordered, auto-generated |
| Money | `DECIMAL(10,2)` | exact decimal arithmetic — never `FLOAT` for currency |
| Free text (bounded) | `VARCHAR` | DuckDB's `VARCHAR` is unbounded/UTF-8, no need for artificial length limits |
| Yes/No flag | `BOOLEAN` | e.g., `is_default`, `is_active` |
| Calendar date | `DATE` | order dates, coupon validity windows |
| Point in time | `TIMESTAMP` | `created_at`, `paid_at`, `shipped_at` |
| Fixed vocabulary | `ENUM` | `order_status`, `payment_method` — see next slide |
| 1–5 rating, non-negative qty | `INTEGER` + `CHECK` | type alone can't stop `rating = 47`; need a constraint too |

DuckDB is used here purely as our target *physical* engine — this mapping table is the same exercise you'd repeat (with different specific types) for PostgreSQL or SQL Server.

---

# DuckDB Feature Spotlight: `ENUM` Types

Rather than a free-text `status VARCHAR` column plus an application-level whitelist, DuckDB lets us encode the controlled vocabulary **in the schema itself**:

```sql
CREATE TYPE order_status   AS ENUM ('PENDING','PAID','SHIPPED','DELIVERED','CANCELLED','REFUNDED');
CREATE TYPE address_type   AS ENUM ('BILLING','SHIPPING');
CREATE TYPE payment_method AS ENUM ('CREDIT_CARD','PAYPAL','GIFT_CARD','BANK_TRANSFER');
CREATE TYPE payment_status AS ENUM ('AUTHORIZED','CAPTURED','FAILED','REFUNDED');
```

Benefits over `VARCHAR` + `CHECK IN (...)`: values are stored as compact integers internally (fast, small), typos are caught at `INSERT` time (`'Shiped'` simply fails), and the legal value set is self-documenting via `SELECT enum_range(NULL::order_status)`.

This is the physical-layer expression of the **domain integrity** requirement (R10, R2, business rules on payment methods) we specified in the logical model.

---

# DuckDB Feature Spotlight: Sequences for Surrogate Keys

DuckDB supports explicit sequence objects (similar to PostgreSQL), which we use to generate every surrogate primary key:

```sql
CREATE SEQUENCE seq_customer_id START 1;
CREATE SEQUENCE seq_order_id    START 1001;   -- orders start numbering at 1001
...
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY DEFAULT nextval('seq_customer_id'),
    ...
);
```

Each `INSERT` that omits `customer_id` gets the next value automatically — the application never has to compute or guess IDs, and IDs are guaranteed unique even under concurrent inserts. (DuckDB also supports `GENERATED ALWAYS AS IDENTITY` in recent versions; we use explicit sequences here because they make the ID-generation mechanism visible for teaching purposes, and because we deliberately want `seq_order_id` to start at 1001 to match NorthGate's existing order numbers.)

---

# Physical DDL — `customers` and `addresses`

```sql
CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY DEFAULT nextval('seq_customer_id'),
    first_name    VARCHAR NOT NULL,
    last_name     VARCHAR NOT NULL,
    email         VARCHAR NOT NULL UNIQUE,          -- R1: alternate key
    phone         VARCHAR,
    created_at    TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE addresses (
    address_id    INTEGER PRIMARY KEY DEFAULT nextval('seq_address_id'),
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),  -- R2, R3: mandatory FK
    addr_type     address_type NOT NULL,             -- R2: controlled vocabulary
    street        VARCHAR NOT NULL,
    city          VARCHAR NOT NULL,
    state_region  VARCHAR,
    postal_code   VARCHAR,
    country       VARCHAR NOT NULL,
    is_default    BOOLEAN NOT NULL DEFAULT FALSE
);
```

Executed against DuckDB 1.5 with zero errors.

---

# Physical DDL — `categories`, `suppliers`, `products`

```sql
CREATE TABLE categories (
    category_id        INTEGER PRIMARY KEY DEFAULT nextval('seq_category_id'),
    category_name      VARCHAR NOT NULL UNIQUE,
    parent_category_id INTEGER REFERENCES categories(category_id)   -- R5: self-reference
);

CREATE TABLE suppliers (
    supplier_id   INTEGER PRIMARY KEY DEFAULT nextval('seq_supplier_id'),
    supplier_name VARCHAR NOT NULL,
    contact_email VARCHAR
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY DEFAULT nextval('seq_product_id'),
    sku           VARCHAR NOT NULL UNIQUE,                       -- R4: natural/alternate key
    product_name  VARCHAR NOT NULL,
    category_id   INTEGER NOT NULL REFERENCES categories(category_id),
    unit_price    DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0), -- R4: domain rule
    description   VARCHAR,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE                   -- R7
);
```

---

# Physical DDL — Associative Tables (M:N)

```sql
CREATE TABLE product_suppliers (                     -- R6
    product_id   INTEGER NOT NULL REFERENCES products(product_id),
    supplier_id  INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    supply_price DECIMAL(10,2) NOT NULL CHECK (supply_price >= 0),
    PRIMARY KEY (product_id, supplier_id)             -- composite key
);

CREATE TABLE warehouses (
    warehouse_id   INTEGER PRIMARY KEY DEFAULT nextval('seq_warehouse_id'),
    warehouse_name VARCHAR NOT NULL, city VARCHAR, country VARCHAR
);

CREATE TABLE inventory (                              -- R8, R9
    product_id       INTEGER NOT NULL REFERENCES products(product_id),
    warehouse_id     INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    quantity_on_hand INTEGER NOT NULL CHECK (quantity_on_hand >= 0),  -- R9
    PRIMARY KEY (product_id, warehouse_id)
);
```

Both tables directly implement the "relationship carries its own attribute" pattern from Part 2.

---

# Physical DDL — `orders` and `order_items`

```sql
CREATE TABLE orders (
    order_id            INTEGER PRIMARY KEY DEFAULT nextval('seq_order_id'),
    customer_id         INTEGER NOT NULL REFERENCES customers(customer_id),   -- R3
    order_date          TIMESTAMP NOT NULL DEFAULT current_timestamp,
    status              order_status NOT NULL DEFAULT 'PENDING',              -- R10
    shipping_address_id INTEGER NOT NULL REFERENCES addresses(address_id),
    billing_address_id  INTEGER NOT NULL REFERENCES addresses(address_id)
);

CREATE TABLE order_items (
    order_id     INTEGER NOT NULL REFERENCES orders(order_id),
    line_number  INTEGER NOT NULL,
    product_id   INTEGER NOT NULL REFERENCES products(product_id),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    unit_price   DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),  -- R11: price AT TIME OF SALE
    PRIMARY KEY (order_id, line_number)
);
```

Notice `orders` has **three** foreign keys to two different tables (`customers` once, `addresses` twice) — perfectly legal, and a good example of a table needing multiple relationships to the same neighbor.

---

# Physical DDL — Coupons, Payments, Shipments, Reviews

```sql
CREATE TABLE coupons (                                        -- R13
    coupon_id    INTEGER PRIMARY KEY DEFAULT nextval('seq_coupon_id'),
    code         VARCHAR NOT NULL UNIQUE,
    discount_pct DECIMAL(5,2) NOT NULL CHECK (discount_pct BETWEEN 0 AND 100),
    valid_from   DATE NOT NULL,
    valid_to     DATE NOT NULL CHECK (valid_to >= valid_from)   -- cross-column business rule
);
CREATE TABLE order_coupons (
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    coupon_id INTEGER NOT NULL REFERENCES coupons(coupon_id),
    PRIMARY KEY (order_id, coupon_id)
);
CREATE TABLE payments (                                        -- R12
    payment_id INTEGER PRIMARY KEY DEFAULT nextval('seq_payment_id'),
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    method payment_method NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    paid_at TIMESTAMP, status payment_status NOT NULL DEFAULT 'AUTHORIZED'
);
CREATE TABLE reviews (                                          -- R14, R15
    review_id INTEGER PRIMARY KEY DEFAULT nextval('seq_review_id'),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),      -- R14
    review_text VARCHAR, created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);
```

---

# Verifying the Schema Actually Built

```sql
SHOW TABLES;
```

```
 addresses  categories  coupons     customers  inventory
 order_coupons  order_items  orders  payments  product_suppliers
 products   reviews     shipments   suppliers  warehouses
```

15 tables, executed and confirmed in a live DuckDB session — every `CREATE TYPE`, `CREATE SEQUENCE`, and `CREATE TABLE` statement ran without a single error, in dependency order (parents before children, since DuckDB validates `REFERENCES` targets exist at creation time).

**Practical lesson:** DDL for a relational schema must be written and executed in **topological order** of the foreign-key graph — you cannot create `order_items` before `orders` and `products` exist.

---

# Proof the Constraints Actually Fire (Not Just Documentation)

A schema's constraints are only as good as their enforcement. We tested this live:

```sql
-- Attempt to insert a line item for an order that doesn't exist
INSERT INTO order_items (order_id, line_number, product_id, quantity, unit_price)
VALUES (9999, 1, 1, 1, 10.00);
```
```
ConstraintException: Constraint Error: Violates foreign key constraint because
key "order_id: 9999" does not exist in the referenced table
```

```sql
-- Attempt to insert a product with a negative price
INSERT INTO products (sku, product_name, category_id, unit_price)
VALUES ('SKU-999','Bad Price', 1, -5.00);
```
```
ConstraintException: Constraint Error: CHECK constraint failed on table
products with expression CHECK((unit_price >= 0))
```

Both failures are **exactly what we want** — the database itself is the last line of defense against bad data, regardless of what any application layer forgets to validate.

---

<!-- _class: lead -->

# Part 6
## Loading Data and Answering Business Questions

---

# Populating the Model

We inserted representative rows into all 15 tables — 5 customers (one, "Emma Chen," deliberately has *no orders yet*, to test optional participation), 8 addresses, 4 categories (with the Electronics→Accessories hierarchy), 2 suppliers, 5 products, 2 warehouses, 5 orders spanning the full status lifecycle, 6 order line items, 2 coupons, 4 payments, 3 shipments, and 4 reviews.

---

# Populating the Model (cont.)

```
customers 5   
addresses 8       
categories 4        
suppliers 2
products  5   
product_suppliers 4   
warehouses 2     
inventory 8
orders    5   
order_items 6     
coupons 2           
order_coupons 1
payments  4   
shipments 3       
reviews 4
```

Every row satisfied every constraint on the first attempt — strong evidence the schema faithfully matches the business rules it was derived from.

---

# Query 1 — Walking the Customer → Order Relationship

```sql
SELECT c.first_name || ' ' || c.last_name AS customer,
       o.order_id, o.order_date::DATE AS order_date, o.status
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_date;
```

```
 customer  | order_id | order_date | status
 Ana Diaz  |   1001   | 2026-06-01 | DELIVERED
 Ana Diaz  |   1003   | 2026-06-03 | SHIPPED
 Ben Ochoa |   1002   | 2026-06-02 | DELIVERED
 Cy Nguyen |   1004   | 2026-06-04 | PAID
 Dana Kim  |   1005   | 2026-06-10 | PENDING
```

Note **Emma Chen does not appear** — an `INNER JOIN` correctly excludes her since she has no matching order row, exactly reflecting "Customer optional / Order mandatory" participation from our ERD.

---

# Query 2 — Order Line Detail (Three-Way Join)

```sql
SELECT o.order_id, p.product_name, oi.quantity, oi.unit_price,
       (oi.quantity * oi.unit_price)::DECIMAL(10,2) AS line_total
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
ORDER BY o.order_id, oi.line_number;
```

```
 order_id | product_name        | quantity | unit_price | line_total
   1001   | Wireless Mouse      |    2     |   24.99    |   49.98
   1001   | USB-C Cable 2m      |    3     |    9.99    |   29.97
   1002   | Wireless Mouse      |    1     |   24.99    |   24.99
   1003   | Yoga Mat            |    1     |   19.50    |   19.50
   1004   | USB-C Cable 2m      |    5     |    9.99    |   49.95
   1005   | Mechanical Keyboard |    1     |   84.99    |   84.99
```

Order 1005's keyboard sold at **84.99**, below the current catalog price of **89.00** — exactly the historical-price scenario R11 was designed to protect.

---

# Query 3 — Aggregating to Order Totals

```sql
SELECT o.order_id, c.first_name || ' ' || c.last_name AS customer,
       SUM(oi.quantity * oi.unit_price)::DECIMAL(10,2) AS order_total
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, customer
ORDER BY o.order_id;
```

```
 order_id | customer  | order_total
   1001   | Ana Diaz  |   79.95
   1002   | Ben Ochoa |   24.99
   1003   | Ana Diaz  |   19.50
   1004   | Cy Nguyen |   49.95
   1005   | Dana Kim  |   84.99
```

This is the query that justifies keeping `order_items` separate from `orders`: the order total is *derived*, never stored — a direct dividend of normalization (no stored total to fall out of sync with its line items).

---

# Query 4 — Revenue by Category (Marketing's Ask)

```sql
SELECT cat.category_name,
       SUM(oi.quantity * oi.unit_price)::DECIMAL(10,2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN categories cat ON cat.category_id = p.category_id
GROUP BY cat.category_name
ORDER BY revenue DESC;
```

```
 category_name | revenue
 Accessories   |  154.89
 Electronics   |   84.99
 Fitness       |   19.50
```

This four-table join (`order_items → products → categories`, plus the implicit link through `orders`) is only possible *because* we normalized: category, product, and order-line facts each live in exactly one place, so joining them back together always produces a consistent answer.

---

# Query 5 — Average Rating per Product

```sql
SELECT p.product_name, ROUND(AVG(r.rating),2) AS avg_rating, COUNT(*) AS num_reviews
FROM reviews r JOIN products p ON p.product_id = r.product_id
GROUP BY p.product_name
ORDER BY avg_rating DESC;
```

```
 product_name    | avg_rating | num_reviews
 Yoga Mat        |    5.0     |     1
 Wireless Mouse  |    4.5     |     2
 USB-C Cable 2m  |    3.0     |     1
```

Because `reviews.rating` is protected by `CHECK (rating BETWEEN 1 AND 5)`, this average is guaranteed meaningful — no application code anywhere needs to re-validate that a rating is sane before trusting it in a report.

---

# Query 6 — Low Stock Alert (Warehouse Ops' Ask)

```sql
SELECT p.product_name, w.warehouse_name, i.quantity_on_hand
FROM inventory i
JOIN products p ON p.product_id = i.product_id
JOIN warehouses w ON w.warehouse_id = i.warehouse_id
WHERE i.quantity_on_hand < 50
ORDER BY i.quantity_on_hand;
```

```
 product_name        | warehouse_name | quantity_on_hand
 Mechanical Keyboard | East Coast DC  |       10
 Mechanical Keyboard | West Coast DC  |       25
 French Press        | West Coast DC  |       45
```

This query only makes sense because `inventory` is its own associative entity keyed on `(product_id, warehouse_id)` — stock is a fact about a **product-at-a-warehouse**, not about the product alone (a product can be well-stocked in one warehouse and nearly out in another).

---

# Query 7 — Window Function: Running Revenue

```sql
SELECT o.order_id, o.order_date::DATE AS order_date,
       SUM(oi.quantity*oi.unit_price)::DECIMAL(10,2) AS order_total,
       SUM(SUM(oi.quantity*oi.unit_price)) OVER (ORDER BY o.order_date)::DECIMAL(10,2) AS running_revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_date
ORDER BY o.order_date;
```

```
 order_id | order_date | order_total | running_revenue
   1001   | 2026-06-01 |   79.95     |    79.95
   1002   | 2026-06-02 |   24.99     |   104.94
   1003   | 2026-06-03 |   19.50     |   124.44
   1004   | 2026-06-04 |   49.95     |   174.39
   1005   | 2026-06-10 |   84.99     |   259.38
```

A well-normalized transactional schema is also the right foundation for analytics — window functions like this are exactly where DuckDB's columnar engine shines.

---

# Query 8 — Anti-Join: Customers With No Orders Yet

```sql
SELECT c.first_name || ' ' || c.last_name AS customer
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;
```

```
 customer
 Emma Chen
```

This confirms, with a live query, the exact optional-participation rule we designed back in Part 2 ("Customer optional, Order mandatory"): the schema *allows* a customer to exist with zero orders, and here we find one. If this query ever returned customers we *expected* to have ordered, that would be a data-quality signal, not a schema bug — the model correctly distinguishes the two.

---

<!-- _class: lead -->

# Part 7
## Design Considerations & Best Practices

---

# Surrogate vs. Natural Keys — Revisited

| | Surrogate key (`customer_id`) | Natural key (`email`, `sku`) |
|---|---|---|
| Stability | Never changes | Can change (rebrand, typo fix) |
| Meaning | None outside the DB | Meaningful to the business |
| Join cost | Small integer — cheap | Often wider strings — costlier |
| Uniqueness guarantee | Guaranteed by the DB (`SEQUENCE`) | Must be guaranteed by the business process |

**Best practice used throughout this schema:** surrogate integer PKs for every entity, with natural keys retained and protected by `UNIQUE` constraints wherever the business genuinely has one (`email`, `sku`, `category_name`, `coupon.code`). You get referential stability *and* business-rule enforcement.

---

# When (and When Not) to Denormalize

Normalize first — always. Denormalize only for a **named, specific reason**, and prefer these safer forms of denormalization over "just duplicate everything":

- **Historical/point-in-time snapshots** (our `order_items.unit_price`) — the duplicate represents a *different fact* (price-then vs. price-now), not redundant storage of the *same* fact.
- **Materialized/derived aggregates for reporting** (e.g., a `daily_revenue_by_category` summary table refreshed nightly) — kept clearly separate from the normalized operational tables, rebuilt from them, never hand-edited.
- **Read-heavy analytical views** — in DuckDB, a `CREATE VIEW` (or even just running the analytical join at query time, since DuckDB is fast) is usually preferable to physically duplicating columns, because a view can never drift out of sync.

Avoid denormalizing simply to save a `JOIN` — modern engines, DuckDB very much included, are built to make joins cheap.

---

# Indexing in DuckDB — A Different Mental Model

If you're coming from row-oriented OLTP databases (PostgreSQL, MySQL), you may reflexively reach for `CREATE INDEX` on every foreign key. DuckDB is a **columnar, vectorized OLAP engine**, and its performance model is different:

- DuckDB automatically builds **zone maps / min-max statistics** per column chunk, which already accelerate range filters and joins without any manual index.
- `PRIMARY KEY` / `UNIQUE` constraints automatically maintain an **ART (Adaptive Radix Tree) index** to enforce uniqueness — you get point-lookup speed on keys "for free" from the constraint itself.
- Manual secondary indexes (`CREATE INDEX`) are still supported and can help for very selective point lookups on large tables, but they are not the primary performance lever the way they are in row-oriented engines — good physical design (correct types, correct constraints) matters more.

**Takeaway:** in DuckDB, get the relational design right first; reach for explicit indexing only after measuring an actual bottleneck.

---

# Evolving the Schema Over Time

Requirements change. NorthGate will eventually want wishlists, product bundles, multi-currency pricing, or return/refund workflows. A well-normalized schema evolves gracefully because responsibilities are already separated:

```sql
-- Adding "wishlist" doesn't touch orders at all -- it's a new relationship
CREATE SEQUENCE seq_wishlist_id START 1;
CREATE TABLE wishlists (
    wishlist_id INTEGER PRIMARY KEY DEFAULT nextval('seq_wishlist_id'),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    added_at    TIMESTAMP NOT NULL DEFAULT current_timestamp,
    UNIQUE (customer_id, product_id)
);
```

Contrast this with a poorly normalized design where customer and product facts are smeared across many tables — every new feature would require touching (and risking) existing, working tables.

---

# Extending the Model with EER: A New Requirement

Six months after launch, NorthGate adds two optional programs:

> **R16.** A customer may open a **business account** — company name, a **unique**
> tax ID, and a credit limit (≥ 0) — to be invoiced instead of paying by card.
> A customer may also join the **loyalty program** — a tier (`SILVER`, `GOLD`,
> `PLATINUM`) and a points balance (≥ 0). A customer can be in **both, either, or
> neither**.

Business accounts and loyalty members are still **customers** — same ID, same
email, same orders — with extra attributes only some customers have. That is a
**specialization** of `Customer`, an Enhanced ER (EER) concept.

---

# The EER Diagram (Text Form)

```
                    CUSTOMER
        customer_id, first_name, last_name, email, phone
                       │
                       ○  (overlapping, partial)
              ┌────────┴────────┐
      BUSINESS_ACCOUNT     LOYALTY_MEMBER
      company_name         tier
      tax_id (unique)      points
      credit_limit         joined_on
```

* **Overlapping (o)** — one customer can be in *both* subtypes. (The Week 1
  notes' payment example is **disjoint (d)**: a payment is one kind or the other.)
* **Partial** — a customer can be in *neither*. (**Total** would mean every
  customer must be in at least one.)
* Each subtype holds **only its own attributes**; the shared ones stay on `CUSTOMER`.

---

# The Four Combinations — Where This One Sits

| | **Total** (every member is in some subtype) | **Partial** (some are in none) |
|---|---|---|
| **Disjoint** (at most one subtype) | Payment → card *or* bank transfer — the Week 1 notebook | Employee → manager *or* engineer, many neither |
| **Overlapping** (may be several) | Person → student *and/or* staff, at a university where everyone is one | **Customer → business account and/or loyalty member — R16** |

The two constraints are **independent** business rules: decide each one by asking
the business, then enforce it in the database.

---

# Implementing a Specialization: Three Options

| Option | Tables | Fits R16? |
|---|---|---|
| **One table per subtype** (shared primary key) | `customers` + `business_accounts` + `loyalty_members` | ✅ Overlap = rows in both; partial = rows in neither |
| **One wide table** with nullable subtype columns | `customers` gains `company_name`, `tax_id`, `tier`, … | ⚠️ Works, but `NULL`s everywhere and "credit limit ≥ 0 *only for* business accounts" needs complex `CHECK`s |
| **A `customer_type` column** | `customers.customer_type = 'BUSINESS'` | ❌ One value per row — can't say "business **and** loyalty" |

The last row is the trap: a single type column **forces** a disjoint
specialization. R16 is overlapping, so it needs one table per subtype.

---

# Physical DDL — The Subtype Tables

```sql
-- R16: each subtype's primary key IS a foreign key to the supertype
CREATE TABLE business_accounts (
    customer_id   INTEGER PRIMARY KEY REFERENCES customers(customer_id),
    company_name  VARCHAR NOT NULL,
    tax_id        VARCHAR NOT NULL UNIQUE,
    credit_limit  DECIMAL(10,2) NOT NULL CHECK (credit_limit >= 0)
);

CREATE TYPE loyalty_tier AS ENUM ('SILVER','GOLD','PLATINUM');
CREATE TABLE loyalty_members (
    customer_id  INTEGER PRIMARY KEY REFERENCES customers(customer_id),
    tier         loyalty_tier NOT NULL,
    points       INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
    joined_on    DATE NOT NULL
);
```

`customer_id` as the **primary key** means a customer appears **at most once** per
subtype; as a **foreign key**, every subtype row belongs to a real customer.

---

# Sample Data and the Proof

```sql
INSERT INTO business_accounts VALUES
 (2, 'Ochoa Design LLC',     '94-1234567',  5000.00),
 (3, 'Nguyen Robotics Inc.', '77-7654321', 12000.00);
INSERT INTO loyalty_members VALUES
 (1, 'GOLD',   1200, DATE '2025-03-14'),
 (2, 'SILVER',  300, DATE '2026-01-09');
```

| customer_id | first_name | business_account | loyalty_member |
|---:|---|---|---|
| 1 | Ana | false | true |
| 2 | Ben | true | **true** ← overlapping |
| 3 | Cy | true | false |
| 4 | Dana | false | false ← partial |
| 5 | Emma | false | false ← partial |

---

# Checking the Constraints with SQL

```sql
WITH roles AS (
    SELECT c.customer_id,
           b.customer_id IS NOT NULL AS is_business,
           l.customer_id IS NOT NULL AS is_loyalty
    FROM customers AS c
    LEFT JOIN business_accounts AS b ON b.customer_id = c.customer_id
    LEFT JOIN loyalty_members   AS l ON l.customer_id = c.customer_id
)
SELECT COUNT(*) FILTER (WHERE is_business AND is_loyalty)         AS in_both,
       COUNT(*) FILTER (WHERE NOT is_business AND NOT is_loyalty) AS in_neither
FROM roles;
```

Result: `in_both = 1`, `in_neither = 2` — both allowed by R16. Under a **disjoint**
rule, `in_both` must be 0; under a **total** rule, `in_neither` must be 0. The
same query audits either rule.

The database still **rejects**: a business account for customer 99 (FK), a
negative credit limit (`CHECK`), a reused tax ID (`UNIQUE`), Ana joining the
loyalty program twice (PK), and a `BRONZE` tier (`ENUM`).

---

# Common Modeling Pitfalls Checklist

A quick self-review checklist for your own schemas:

1. **Does every table have a real primary key?** ("No PK" is the single most common real-world schema defect.)
2. **Is every foreign key actually declared as a `FOREIGN KEY`?** — an "implied" relationship enforced only in application code will eventually be violated.
3. **Are there columns that repeat data already stored elsewhere, without a documented reason?** (Silent denormalization.)
4. **Are business rules (ranges, enumerations, cross-column rules) enforced with `CHECK`, or only in application code?**
5. **Can you trace every table back to a specific business requirement?** If not, ask why it exists.
6. **Did you test constraint violations, not just the happy path?** (We did — Part 5, live `ConstraintException`s.)

---

<!-- _class: lead -->

# Part 8
## Summary and Exercises

---

# The Journey, Recapped

```
Business Requirements (R1–R15, plain English)
        │  noun/verb extraction
        ▼
Conceptual Model  (entities, attributes, relationships, ERD, cardinality)
        │  normalize (1NF → 2NF → 3NF), resolve M:N via associative entities
        ▼
Logical Model  (15 tables, keys, FK map, 3 kinds of integrity)
        │  choose engine-specific types, sequences, enums
        ▼
Physical Model  (DuckDB DDL — executed, verified, constraint-tested)
        │  load data, query
        ▼
Answers to real business questions, with data quality guaranteed by the schema
```

Every arrow in this pipeline was demonstrated, live, against a running DuckDB database in this module — not just described.

---

# Key Takeaways

- **Requirements drive design.** Every table, key, and constraint in the final schema traces back to a specific sentence in the business requirements (R1–R15).
- **Normalization is a tool for eliminating redundancy and anomalies**, not a bureaucratic checkbox — we demonstrated real update/insert/delete anomalies and watched them disappear after decomposition.
- **Relationships with their own attributes, and all M:N relationships, become their own tables** (associative entities) — this single rule resolved four of our trickiest requirements.
- **Denormalization is a deliberate, documented exception**, applied for a named reason (historical pricing), never a default.
- **The database itself should enforce integrity** — constraints caught bad data live, in this session, that application code might have missed.
- **DuckDB is a fully capable relational engine** for learning and validating these principles, even though it's best known for analytics.

---

# Exercises for Further Practice

1. **Extend the model:** NorthGate wants to support **product returns**. Model a `returns` entity — what does it reference, what new status values does `orders.status` (or a new table) need, and does any existing table need a new nullable foreign key?
2. **Normalize this:** given a flat table `(employee_id, employee_name, department_name, department_manager, project_name, hours_logged)`, find the functional dependencies and decompose to 3NF.
3. **Multi-currency:** NorthGate is expanding to Canada. Redesign `unit_price` handling so orders can be placed in either USD or CAD without losing the "price at time of sale" guarantee from R11.
4. **Constraint design:** write a `CHECK` constraint (or a small set of tables) that prevents a `shipments.shipped_at` from being earlier than its order's `orders.order_date`.
5. **Query practice:** write a query that finds every product that has *never* been ordered, using the schema from this module.

---

# Further Reading

- Codd, E.F. (1970). *A Relational Model of Data for Large Shared Data Banks.* — the original paper that started it all.
- Date, C.J. *An Introduction to Database Systems* — the standard graduate reference for relational theory and normalization.
- Elmasri & Navathe. *Fundamentals of Database Systems* — strong treatment of ER modeling and normal forms with worked examples.
- DuckDB documentation: [https://duckdb.org/docs/](https://duckdb.org/docs/) — types, constraints, `ENUM`, sequences, and SQL reference used throughout this module.

<br>

**Everything in this deck — every schema, every row, every query result, every constraint-violation error — was generated by actually running the SQL in DuckDB 1.5.4. Load the code yourself and re-run it to build your intuition.**

---

<!-- _class: lead -->

# Questions?
