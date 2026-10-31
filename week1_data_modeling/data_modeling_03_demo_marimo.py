import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 🧭 MSIS-2407 — Week 1 (Part 3) — Demo Notebook
    ## Structured, Semi-Structured, and Unstructured Data

    Companion to `data_modeling_03_structured_semistructured_unstructured.md`. Every
    query from the deck runs here, in the same order, on the **Harborview Mutual**
    auto-claims case — and each cell checks that it still returns the numbers the
    slides quote.

    ```bash
    pip install "marimo[sql]" duckdb pandas
    marimo edit data_modeling_03_demo_marimo.py
    ```

    The full-text-search cell downloads DuckDB's `fts` extension the first time
    (it needs an internet connection once); everything else runs offline.
    """)
    return


@app.cell
def _():
    import duckdb
    import pandas as pd
    pd.set_option("display.width", 175)
    pd.set_option("display.max_colwidth", 120)
    con = duckdb.connect()
    return con, duckdb, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## The case — three shapes of data about the same claims

    `claim` is structured, `app_event` holds JSON from two app versions, and
    `adjuster_note` is free text typed by people.
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE claim (
        claim_id      INTEGER PRIMARY KEY,
        policy_id     VARCHAR NOT NULL,
        loss_date     DATE    NOT NULL,
        status        VARCHAR NOT NULL CHECK (status IN ('open','closed','denied')),
        reserve_cents BIGINT  NOT NULL CHECK (reserve_cents >= 0)
    );
    INSERT INTO claim VALUES
     (101,'POL-2231','2026-01-04','open',   450000),
     (102,'POL-1187','2026-01-06','closed', 120000),
     (103,'POL-3302','2026-01-09','open',   980000),
     (104,'POL-2231','2026-01-15','denied',      0),
     (105,'POL-4410','2026-01-21','open',   275000);

    CREATE TABLE app_event (event_id INTEGER PRIMARY KEY, payload JSON NOT NULL);
    INSERT INTO app_event VALUES
     (1, '{"v":1,"claim_id":101,"type":"photo_upload","ts":"2026-01-04T10:02:00Z","device":{"os":"iOS","app":"3.2"},"photos":[{"file":"101-a.jpg","kb":812},{"file":"101-b.jpg","kb":774}]}'),
     (2, '{"v":1,"claim_id":101,"type":"status_check","ts":"2026-01-05T08:15:00Z","device":{"os":"iOS","app":"3.2"}}'),
     (3, '{"v":1,"claim_id":102,"type":"photo_upload","ts":"2026-01-06T14:40:00Z","device":{"os":"Android","app":"3.2"},"photos":[{"file":"102-a.jpg","kb":1030}]}'),
     (4, '{"v":2,"claim_id":103,"type":"crash_report","ts":"2026-01-09T17:21:00Z","device":{"os":"iOS","app_version":"4.0"},"geo":{"lat":37.35,"lon":-121.94},"speed_kph":62}'),
     (5, '{"v":2,"claim_id":103,"type":"photo_upload","ts":"2026-01-09T17:30:00Z","device":{"os":"iOS","app_version":"4.0"},"geo":{"lat":37.35,"lon":-121.94},"photos":[{"file":"103-a.jpg","kb":2048},{"file":"103-b.jpg","kb":1987},{"file":"103-c.jpg","kb":2210}]}'),
     (6, '{"v":2,"claim_id":105,"type":"crash_report","ts":"2026-01-21T07:55:00Z","device":{"os":"Android","app_version":"4.0.1"},"geo":{"lat":37.77,"lon":-122.42},"speed_kph":"48"}'),
     (7, '{"v":2,"claim_id":105,"type":"status_check","ts":"2026-01-22T09:00:00Z","device":{"os":"Android","app_version":"4.0.1"}}'),
     (8, '{"v":2,"claim_id":104,"type":"crash_report","ts":"2026-01-15T12:10:00Z","device":{"os":"iOS","app_version":"4.0"},"speed_kph":null}');

    CREATE TABLE adjuster_note (note_id INTEGER PRIMARY KEY,
                                claim_id INTEGER NOT NULL REFERENCES claim(claim_id),
                                body VARCHAR NOT NULL);
    INSERT INTO adjuster_note VALUES
     (1, 101, 'Rear bumper crushed, trunk will not close. Insured asked to be called at 408-555-0142.'),
     (2, 102, 'Minor scrape on passenger door. Paid in full, file closed.'),
     (3, 103, 'Front end crushed, both airbags deployed. Driver reports neck pain, possible whiplash. Email photos to j.ortiz@mailbox.com.'),
     (4, 104, 'Policy lapsed before loss date. Claim denied; letter sent.'),
     (5, 105, 'Side impact at intersection, airbag deployed, door crushed. Witness phone 650-555-0199.');
    """)
    con.execute("SELECT * FROM app_event ORDER BY event_id").df()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Part B — Semi-structured data
    ### Profiling drift: how many shapes?
    """)
    return


@app.cell
def _(con):
    shapes = con.execute("""
    SELECT count(*) AS events,
           count(DISTINCT json_structure(payload)) AS distinct_shapes
    FROM app_event
    """).df()
    assert shapes.iloc[0].tolist() == [8, 7]
    shapes
    return


@app.cell
def _(con):
    keys_by_version = con.execute("""
    SELECT payload->>'$.v' AS v,
           list_sort(list_distinct(flatten(list(json_keys(payload))))) AS keys_seen
    FROM app_event GROUP BY v ORDER BY v
    """).df()
    assert list(keys_by_version.iloc[1]["keys_seen"]) == [
        "claim_id", "device", "geo", "photos", "speed_kph", "ts", "type", "v"]
    keys_by_version
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### A renamed field, reconciled with `coalesce`
    """)
    return


