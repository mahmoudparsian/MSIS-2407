---
marp: true
title: MSIS-2407 — Week 1 (Part 3) — Structured, Semi-Structured, and Unstructured Data
subtitle: Managing every shape of business data
paginate: true
style: |
  section {
    justify-content: flex-start;
    font-size: 24px;
  }
  h2 {
    background: linear-gradient(90deg, #2c3e50, #4ca1af);
    color: white;
    padding: 10px 18px;
    border-radius: 6px;
    width: fit-content;
  }
  pre { font-size: 18px; }
  table { font-size: 20px; }
---

# 🧭 Structured, Semi-Structured, and Unstructured Data
## MSIS-2407 — Week 1 (Part 3)

### Managing every shape of business data — from the basics to the design decisions

> **Catalog alignment.** The MSIS-2407 description names *"structured and
> unstructured data management"* as a course topic. Part 2 (`data_modeling_02_explained.md`)
> introduced the three categories; this part is the full treatment.

---

# 🎯 Learning Objectives

**Basics** — by the end you can:

- Explain what *data management* covers, beyond storing data
- Place any data source on the structured ↔ unstructured spectrum, and say why
- Match each shape of data to the kinds of systems that store and query it

**Intermediate** — you can also:

- Detect and handle **schema drift** in semi-structured data with SQL
- Choose between **shredding**, **JSON + promoted columns**, and **EAV** — and defend the choice
- Turn unstructured text into **structured facts with provenance**
- Explain how **keyword search** (inverted index, TF-IDF/BM25) and **semantic search**
  (embeddings, cosine similarity) work, and when each fits
- Govern data you cannot query: metadata, retention, legal hold, PII in free text

---

# 🗺 Roadmap

| Part | Level | Topics | When |
|---|---|---|---|
| **A** | Basics | data management · the spectrum · formats · where each shape lives · the running case | **Session 1**, in class |
| **B** | Intermediate — semi-structured | schema drift · profiling with SQL · shredding · nested arrays · design patterns · the EAV trap | **Session 8**, with the document model |
| **C** | Intermediate — unstructured | metadata & retention · extraction with provenance · keyword search · semantic search · PII in text | optional reading |
| **D** | Putting it together | governance across the spectrum · a decision framework · common mistakes | optional reading |

Every query in this deck was run in **DuckDB 2.0.0**; the outputs shown are real.
The companion notebook `data_modeling_03_demo_marimo.py` runs all of them.

---

# Part A — The Basics

---

# 🏢 What "Data Management" Means

Storing data is the easy part. **Data management** is everything an organization
does to make data *usable, trustworthy, and safe* across its whole life:

```text
create / capture → store → integrate → use & share → archive → delete
        ↑                                                       │
        └───────────── governed, secured, quality-checked ──────┘
```

The DAMA *Data Management Body of Knowledge* (DMBOK) organizes it into eleven
knowledge areas, including **data governance**, **data modeling & design**,
**data storage & operations**, **data security**, **data quality**, **metadata**,
**data warehousing & BI** — and one aimed squarely at this topic:
**document and content management** (the unstructured side).

This course touches all of them. Today's question: *how does the shape of the
data change what managing it means?*

---

# 🧭 Recap: The Spectrum (from Part 2)

| | Structured | Semi-structured | Unstructured |
|---|---|---|---|
| **Schema** | fixed before writing | travels with each record | none |
| **Enforced** | on write | on read (if at all) | never — only metadata |
| **Query with** | SQL | SQL + path expressions | search, extraction, ML |

The deciding question is not the file type — it is **when you commit to a
schema** (schema-on-write vs schema-on-read).

Think of it as a **spectrum**, not three boxes: a CSV with a stable header is
structured; a CSV whose columns change every month is drifting toward
semi-structured; a PDF *form* with labelled fields sits closer to semi-structured
than a scanned handwritten letter does.

---

# 📄 Formats Along the Spectrum

<style scoped>table { font-size: 16px; }</style>

| Format | Where it sits | Schema lives… | Notes |
|---|---|---|---|
| Relational table | structured | in the database catalog | enforced on every write |
| CSV | structured (usually) | in a header row + your head | no types, no enforcement |
| **Parquet** | structured, nesting allowed | in the file footer, typed | columnar; the lakehouse workhorse |
| **Avro** | structured / semi | in the file header | built for schema evolution in streams |
| **JSON / JSONL** | semi-structured | per record, implicit | the API and event lingua franca |
| XML | semi-structured | per record (+ optional XSD) | still common in finance, healthcare, government |
| Logs | semi → unstructured | a format string, if you're lucky | |
| Email, PDF, Office docs | unstructured (with metadata) | — | some PDFs contain form fields |
| Images, audio, video | unstructured | — | metadata (EXIF, duration) is structured |

---

# 🏗 Where Each Shape Lives

<style scoped>table { font-size: 15px; } p { font-size: 20px; }</style>

| Store | Data shape | Query model | Good at | Poor at |
|---|---|---|---|---|
| **Relational** (MySQL, PostgreSQL, DuckDB) | tables | SQL | integrity, joins, ad-hoc analysis | rapidly changing shapes |
| **Document** (MongoDB, Couchbase) | JSON documents | path queries | evolving records read whole | cross-document integrity |
| **Key-value** (Redis, DynamoDB) | opaque value per key | get / put | very fast lookups | anything but the key |
| **Wide-column** (Cassandra, Bigtable) | sparse rows | key + range | huge write volume | joins, ad-hoc queries |
| **Graph** (Neo4j) | nodes + edges | traversals | relationships many hops deep | aggregation over everything |
| **Search index** (Elasticsearch, OpenSearch) | text + fields | relevance ranking | "find documents about X" | exact accounting |
| **Object store / data lake** (S3, ADLS) | any file | engines on top (DuckDB, Spark) | cheap storage of everything | nothing by itself |
| **Vector index** (pgvector, Pinecone) | embeddings | nearest neighbour | "find things *like* this" | exact matches, totals |

Modern relational engines blur the lines: **DuckDB and PostgreSQL store JSON,
lists, and structs natively**, and can add text search and vector similarity.

---

# 🚗 The Running Case: Harborview Mutual

An auto insurer. One claim produces all three shapes of data:

| Data | Shape | Source |
|---|---|---|
| `claim` — policy, loss date, status, reserve | **structured** | core claims system |
| `app_event` — uploads, crash reports, status checks | **semi-structured** JSON | the mobile app, two versions in the field |
| `adjuster_note` — what the adjuster wrote | **unstructured** text | typed by people |
| photos, police reports, letters | **unstructured** files | object storage |

```sql
CREATE TABLE claim (
    claim_id      INTEGER PRIMARY KEY,
    policy_id     VARCHAR NOT NULL,
    loss_date     DATE    NOT NULL,
    status        VARCHAR NOT NULL CHECK (status IN ('open','closed','denied')),
    reserve_cents BIGINT  NOT NULL CHECK (reserve_cents >= 0)
);
CREATE TABLE app_event     (event_id INTEGER PRIMARY KEY, payload JSON NOT NULL);
CREATE TABLE adjuster_note (note_id  INTEGER PRIMARY KEY,
                            claim_id INTEGER NOT NULL REFERENCES claim(claim_id),
                            body     VARCHAR NOT NULL);
```

---

# 🚗 Two App Versions, One Table

Version 1 of the app sends:

```json
{"v":1, "claim_id":101, "type":"photo_upload", "ts":"2026-01-04T10:02:00Z",
 "device":{"os":"iOS", "app":"3.2"},
 "photos":[{"file":"101-a.jpg","kb":812}, {"file":"101-b.jpg","kb":774}]}
```

Version 2 adds location and speed — and renames a field:

```json
{"v":2, "claim_id":103, "type":"crash_report", "ts":"2026-01-09T17:21:00Z",
 "device":{"os":"iOS", "app_version":"4.0"},
 "geo":{"lat":37.35, "lon":-121.94}, "speed_kph":62}
```

…and one Android build sends `"speed_kph":"48"` — **a string**.

Nothing rejected any of this. The `JSON` column accepted all eight events.

---

# Part B — Semi-Structured Data, In Depth

---

# 🌊 Schema Drift: Four Ways a Shape Changes

| Change | Example | What breaks — silently |
|---|---|---|
| **Field added** | `geo` appears in v2 | nothing, until someone assumes it is always there |
| **Field removed** | `photos` only on uploads | queries return `NULL`, not an error |
| **Field renamed** | `device.app` → `device.app_version` | every query on the old name now misses half the data |
| **Type changed** | `speed_kph`: `62` vs `"48"` | numeric comparisons, sums, and casts misbehave |

Structured storage turns each of these into a **loud failure at write time**.
Semi-structured storage turns them into **quiet wrong answers at read time** —
which is why profiling the data is the first job.

---

# 🔎 Profiling Drift with SQL

How many different shapes are there? `json_structure` infers each document's schema:

```sql
SELECT count(*) AS events,
       count(DISTINCT json_structure(payload)) AS distinct_shapes
FROM app_event;
```
```text
 events │ distinct_shapes
      8 │               7
```

Eight events, **seven** shapes. Which top-level keys does each version use?

```sql
SELECT payload->>'$.v' AS v,
       list_sort(list_distinct(flatten(list(json_keys(payload))))) AS keys_seen
FROM app_event GROUP BY v ORDER BY v;
```
```text
 v │ keys_seen
 1 │ [claim_id, device, photos, ts, type, v]
 2 │ [claim_id, device, geo, photos, speed_kph, ts, type, v]
```

---

# 🔁 Handling a Renamed Field

```sql
SELECT event_id,
       payload->>'$.device.app'         AS app_v1,
       payload->>'$.device.app_version' AS app_v2,
       coalesce(payload->>'$.device.app_version',
                payload->>'$.device.app') AS app_version
FROM app_event ORDER BY event_id;
```
```text
 event_id │ app_v1 │ app_v2 │ app_version
        1 │ 3.2    │ NULL   │ 3.2
        3 │ 3.2    │ NULL   │ 3.2
        4 │ NULL   │ 4.0    │ 4.0
        6 │ NULL   │ 4.0.1  │ 4.0.1
      …   (8 rows)
```

Querying only `$.device.app` would have returned `NULL` for every v2 event —
**no error, just a wrong answer**. `coalesce` reconciles the two names in one place.

---

# 🔢 Handling a Changed Type

```sql
SELECT event_id,
       payload->'$.speed_kph'               AS raw,
       json_type(payload, '$.speed_kph')    AS json_type
FROM app_event
WHERE payload->>'$.type' = 'crash_report'
ORDER BY event_id;
```
```text
 event_id │ raw  │ json_type
        4 │ 62   │ UBIGINT
        6 │ "48" │ VARCHAR
        8 │ null │ NULL
```

Three crash reports, three different situations: a number, a number *written as
text*, and an explicit `null`. `TRY_CAST(payload->>'$.speed_kph' AS INTEGER)`
turns the first two into `62` and `48` and leaves the third `NULL` — and a data
quality check should **count** how many needed the conversion.

---

# 🧱 Shredding: Semi-Structured → Relational

**Shredding** extracts the fields you rely on into typed columns, once:

```sql
CREATE TABLE event_flat AS
SELECT event_id,
       CAST(payload->>'$.claim_id' AS INTEGER)       AS claim_id,
       payload->>'$.type'                            AS event_type,
       CAST(payload->>'$.ts' AS TIMESTAMP)           AS event_ts,
       payload->>'$.device.os'                       AS os,
       coalesce(payload->>'$.device.app_version',
                payload->>'$.device.app')            AS app_version,
       TRY_CAST(payload->>'$.speed_kph' AS INTEGER)  AS speed_kph,
       CAST(payload->>'$.geo.lat' AS DOUBLE)         AS lat,
       CAST(payload->>'$.geo.lon' AS DOUBLE)         AS lon
FROM app_event;
```
```text
-- the three crash reports (first seven columns):
 event_id │ claim_id │ event_type   │ event_ts            │ os      │ app_version │ speed_kph
        4 │      103 │ crash_report │ 2026-01-09 17:21:00 │ iOS     │ 4.0         │        62
        6 │      105 │ crash_report │ 2026-01-21 07:55:00 │ Android │ 4.0.1       │        48
        8 │      104 │ crash_report │ 2026-01-15 12:10:00 │ iOS     │ 4.0         │      NULL
```

All the drift handling now lives in **one** statement, instead of in every analyst's query.

---

# 📸 Nested Arrays Are Hidden Entities

<style scoped>pre { font-size: 15px; } section { font-size: 21px; }</style>

`photos` is a list *inside* a document — a one-to-many relationship in disguise.
`UNNEST` turns it into rows:

```sql
SELECT e.event_id,
       CAST(e.payload->>'$.claim_id' AS INTEGER) AS claim_id,
       p.photo.file AS file, p.photo.kb AS kb
FROM app_event e,
     unnest(from_json(e.payload->'$.photos',
                      '[{"file":"VARCHAR","kb":"INTEGER"}]')) AS p(photo)
ORDER BY e.event_id, file;
```
```text
 event_id │ claim_id │ file      │   kb
        1 │      101 │ 101-a.jpg │  812
        1 │      101 │ 101-b.jpg │  774
        3 │      102 │ 102-a.jpg │ 1030
        5 │      103 │ 103-a.jpg │ 2048
        5 │      103 │ 103-b.jpg │ 1987
        5 │      103 │ 103-c.jpg │ 2210
```

In ER terms: **Photo** is an entity with its own attributes, related 1:M to the
event. Shredding a nested array *is* data modeling (Part 2) applied after the fact.

---

# 🧩 Four Design Patterns for Semi-Structured Data

<style scoped>table { font-size: 16px; }</style>

| Pattern | What you store | Integrity | Query effort | Absorbs new fields? |
|---|---|---|---|---|
| **1. Shred fully** | only typed columns | high — constraints apply | low | no — every change is a migration |
| **2. JSON + promoted columns** | the document **and** typed columns for contractual fields | high on promoted fields | low on promoted, medium elsewhere | yes |
| **3. EAV** (entity–attribute–value) | one row per (entity, attribute, value) | **very low** | high | yes — at a steep price |
| **4. Raw in a lake, modeled downstream** | files as received | none at landing | depends on the layer | yes — bronze → silver → gold (Week 4) |

Pattern 2 is the usual answer for operational systems today: keep the full
document for flexibility, and **promote** the few fields that contracts,
reports, and joins depend on.

---

# ⬆️ Pattern 2: Promoted (Generated) Columns

```sql
CREATE TABLE app_event_v2 (
    event_id   INTEGER PRIMARY KEY,
    payload    JSON NOT NULL,
    claim_id   INTEGER GENERATED ALWAYS AS (CAST(payload->>'$.claim_id' AS INTEGER)) VIRTUAL,
    event_type VARCHAR GENERATED ALWAYS AS (payload->>'$.type') VIRTUAL
);
INSERT INTO app_event_v2 (event_id, payload) SELECT event_id, payload FROM app_event;

SELECT event_type, count(*) AS n FROM app_event_v2
GROUP BY event_type ORDER BY n DESC, event_type;
```
```text
 event_type   │ n
 crash_report │ 3
 photo_upload │ 3
 status_check │ 2
```

The promoted columns are **declared in the schema**: they have a type, a name
every consumer shares, and they can't drift from the document they come from.

---

# ⚠️ Pattern 3: The EAV Trap

<style scoped>pre { font-size: 15px; } section { font-size: 21px; }</style>

EAV looks infinitely flexible — any attribute, no migrations:

```sql
CREATE TABLE claim_attr (claim_id INTEGER, attr VARCHAR, value VARCHAR);
-- (101,'tow_required','true'), (103,'tow_required','yes'), (105,'tow_required','true'),
-- (103,'rental_days','7'),     (105,'rental_days','seven'), (101,'repair_shop','Bay Auto')

SELECT attr, list(value ORDER BY claim_id) AS values_seen
FROM claim_attr GROUP BY attr ORDER BY attr;
```
```text
 attr         │ values_seen
 rental_days  │ [7, seven]
 repair_shop  │ [Bay Auto]
 tow_required │ [true, yes, true]
```

Everything is a string, so nothing stops `'yes'` vs `'true'` or `'seven'` vs `7`.
Pivoting back to columns needs one aggregate per attribute, and `TRY_CAST`
quietly turns `'seven'` into `NULL`. No types, no `CHECK`, no foreign keys.

**Use EAV only** for genuinely sparse, user-defined attributes — and even then,
prefer a JSON column (pattern 2), which at least keeps types per value.

---

# Part C — Unstructured Data, In Depth

---

# 🗄 Managing What You Cannot Query

You cannot `SELECT` the contents of a photo. You **can** model everything about it:

```sql
CREATE TABLE stored_object (
    object_uri   VARCHAR PRIMARY KEY,               -- where the bytes live
    claim_id     INTEGER NOT NULL REFERENCES claim(claim_id),
    media_type   VARCHAR NOT NULL,
    bytes        BIGINT  NOT NULL CHECK (bytes > 0),
    sha256       VARCHAR NOT NULL,                  -- has it changed? is it a duplicate?
    contains_pii BOOLEAN NOT NULL,                  -- classification
    retain_until DATE    NOT NULL,                  -- retention schedule
    legal_hold   BOOLEAN NOT NULL DEFAULT false     -- litigation overrides retention
);
```

---

# 🗄 Retention vs. Legal Hold

Which files may be deleted at the end of 2026?

```sql
SELECT object_uri, retain_until, legal_hold
FROM stored_object
WHERE retain_until <= DATE '2026-12-31' AND NOT legal_hold;
```
```text
 object_uri                           │ retain_until │ legal_hold
 s3://hm-claims/102/102-a.jpg         │ 2026-12-31   │ false
 s3://hm-claims/104/denial_letter.pdf │ 2026-12-31   │ false
```

Claim 103's police report reached its retention date too (`2026-06-30`) — but
it is on **legal hold** (the claim is in litigation), so the query skips it. This metadata table is structured,
constrained, and auditable even though the files are not.

---

# 🛠 From Text to Facts: Extraction with Provenance

The adjuster notes hold facts the business needs — *airbags deployed? injury
mentioned?* — but as prose. An **extraction pipeline** turns prose into rows:

```text
source text → extract (rules, NLP, OCR, an LLM) → validate → structured facts → human review
```

The rule that separates a professional pipeline from a fragile one:
**every extracted fact carries its provenance.**

| Column | Why it is there |
|---|---|
| `note_id` | which document the fact came from |
| `fact` | what was extracted |
| `method` | how — keyword rule, model name and version… |
| `confidence` | how sure — so low-confidence facts go to a person |
| `span_start` | where in the text — so a reviewer can check it in seconds |

---

# 🛠 Extraction, Run on the Notes

```sql
CREATE TABLE extracted_fact AS
SELECT note_id, 'injury_mentioned' AS fact, 'keyword' AS method, 0.6 AS confidence,
       instr(lower(body), 'whiplash') AS span_start
FROM adjuster_note WHERE lower(body) LIKE '%whiplash%' OR lower(body) LIKE '%neck pain%'
UNION ALL
SELECT note_id, 'airbag_deployed', 'keyword', 0.9, instr(lower(body), 'airbag')
FROM adjuster_note WHERE regexp_matches(lower(body), 'airbags? deployed');
```
```text
 note_id │ fact             │ method  │ confidence │ span_start
       3 │ airbag_deployed  │ keyword │        0.9 │         25
       3 │ injury_mentioned │ keyword │        0.6 │         78
       5 │ airbag_deployed  │ keyword │        0.9 │         30
```

Note 3's injury fact has confidence 0.6 — a keyword rule cannot tell
*"possible whiplash"* from *"no whiplash"*, so it goes to a person.

---

# 🔗 Facts Joined Back to Claims

Joined back to `claim`, the unstructured notes now answer a structured question:

```sql
SELECT c.claim_id, c.status, c.reserve_cents,
       bool_or(f.fact = 'airbag_deployed')  AS airbag,
       bool_or(f.fact = 'injury_mentioned') AS injury
FROM claim c JOIN adjuster_note n USING (claim_id) JOIN extracted_fact f USING (note_id)
GROUP BY ALL ORDER BY c.claim_id;
```
```text
 claim_id │ status │ reserve_cents │ airbag │ injury
      103 │ open   │        980000 │ true   │ true
      105 │ open   │        275000 │ true   │ false
```

---

# 🔍 Keyword Search: The Inverted Index

<style scoped>pre { font-size: 15px; } section { font-size: 21px; }</style>

Search engines don't scan every document. They build an **inverted index**:
for each term, the list of documents containing it (its *postings*).

```sql
CREATE TABLE note_term AS
SELECT note_id, term, count(*) AS tf          -- tf = term frequency in that note
FROM (SELECT note_id, unnest(regexp_extract_all(lower(body), '[a-z]+')) AS term
      FROM adjuster_note)
GROUP BY ALL;

SELECT term, list(note_id ORDER BY note_id) AS postings
FROM note_term
WHERE term IN ('crushed', 'airbag', 'airbags', 'deployed', 'whiplash')
GROUP BY term ORDER BY term;
```
```text
 term     │ postings
 airbag   │ [5]
 airbags  │ [3]
 crushed  │ [1, 3, 5]
 deployed │ [3, 5]
 whiplash │ [3]
```

Notice `airbag` and `airbags` are **different terms** — remember that.

---

# 📊 Ranking: TF-IDF

Not every match is equally good. **TF-IDF** scores a document higher when a query
term appears often *in it* (term frequency) and rarely *elsewhere* (inverse
document frequency, `ln(N / df)`):

```sql
WITH n  AS (SELECT count(*) AS docs FROM adjuster_note),
     df AS (SELECT term, count(*) AS df FROM note_term GROUP BY term)
SELECT t.note_id, round(sum(t.tf * ln(n.docs / df.df)), 3) AS score
FROM note_term t JOIN df USING (term), n
WHERE t.term IN ('crushed', 'airbag')
GROUP BY t.note_id ORDER BY score DESC, t.note_id;
```
```text
 note_id │ score
       5 │ 2.12      -- 'airbag' is rare (1 of 5 notes) → weighs a lot
       1 │ 0.511     -- 'crushed' is common (3 of 5) → weighs little
       3 │ 0.511     -- …and its 'airbags' doesn't count as 'airbag'
```

Note 3 — both airbags deployed — ranks no better than a crushed bumper.
The fix is **stemming**: reducing *airbags* to *airbag* before indexing.

---

# 📊 Production Ranking: BM25 with Stemming

DuckDB's `fts` extension builds a real inverted index with stemming and ranks
with **BM25**, the refinement of TF-IDF used by most search engines:

```sql
INSTALL fts; LOAD fts;                 -- one-time download (needs internet)
PRAGMA create_fts_index('adjuster_note', 'note_id', 'body');

SELECT note_id, score
FROM (SELECT note_id,
             round(fts_main_adjuster_note.match_bm25(note_id, 'crushed airbag'), 3) AS score
      FROM adjuster_note)
WHERE score IS NOT NULL ORDER BY score DESC;
```
```text
 note_id │ score
       5 │ 0.62
       3 │ 0.506     -- now found through 'airbags' → 'airbag'
       1 │ 0.247
```

With stemming, note 3 overtakes the bumper note. Keyword search is still
**literal**, though: a note saying *"the SRS module fired"* would not match at all.

---

# 🧠 Semantic Search: Embeddings and Similarity

An **embedding model** turns text into a vector of numbers so that texts with
similar *meaning* get nearby vectors. Similarity is usually **cosine similarity**
(1 = same direction, 0 = unrelated).

```sql
-- toy 4-dimensional vectors for illustration — real embeddings have hundreds
-- to thousands of dimensions and come from a model
CREATE TABLE note_vec (note_id INTEGER PRIMARY KEY, v FLOAT[4]);
SELECT note_id,
       round(array_cosine_similarity(v, [0.8, 0.9, 0.0, 0.0]::FLOAT[4]), 3) AS similarity
FROM note_vec ORDER BY similarity DESC;
```
```text
 note_id │ similarity
       5 │ 0.991
       3 │ 0.864
       1 │ 0.738
       2 │ 0.144
       4 │ 0.0
```

Notes 5 and 3 (airbags, crushed fronts) sit closest to the query vector; the
paperwork notes 2 and 4 are far away.

---

# ⚖️ Keyword vs. Semantic Search

| | Keyword (BM25) | Semantic (vectors) |
|---|---|---|
| Matches | the words you typed | the meaning, even with other words |
| Explainable | yes — which terms matched | hardly — a distance |
| Good for | IDs, names, exact phrases, legal search | "find claims *like* this one" |

Most production systems combine both (**hybrid search**).

---

# 🔐 PII Hiding in Free Text

Structured columns can be classified once (Session 9). Free text can contain
**anything** — phone numbers, emails, health details — typed by people:

```sql
SELECT note_id,
       regexp_extract_all(body, '\d{3}-\d{3}-\d{4}')              AS phones,
       regexp_extract_all(body, '[\w.+-]+@[\w-]+(?:\.[\w-]+)+')   AS emails
FROM adjuster_note
WHERE regexp_matches(body, '\d{3}-\d{3}-\d{4}|[\w.+-]+@[\w-]+\.[\w-]+');
```
```text
 note_id │ phones         │ emails
       1 │ [408-555-0142] │ []
       3 │ []             │ [j.ortiz@mailbox.com]
       5 │ [650-555-0199] │ []
```

⚠️ A first draft used `'[\w.+-]+@[\w-]+\.[\w.]+'` and captured
`j.ortiz@mailbox.com.` — **with the sentence's full stop**. Redaction with that
pattern swallowed the period too. Test detection patterns on real text.

---

# 🔐 Redaction — and Its Limits

```sql
SELECT regexp_replace(body, '[\w.+-]+@[\w-]+(?:\.[\w-]+)+', '[EMAIL]', 'g') AS body_redacted
FROM adjuster_note WHERE note_id = 3;
```
```text
Front end crushed, both airbags deployed. Driver reports neck pain,
possible whiplash. Email photos to [EMAIL].
```

The email is gone — but *"neck pain, possible whiplash"* is **health information**
about an identifiable claimant, and no pattern caught it. Regular expressions
find things with a fixed shape (phones, emails, card numbers). Names, health
conditions, and addresses need **named-entity recognition** or a trained
classifier — and a person reviewing what they miss.

**Design consequence:** treat every free-text column as *potentially*
containing restricted data, and restrict access to the column, not just to
the fields you know about.

---

# Part D — Putting It Together

---

# 🛡 Governance Across the Spectrum

| Concern | Structured | Semi-structured | Unstructured |
|---|---|---|---|
| **Integrity** | constraints on write | promoted columns + validation on load | checksums on the object |
| **Quality** | rules as SQL (Session 10) | drift profiling + rules on shredded fields | extraction confidence + human review |
| **Security** | column-level views (Session 9) | views over shredded/promoted fields | access to the object + PII scanning |
| **Retention** | per table / per row | per table / per record | per object, with legal hold |
| **Lineage** | query logs, ETL metadata | source version (`v`) kept in the record | provenance on every extracted fact |
| **Catalog entry** | table + columns | table + contractual paths | object type + classification + owner |

The pattern: the **less structure the data has, the more structured its
metadata must be**.

---

# 🧭 A Decision Framework

Ask, in this order:

1. **Who queries it, and how?** Reports and joins → structure it. Whole-record reads by one app → a document is fine. People searching → index it.
2. **How stable is the shape?** Stable → shred. Evolving → JSON + promoted columns. Unknown → land raw, model downstream.
3. **What must never be wrong?** Money, identity, legal status → schema-on-write with constraints, always.
4. **What would it cost to get wrong later?** Deferring the schema is cheap today and expensive in every query after.
5. **What does it contain?** If people typed it, assume it holds personal data until scanned.

**Harborview, decided:** `claim` structured · `app_event` JSON with promoted
`claim_id`, `event_type`, `event_ts`, plus a shredded `event_flat` for analysts ·
notes in a restricted column with BM25 search and an `extracted_fact` table ·
files in object storage, governed through `stored_object`.

---

# 🧪 Three More Scenarios — Your Turn

For each, decide what to structure, what to keep semi-structured, and what
metadata you need for the unstructured parts:

1. **E-commerce clickstream** — 40 event types from web and mobile, a new app
   release every two weeks, marketing wants funnels by day.
2. **HR contracts** — signed PDFs, offer letters, and performance reviews;
   legal must find every contract with a non-compete clause; employees may
   request deletion of their data.
3. **Hospital imaging** — scans (large binary files), radiologist reports (text),
   and appointment records; strict privacy law; research team wants
   "find scans similar to this one".

---

# ❌ Common Mistakes

1. **"It's JSON, so we don't need a model."** You still have entities and
   relationships — you have just postponed finding them.
2. **Querying only the newest field name** after a rename — half the data quietly disappears.
3. **Casting drifted fields with `CAST`** instead of `TRY_CAST` + a count of what failed.
4. **EAV for core business attributes** — no types, no constraints, painful queries.
5. **Treating free text as harmless** — it is the most likely place for unclassified PII.
6. **Storing extracted facts without provenance** — nobody can check or correct them.
7. **Deleting on schedule without checking legal hold.**
8. **Choosing semantic search for exact lookups** — a policy number is not a "meaning".

---

# ✅ Check Your Understanding

1. A vendor's CSV feed adds a column every quarter and occasionally changes a
   column's units. Where is it on the spectrum, and how would you land it?
2. Your app renamed `device.app` to `device.app_version`. Write the expression
   that works for both versions, and say where in the pipeline it should live.
3. Why does a nested `photos` array signal a missing entity? What are its key and its relationship?
4. Give one case where EAV is acceptable and one where it is a design error.
5. TF-IDF ranked note 3 too low. Explain why, and what fixed it.
6. An extracted fact has confidence 0.55. What should happen to it before it
   reaches a report — and which columns let that happen?
7. Retention says delete a file today; it is on legal hold. What wins, and how
   does the metadata model make that decision automatic?

---

# 🙌 Summary

- **Data management** is the whole life of the data — the shape decides how hard each part is.
- The spectrum is about **when the schema is committed**, not about file formats.
- Semi-structured data **drifts**: profile it, reconcile renames and types once,
  shred or promote what you depend on, and avoid EAV for core attributes.
- Unstructured data is managed through **structured metadata**, **extracted facts
  with provenance**, and **search** — keyword (BM25) and semantic (vectors).
- The less structure the data has, **the more structured its metadata must be**.

**Where this goes next:** the shredded `event_flat` and the `photos` entity are
exactly what Week 2 normalizes · Week 4 Part 2 and Session 8's Lab 2b compare
relational, nested, and document models in depth · Week 4's medallion
architecture stages schema commitment · Sessions 9–10 cover classification,
masking, retention, and data-quality rules.
