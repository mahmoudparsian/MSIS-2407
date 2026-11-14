---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 27px; }
  section.lead h1 { font-size: 2.2em; }
  table { font-size: 0.78em; }
  pre, code { font-size: 0.78em; }
  h1 { color: #1a3e6f; }
  h2 { color: #1a3e6f; }
---

<!-- _class: lead -->

# Relational Data Modeling
## Case Study 1: A Music Catalog — the Smallest Possible Complete Example

MSIS-2407 — Week 1, Data Modeling (Case Study 1 of 3: the warm-up, before the bookstore and e-commerce case studies)

---

# Learning Objectives & Agenda

This is the smallest possible *complete* relational model: 

* **3 tables**, 
* **2 relationships**, 
* no normalization theory, 
* no many-to-many relationships. 

The goal is to nail the core vocabulary — entity, attribute, primary key, foreign key, cardinality, participation — before Case Study 1 (PageTurner Books, 6 tables, adds normalization) and Case Study 2 (e-commerce, 10+ tables, adds many-to-many and self-reference).

---

# Learning Objectives & Agenda (cont.)

**Agenda:** 

1. the business story
2. requirements
3. entities & attributes
4. relationships & ERD
5. the logical schema
6. the physical model in DuckDB
7. sample data and queries
8. summary.

Every SQL statement in this deck was executed, live, against DuckDB 2.0.0.

---

# The Business Story: Harmony Records' Catalog

Harmony Records wants a simple database of the music it catalogs: which **artists** it tracks, which **albums** each artist has released, and which **tracks** are on each album. Nothing about sales, streaming, or pricing yet — just the catalog itself.

**Business Requirements:**

> **R1.** Every artist has a name and a country of origin. An artist can release many albums; a new artist can be added to the catalog before they've released anything.
>
> **R2.** Every album has a title, a release year, and a genre. Every album must belong to exactly one artist — there's no such thing as an album with no artist.
>
> **R3.** Every album contains one or more tracks. Every track belongs to exactly one album — a track can't exist without its album.

---

# The Business Story (cont.)

> **R4.** Each track has a track number (its position on the album, like "track 3") and a title.
>
> **R5.** Each track has a duration in seconds, and a duration can never be zero or negative.
>
> **R6.** Two tracks on the *same* album can never share the same track number — but the same track number (e.g., "track 1") is obviously fine across *different* albums.

**Modeling signal:** 

* R1 → a one-to-many relationship, optional on the artist side (R6's "before they've released anything"). 
* R2/R3 → two more one-to-many relationships, both mandatory on the child side. 
* R5 → a `CHECK` constraint. 
* R6 → a **composite uniqueness rule** that isn't the primary key — a new idea we haven't needed in a single-column-key world.

---

# Step 1 — Entities and Attributes

Three nouns, three entities — this is as simple as noun-extraction gets:

| Entity | Attributes | Source rule(s) |
|---|---|---|
| **Artist** | `artist_id` *(surrogate PK)*, `artist_name`, `country` | R1 |
| **Album** | `album_id` *(surrogate PK)*, `title`, `release_year`, `genre`, *owning artist* | R2 |
| **Track** | `track_id` *(surrogate PK)*, `track_number`, `title`, `duration_seconds`, *owning album* | R3, R4, R5, R6 |

Notice there is **no separate relationship-with-attributes** 
here (unlike `order_items` in the other two case studies) — 
nothing in R1–R6 describes a fact that belongs to a *pairing* 
of two entities rather than to one entity alone. That's part 
of what makes this the simplest possible model: every attribute 
belongs cleanly to exactly one box.

---

# Step 2 — Relationships, Cardinality, and Participation

| Relationship | Cardinality | Participation | Rule |
|---|---|---|---|
| Artist **releases** Album | 1 : N | Artist optional, Album mandatory | R1, R2 |
| Album **contains** Track | 1 : N | Album mandatory, Track mandatory | R2, R3 |

Both relationships are plain one-to-many, chained one after another: `Artist → Album → Track`. There is no many-to-many anywhere in this model (an album has exactly one artist — real-world collaborations/compilations would need M:N, which is exactly what Case Study 2 introduces).

**ERD** (crow's-foot shorthand — see `ERD_Notation_Guide.md` for the full symbol legend):

```
Artist 1───< Album 1───< Track
```

---

# Step 3 — The Logical Schema

| Table | Purpose | Primary Key | Notable constraint |
|---|---|---|---|
| `artists` | who made the music | `artist_id` | — |
| `albums` | releases | `album_id` | `artist_id` mandatory FK |
| `tracks` | songs on an album | `track_id` | `album_id` mandatory FK; `UNIQUE(album_id, track_number)` |

**Keys, formally:** `track_id` is the **primary key** (surrogate — internal, meaningless, stable). `(album_id, track_number)` is a **candidate key** we did *not* choose as PK, but still protect with a `UNIQUE` constraint — this directly implements R6. It's a good first example of a candidate key that is neither the primary key nor a single natural column, but a *composite pair spanning a foreign key and an ordinary attribute*.

**Referential integrity:** 

`albums.artist_id → artists.artist_id`, <br>
`tracks.album_id → albums.album_id`. 

Both mandatory (`NOT NULL`) — no orphan albums, no orphan tracks (R2, R3).

---

# Step 4 — Physical DDL in DuckDB

```sql
CREATE TABLE artists (
    artist_id   INTEGER PRIMARY KEY,
    artist_name VARCHAR NOT NULL,
    country     VARCHAR
);

CREATE TABLE albums (
    album_id      INTEGER PRIMARY KEY,
    artist_id     INTEGER NOT NULL REFERENCES artists(artist_id),  -- R2
    title         VARCHAR NOT NULL,
    release_year  INTEGER,
    genre         VARCHAR
);

CREATE TABLE tracks (
    track_id          INTEGER PRIMARY KEY,
    album_id          INTEGER NOT NULL REFERENCES albums(album_id),        -- R3
    track_number      INTEGER NOT NULL CHECK (track_number > 0),
    title             VARCHAR NOT NULL,
    duration_seconds  INTEGER NOT NULL CHECK (duration_seconds > 0),       -- R5
    UNIQUE (album_id, track_number)                                       -- R6
);
```

---

# Step 4 — Physical DDL in DuckDB (cont.)

Executed against DuckDB 2.0.0 with zero errors — no sequences or `ENUM` types needed here (contrast with the other two case studies), because this model has no controlled-vocabulary attribute and our sample data is small enough to assign IDs by hand.

---

# Proving the Constraints Fire

```sql
INSERT INTO tracks (track_id, album_id, track_number, title, duration_seconds)
VALUES (99, 1, 1, 'Duplicate Track 1', 200);
-- ConstraintException: Duplicate key "album_id: 1, track_number: 1" violates unique constraint

INSERT INTO albums (album_id, artist_id, title) VALUES (99, 999, 'Orphan Album');
-- ConstraintException: Violates foreign key constraint ("artist_id: 999" does not exist)

INSERT INTO tracks (track_id, album_id, track_number, title, duration_seconds)
VALUES (98, 1, 4, 'Bad Duration', -5);
-- ConstraintException: CHECK constraint failed: CHECK((duration_seconds > 0))
```

All three tested live. Notice the **first** error is the new one in this case study — it's not a foreign key or a `CHECK`, it's the composite `UNIQUE (album_id, track_number)` catching R6's business rule directly.

---

# Sample Data

We loaded 4 artists, 4 albums, and 12 tracks (3 per album). **Fontaines D.C.** was added with **zero albums**, deliberately, to exercise the "Artist optional participation" rule from Step 2 — the same pattern as Tom Becker (bookstore) and Emma Chen (e-commerce): every case study includes one row that participates in *no* relationship instance, so students can see optional participation return real, empty results rather than just reading about it.

```
artists 4    
albums 4    
tracks 12
```

Every row satisfied every constraint on the first attempt.

---

# Query 1 & 2 — Albums by Artist, Tracklist for an Album

```sql
SELECT a.artist_name, al.title, al.release_year
FROM artists a JOIN albums al ON al.artist_id = a.artist_id
ORDER BY a.artist_name, al.release_year;
```
```
 artist_name |       title        | release_year
     BTS     | Map of the Soul: 7 |    2020
   Beyoncé   |     Renaissance    |    2022
  Radiohead  |     OK Computer    |    1997
  Radiohead  |     In Rainbows    |    2007
```

---

# Query 1 & 2 — Albums by Artist, Tracklist for an Album (cont.)

```sql
SELECT al.title AS album, 
       t.track_number, 
       t.title AS track, 
       t.duration_seconds
FROM tracks t 
JOIN albums al ON al.album_id = t.album_id
WHERE al.title = 'OK Computer' 
ORDER BY t.track_number;
```
```
    album     | track_number |          track            | duration_seconds
 OK Computer  |      1       |          Airbag            |       284
 OK Computer  |      2       |     Paranoid Android        |       383
 OK Computer  |      3       | Exit Music (For a Film)     |       264
```

---

# Query 3 — Total Duration per Album (Aggregation)

```sql
SELECT al.title, 
       COUNT(*) AS num_tracks, 
       SUM(t.duration_seconds) AS total_seconds,
       ROUND(SUM(t.duration_seconds)/60.0, 1) AS total_minutes
FROM albums al 
JOIN tracks t ON t.album_id = al.album_id
GROUP BY al.title 
ORDER BY total_seconds DESC;
```
```
        title        | num_tracks | total_seconds | total_minutes
    OK Computer      |     3      |     931       |     15.5
    In Rainbows      |     3      |     735       |     12.3
 Map of the Soul: 7  |     3      |     651       |     10.9
    Renaissance      |     3      |     557       |      9.3
```

Just like `order_totals` in the other two case studies, 
this total is **derived**, never stored — a direct benefit 
of keeping `tracks` separate from `albums`.

---

# Query 4 & 5 — Albums per Artist, Artists With No Albums Yet

```sql
SELECT a.artist_name, 
       COUNT(al.album_id) AS num_albums
FROM artists a 
LEFT JOIN albums al ON al.artist_id = a.artist_id
GROUP BY a.artist_name 
ORDER BY num_albums DESC;
```
```
  artist_name     | num_albums
   Radiohead      |     2
      BTS         |     1
    Beyoncé       |     1
 Fontaines D.C.   |     0
```

```sql
SELECT a.artist_name 
FROM artists a
LEFT JOIN albums al ON al.artist_id = a.artist_id 
WHERE al.album_id IS NULL;
```
```
  artist_name
 Fontaines D.C.
```

`LEFT JOIN` + `COUNT` correctly reports **zero**, 
not a missing row, for an artist with no albums — 
this is why we use `LEFT JOIN` (not `JOIN`) whenever 
a relationship is optional and we still want every 
parent row represented.

---

# Query 6 — Longest Track per Album (Subquery)

```sql
SELECT al.title, 
       t.title AS longest_track, 
       t.duration_seconds
FROM tracks t 
JOIN albums al ON al.album_id = t.album_id
WHERE (t.album_id, t.duration_seconds) IN (
    SELECT album_id, 
           MAX(duration_seconds) 
    FROM tracks 
    GROUP BY album_id
)
ORDER BY al.title;
```
```
        title        |   longest_track   | duration_seconds
    In Rainbows      |        Nude       |       255
 Map of the Soul: 7  |         ON        |       247
    OK Computer      |  Paranoid Android |       383
    Renaissance      |        Cozy       |       196
```

---

# Query 6 — Longest Track per Album (Subquery) (cont.)

A row-value subquery (`(album_id, duration_seconds) IN (...)`) — 
a small taste of what's ahead once schemas grow past three tables.

---

# Summary: What This Case Study Established

- **Entity, attribute, primary key, foreign key, cardinality, participation** — the six terms every later case study builds on — all appeared here in their simplest possible form.
- **A candidate key doesn't have to be the primary key, or a single column** — `UNIQUE(album_id, track_number)` was our first composite alternate key.
- **`LEFT JOIN` reveals optional participation**; `JOIN` alone would have silently hidden Fontaines D.C. entirely.
- **What's deliberately *not* here:** normalization theory (anomalies, 1NF/2NF/3NF — coming in Case Study 1), many-to-many relationships and associative entities, self-referencing hierarchies, and controlled-vocabulary `ENUM` types (both coming in Case Study 2).

---

# Summary: What This Case Study Established (cont.)

**Exercise:** Harmony Records now wants to track which **musicians played on which tracks** (a drummer might appear on tracks across several albums; a track usually has several musicians). What kind of relationship is this, and what new table does it require? *(This is a preview of Case Study 2's core idea.)*

---

<!-- _class: lead -->

# Questions?