@app.cell
def _(con):
    renamed = con.execute("""
    SELECT event_id,
           payload->>'$.device.app'         AS app_v1,
           payload->>'$.device.app_version' AS app_v2,
           coalesce(payload->>'$.device.app_version',
                    payload->>'$.device.app') AS app_version
    FROM app_event ORDER BY event_id
    """).df()
    assert renamed["app_version"].tolist() == ["3.2", "3.2", "3.2", "4.0", "4.0", "4.0.1", "4.0.1", "4.0"]
    renamed
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### A changed type, found with `json_type`
    """)
    return


@app.cell
def _(con):
    type_drift = con.execute("""
    SELECT event_id,
           payload->'$.speed_kph'               AS raw,
           json_type(payload, '$.speed_kph')    AS json_type
    FROM app_event
    WHERE payload->>'$.type' = 'crash_report'
    ORDER BY event_id
    """).df()
    assert type_drift["json_type"].tolist()[:2] == ["UBIGINT", "VARCHAR"]
    type_drift
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Shredding into typed columns
    """)
    return


@app.cell
def _(con, pd):
    con.execute("""
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
    FROM app_event
    """)
    event_flat = con.execute("SELECT * FROM event_flat ORDER BY event_id").df()
    _crash = event_flat[event_flat["event_type"] == "crash_report"]
    assert _crash["speed_kph"].tolist()[:2] == [62, 48] and pd.isna(_crash["speed_kph"].tolist()[2])
    event_flat
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### A nested array is a hidden entity — `UNNEST` it
    """)
    return


@app.cell
def _(con):
    photos = con.execute("""
    SELECT e.event_id,
           CAST(e.payload->>'$.claim_id' AS INTEGER) AS claim_id,
           p.photo.file AS file, p.photo.kb AS kb
    FROM app_event e,
         unnest(from_json(e.payload->'$.photos',
                          '[{"file":"VARCHAR","kb":"INTEGER"}]')) AS p(photo)
    ORDER BY e.event_id, file
    """).df()
    assert len(photos) == 6 and photos["kb"].tolist() == [812, 774, 1030, 2048, 1987, 2210]
    photos
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Pattern 2 — JSON plus promoted (generated) columns
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE app_event_v2 (
        event_id   INTEGER PRIMARY KEY,
        payload    JSON NOT NULL,
        claim_id   INTEGER GENERATED ALWAYS AS (CAST(payload->>'$.claim_id' AS INTEGER)) VIRTUAL,
        event_type VARCHAR GENERATED ALWAYS AS (payload->>'$.type') VIRTUAL
    );
    INSERT INTO app_event_v2 (event_id, payload) SELECT event_id, payload FROM app_event;
    """)
    promoted = con.execute("""
    SELECT event_type, count(*) AS n FROM app_event_v2
    GROUP BY event_type ORDER BY n DESC, event_type
    """).df()
    assert promoted.values.tolist() == [["crash_report", 3], ["photo_upload", 3], ["status_check", 2]]
    promoted
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Pattern 3 — the EAV trap
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE claim_attr (claim_id INTEGER, attr VARCHAR, value VARCHAR);
    INSERT INTO claim_attr VALUES
     (101,'tow_required','true'), (101,'repair_shop','Bay Auto'),
     (103,'tow_required','yes'),  (103,'rental_days','7'),
     (105,'rental_days','seven'), (105,'tow_required','true');
    """)
    eav = con.execute("""
    SELECT attr, list(value ORDER BY claim_id) AS values_seen
    FROM claim_attr GROUP BY attr ORDER BY attr
    """).df()
    assert list(eav.iloc[0]["values_seen"]) == ["7", "seven"]
    assert list(eav.iloc[2]["values_seen"]) == ["true", "yes", "true"]
    eav
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Part C — Unstructured data
    ### Managing what you cannot query: object metadata, retention, legal hold
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE stored_object (
        object_uri   VARCHAR PRIMARY KEY,
        claim_id     INTEGER NOT NULL REFERENCES claim(claim_id),
        media_type   VARCHAR NOT NULL,
        bytes        BIGINT  NOT NULL CHECK (bytes > 0),
        sha256       VARCHAR NOT NULL,
        contains_pii BOOLEAN NOT NULL,
        retain_until DATE    NOT NULL,
        legal_hold   BOOLEAN NOT NULL DEFAULT false
    );
    INSERT INTO stored_object VALUES
     ('s3://hm-claims/101/101-a.jpg',         101, 'image/jpeg',       831488, '9f2c...a1', false, '2033-01-04', false),
     ('s3://hm-claims/102/102-a.jpg',         102, 'image/jpeg',      1054720, '77b0...4e', false, '2026-12-31', false),
     ('s3://hm-claims/103/police_report.pdf', 103, 'application/pdf',  402112, 'c41d...90', true,  '2026-06-30', true),
     ('s3://hm-claims/104/denial_letter.pdf', 104, 'application/pdf',   98304, '0ad3...7c', true,  '2026-12-31', false);
    """)
    due = con.execute("""
    SELECT object_uri, retain_until, legal_hold
    FROM stored_object
    WHERE retain_until <= DATE '2026-12-31' AND NOT legal_hold
    ORDER BY object_uri
    """).df()
    assert due["object_uri"].tolist() == ["s3://hm-claims/102/102-a.jpg",
                                          "s3://hm-claims/104/denial_letter.pdf"]
    due
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### From text to facts — with provenance
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE extracted_fact AS
    SELECT note_id, 'injury_mentioned' AS fact, 'keyword' AS method, 0.6 AS confidence,
           instr(lower(body), 'whiplash') AS span_start
    FROM adjuster_note WHERE lower(body) LIKE '%whiplash%' OR lower(body) LIKE '%neck pain%'
    UNION ALL
    SELECT note_id, 'airbag_deployed', 'keyword', 0.9, instr(lower(body), 'airbag')
    FROM adjuster_note WHERE regexp_matches(lower(body), 'airbags? deployed')
    """)
    facts = con.execute("SELECT * FROM extracted_fact ORDER BY note_id, fact").df()
    assert facts[["note_id", "fact", "span_start"]].values.tolist() == [
        [3, "airbag_deployed", 25], [3, "injury_mentioned", 78], [5, "airbag_deployed", 30]]
    facts
    return


@app.cell
def _(con):
    claim_facts = con.execute("""
    SELECT c.claim_id, c.status, c.reserve_cents,
           bool_or(f.fact = 'airbag_deployed')  AS airbag,
           bool_or(f.fact = 'injury_mentioned') AS injury
    FROM claim c JOIN adjuster_note n USING (claim_id) JOIN extracted_fact f USING (note_id)
    GROUP BY ALL ORDER BY c.claim_id
    """).df()
    assert claim_facts.values.tolist() == [[103, "open", 980000, True, True],
                                           [105, "open", 275000, True, False]]
    claim_facts
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Keyword search — an inverted index built in SQL
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE note_term AS
    SELECT note_id, term, count(*) AS tf
    FROM (SELECT note_id, unnest(regexp_extract_all(lower(body), '[a-z]+')) AS term
          FROM adjuster_note)
    GROUP BY ALL
    """)
    postings = con.execute("""
    SELECT term, list(note_id ORDER BY note_id) AS postings
    FROM note_term
    WHERE term IN ('crushed', 'airbag', 'airbags', 'deployed', 'whiplash')
    GROUP BY term ORDER BY term
    """).df()
    assert [list(p) for p in postings["postings"]] == [[5], [3], [1, 3, 5], [3, 5], [3]]
    postings
    return


