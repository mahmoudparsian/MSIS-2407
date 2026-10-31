# ERD Notation Guide

A short, standalone reference for the entity-relationship diagram (ERD) notation used throughout the Week 1 Data Modeling case studies (music catalog, PageTurner Books, and NorthGate e-commerce). 

Read this document once and you can read every diagram in the case studies.

## 1. The Three Building Blocks

An ER diagram has only three kinds of things on it:

- **Entity** — a box, representing a *type* of real-world thing the business tracks (`Customer`, `Book`, `Order`). Each entity becomes a table.

- **Attribute** — a property of an entity (`Customer.email`, `Book.price`). In our tutorials, attributes are usually listed in a table underneath the diagram rather than drawn as circles on the diagram itself — this keeps the diagram readable.


- **Relationship** — a line connecting two entities, describing how instances of one relate to instances of the other (`Customer places Order`).

Almost everything in this guide is about how to read the *symbols at the ends of a relationship line*, because that's where all the meaning lives.

## 2. Cardinality: "One" vs. "Many"

Cardinality answers: *for a single instance of Entity A, how many instances of Entity B can it be linked to?* There are only two options at each end of a line:

- **One** — linked to at most one instance on the other side.
- **Many** — linked to any number of instances on the other side.

## 3. Participation: "Mandatory" vs. "Optional"

Participation answers a different question: *does every instance of this entity have to participate in the relationship at all?*

- **Mandatory** — every row of this entity *must* have at least one link. (Example: every `Order` must belong to a `Customer` — an order can't exist in a vacuum.)
- **Optional** — a row of this entity is allowed to have zero links. (Example: a `Customer` can exist with zero `Order`s — someone can register without ever buying anything.)

Cardinality and participation are *independent* — you need both to fully describe one end of a relationship.

## 4. Crow's Foot Symbols

We use **crow's foot notation**, the most common ERD style in industry. Each end of a relationship line gets one of four symbols, combining cardinality and participation:

| Symbol (at one end of the line) | Cardinality | Participation | Plain-English meaning |
|---|---|---|---|
| `──┤├──` | One | Mandatory | "exactly one" |
| `──○├──` | One | Optional | "zero or one" |
| `──┤<──` | Many | Mandatory | "one or more" |
| `──○<──` | Many | Optional | "zero or more" |

How to remember the pieces: the **crow's foot** (`<`, the three-pronged fork) means *many*; a **single bar** (`│`) close to the entity means *mandatory*; a **circle** (`○`) close to the entity means *optional*. The symbol always sits on the end of the line **closest to the entity it describes** — read it as "from the other entity's point of view, looking at this one."

## 5. Reading a Full Relationship Line

A relationship line has a symbol at *each* end, and you read each end separately. Take this line from the PageTurner Books tutorial:

```
Customer ──┤├───────○<── Order
```

Read it in two halves:

- The end touching `Customer` is `┤├` (one, mandatory) — but it describes **how many Customers a given Order connects to**. So: *"each Order relates to exactly one Customer."*
- The end touching `Order` is `○<` (many, optional) — it describes **how many Orders a given Customer connects to**. So: *"each Customer relates to zero-or-more Orders."*

Put together: *"Every order belongs to exactly one customer; a customer may have placed no orders, one order, or many."* This is the classic **one-to-many (1:N)** relationship, and it's the single most common pattern you'll draw.

**The rule of thumb:** the symbol touching an entity tells you about the *other* entity's relationship to it, not about itself.

## 6. The Four Everyday Combinations, Worked

| Diagram | Reads as | Example from our tutorials |
|---|---|---|
| `A ──┤├───○<── B` | One A has zero-or-more B's; each B has exactly one A | `Customer ──┤├───○<── Order` |
| `A ──┤├───┤<── B` | One A has one-or-more B's; each B has exactly one A | `Order ──┤├───┤<── OrderItem` (an order line can't exist without its order, and — going the other way — every order needs at least one line) |
| `A ──○├───○<── B` | One A has zero-or-more B's; each B has zero-or-one A | Rare in our schemas — usually a sign a relationship is genuinely optional on *both* sides |
| `A ──┤<───┤<── B` | Many-to-many: one A relates to many B's, and one B relates to many A's | `Product ──┤<───┤<── Supplier` (e-commerce tutorial) |

## 7. One-to-Many (1:N) — the Default Pattern

Most relationships in both tutorials are 1:N. The "one" side is the **parent**; the "many" side is the **child**, and the child holds a **foreign key** pointing back to the parent's primary key. From the bookstore tutorial:

```
Author 1───< Book      "One Author writes many Books;
                         each Book has exactly one Author."

Publisher 1───< Book   "One Publisher publishes many Books;
                         each Book has exactly one Publisher."
```

(Note: in running prose and compact diagrams, we often shorten the full crow's-foot symbols to just `1───<`, using a bare `1` for "one, mandatory" and a bare crow's foot `<` for "many" — the detailed four-symbol table in Section 4 is the precise version; this shorthand is what you'll see inline in the tutorial decks.)

## 8. Many-to-Many (M:N) — Needs a Junction Table

A relational database **cannot directly store** a many-to-many relationship — a single foreign-key column can only point to one parent row. So whenever two entities are M:N, we resolve it with an **associative (junction) table** sitting between them, holding two foreign keys:

```
Product ──┤<───────┤<── Supplier

  becomes, in the relational model:

Product 1───< product_suppliers >───1 Supplier
```

`product_suppliers` has its own composite primary key `(product_id, supplier_id)`, and it's also the natural home for any attribute that belongs to the *pairing itself* rather than to either party alone — here, `supply_price` (this supplier's cost for this specific product). This exact pattern appears three times in the e-commerce tutorial: `product_suppliers`, `inventory` (Product ↔ Warehouse), and `order_coupons` (Order ↔ Coupon).

The bookstore tutorial deliberately has **no M:N relationships** — every book has exactly one author and one publisher — specifically so this pattern could be introduced later, in the e-commerce tutorial, without competing for attention against normalization basics.

## 9. When a Relationship Itself Has Data

Look closely at `order_items` in either tutorial. It looks like a junction table, but it exists even though `Order` and `Book`/`Product` aren't really many-to-many in the same automatic sense — it exists because the relationship *"Order contains Book"* carries its own facts: `quantity` and the price *at the time of that sale*. Whenever a relationship needs to record data about the pairing itself, it gets promoted to its own entity, drawn as:

```
Order 1───< OrderItem >───1 Book
```

This is really the same idea as Section 8 (an associative entity in the middle, two foreign keys), just arrived at from a different direction: not because the cardinality forced it, but because the relationship has attributes.

## 10. Self-Referencing Relationships

Sometimes an entity relates to *itself* — the e-commerce tutorial's `categories` table is the example, where a category can have a parent category:

```
Category 1───< Category   (parent / child, via categories.parent_category_id)
```

This is drawn as a loop back to the same box, and implemented as a foreign key column in a table that references that same table's own primary key.

## 11. Quick Reference Card

```
  ONE, mandatory:   ──┤├──   "exactly one"    (shorthand:  1  )
  ONE, optional:    ──○├──   "zero or one"    (shorthand:  0..1 )
  MANY, mandatory:  ──┤<──   "one or more"    (shorthand:  <  , mandatory)
  MANY, optional:   ──○<──   "zero or more"   (shorthand:  ○<  )

  Read each end separately, and each end describes 
  the OTHER entity's multiplicity into this one.

  1:N   → foreign key lives on the "many" side, 
          pointing at the "one" side's PK.
          
  M:N   → cannot be stored directly; needs an 
          associative/junction table with two 
          foreign keys (and, often, its own attributes).
          
  Self- → a foreign key column on a table that references 
          that same table's referencing  own primary key.
```

## 12. Where to See This in Action

The three Week 1 case studies, smallest first. Each has a lecture deck and a DuckDB
Marimo notebook that builds the same schema.

- [`data_modeling_case_study_01_music_catalog/relational_data_modeling_music_catalog.md`](data_modeling_case_study_01_music_catalog/relational_data_modeling_music_catalog.md) — **Case Study 1**: 3 tables, two chained 1:N relationships, one optional participation.

- [`data_modeling_case_study_02_book_store/relational_data_modeling_bookstore.md`](data_modeling_case_study_02_book_store/relational_data_modeling_bookstore.md) — **Case Study 2**: Part 2 ("Conceptual Data Modeling") uses this notation for a 6-table schema of 1:N relationships, including an Order Line entity between Order and Book.

- [`data_modeling_case_study_03_ecommerce/relational_data_modeling_duckdb.md`](data_modeling_case_study_03_ecommerce/relational_data_modeling_duckdb.md) — **Case Study 3**: Part 2 uses the same notation plus worked examples of M:N (Section 8 above) and self-referencing relationships (Section 10 above).

The decks share this notation, so once you can read one, you can read the others.