@app.cell
def _(con):
    tfidf = con.execute("""
    WITH n  AS (SELECT count(*) AS docs FROM adjuster_note),
         df AS (SELECT term, count(*) AS df FROM note_term GROUP BY term)
    SELECT t.note_id, round(sum(t.tf * ln(n.docs / df.df)), 3) AS score
    FROM note_term t JOIN df USING (term), n
    WHERE t.term IN ('crushed', 'airbag')
    GROUP BY t.note_id ORDER BY score DESC, t.note_id
    """).df()
    assert tfidf.values.tolist() == [[5, 2.12], [1, 0.511], [3, 0.511]]
    tfidf
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### BM25 with stemming — DuckDB's `fts` extension

    Downloads the extension the first time (needs internet once). If that fails,
    the cell says so instead of stopping the notebook.
    """)
    return


@app.cell
def _(con, duckdb):
    try:
        con.execute("INSTALL fts; LOAD fts")
        con.execute("PRAGMA create_fts_index('adjuster_note', 'note_id', 'body')")
        bm25 = con.execute("""
        SELECT note_id,
               round(fts_main_adjuster_note.match_bm25(note_id, 'crushed airbag'), 3) AS score
        FROM adjuster_note WHERE score IS NOT NULL ORDER BY score DESC
        """).df()
        assert bm25["note_id"].tolist() == [5, 3, 1]
    except duckdb.IOException as _e:
        bm25 = f"fts extension unavailable (no internet?): {_e}"
    bm25
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Semantic search — cosine similarity on (toy) embeddings
    """)
    return


@app.cell
def _(con):
    con.execute("""
    CREATE TABLE note_vec (note_id INTEGER PRIMARY KEY, v FLOAT[4]);
    INSERT INTO note_vec VALUES
     (1, [0.9, 0.1, 0.0, 0.1]::FLOAT[4]), (2, [0.2, 0.0, 0.0, 0.9]::FLOAT[4]),
     (3, [0.8, 0.7, 0.6, 0.0]::FLOAT[4]), (4, [0.0, 0.0, 0.1, 0.9]::FLOAT[4]),
     (5, [0.7, 0.8, 0.1, 0.1]::FLOAT[4]);
    """)
    similar = con.execute("""
    SELECT note_id,
           round(array_cosine_similarity(v, [0.8, 0.9, 0.0, 0.0]::FLOAT[4]), 3) AS similarity
    FROM note_vec ORDER BY similarity DESC
    """).df()
    assert similar["note_id"].tolist() == [5, 3, 1, 2, 4]
    similar
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### PII hiding in free text — detection and redaction
    """)
    return


@app.cell
def _(con):
    pii = con.execute(r"""
    SELECT note_id,
           regexp_extract_all(body, '\d{3}-\d{3}-\d{4}')              AS phones,
           regexp_extract_all(body, '[\w.+-]+@[\w-]+(?:\.[\w-]+)+')   AS emails
    FROM adjuster_note
    WHERE regexp_matches(body, '\d{3}-\d{3}-\d{4}|[\w.+-]+@[\w-]+\.[\w-]+')
    ORDER BY note_id
    """).df()
    assert pii["note_id"].tolist() == [1, 3, 5]
    assert list(pii.iloc[1]["emails"]) == ["j.ortiz@mailbox.com"]
    _naive = con.execute(r"""
    SELECT regexp_extract_all(body, '[\w.+-]+@[\w-]+\.[\w.]+') FROM adjuster_note WHERE note_id = 3
    """).fetchone()[0]
    assert _naive == ["j.ortiz@mailbox.com."], "the naive pattern swallows the full stop"
    pii
    return


@app.cell
def _(con):
    redacted = con.execute(r"""
    SELECT regexp_replace(body, '[\w.+-]+@[\w-]+(?:\.[\w-]+)+', '[EMAIL]', 'g') AS body_redacted
    FROM adjuster_note WHERE note_id = 3
    """).fetchone()[0]
    assert redacted.endswith("Email photos to [EMAIL].")
    assert "whiplash" in redacted   # health information is still there — regex can't see it
    redacted
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    That is every query in the deck. The questions on the *Check your understanding*
    slide are a good next step — try answering them against this notebook's tables.
    """)
    return


if __name__ == "__main__":
    app.run()
