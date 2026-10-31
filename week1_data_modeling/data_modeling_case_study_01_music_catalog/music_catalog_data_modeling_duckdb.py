import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Relational Data Modeling — Hands-on DuckDB Notebook
    ## Case Study 1 of 3: Music Catalog

    Companion notebook to **`relational_data_modeling_music_catalog.md`** — the
    smallest possible complete example (3 tables, 2 chained one-to-many
    relationships, no many-to-many, no normalization theory).

    Every table below is built and populated with a single, pure-SQL `mo.sql()`
    cell, in dependency order, backed by marimo's embedded in-memory DuckDB
    connection.

    * **Part 1** creates and populates the 3-table schema.
    * **Part 2** runs sample business-question queries against it.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 1 — Schema & Sample Data
    """)
    return


@app.cell
def _(mo):
    # R1: an artist can release many albums; a new artist may have zero albums yet
    # (Fontaines D.C., below, is newly signed -- optional participation).
    artists = mo.sql(
        f"""
        CREATE TABLE artists (
            artist_id   INTEGER PRIMARY KEY,
            artist_name VARCHAR NOT NULL,
            country     VARCHAR
        );

        INSERT INTO artists (artist_id, artist_name, country) VALUES
         (1,'Radiohead','UK'),
         (2,'Beyoncé','USA'),
         (3,'BTS','South Korea'),
         (4,'Fontaines D.C.','Ireland');

        SELECT * FROM artists;
        """
    )
    return


@app.cell
def _(mo):
    # R2: every album must belong to exactly one artist (mandatory FK) -- no orphan albums.
    albums = mo.sql(
        f"""
        CREATE TABLE albums (
            album_id      INTEGER PRIMARY KEY,
            artist_id     INTEGER NOT NULL REFERENCES artists(artist_id),
            title         VARCHAR NOT NULL,
            release_year  INTEGER,
            genre         VARCHAR
        );

        INSERT INTO albums (album_id, artist_id, title, release_year, genre) VALUES
         (1,1,'OK Computer',1997,'Alternative Rock'),
         (2,1,'In Rainbows',2007,'Alternative Rock'),
         (3,2,'Renaissance',2022,'R&B/Dance'),
         (4,3,'Map of the Soul: 7',2020,'K-Pop');

        SELECT * FROM albums;
        """
    )
    return


@app.cell
def _(mo):
    # R3: every track must belong to exactly one album (mandatory FK).
    # R5: duration must be positive (CHECK).
    # R6: two tracks on the SAME album can't share a track_number -- a composite
    # UNIQUE constraint that is NOT the primary key (track_id is the PK).
    tracks = mo.sql(
        f"""
        CREATE TABLE tracks (
            track_id          INTEGER PRIMARY KEY,
            album_id          INTEGER NOT NULL REFERENCES albums(album_id),
            track_number      INTEGER NOT NULL CHECK (track_number > 0),
            title             VARCHAR NOT NULL,
            duration_seconds  INTEGER NOT NULL CHECK (duration_seconds > 0),
            UNIQUE (album_id, track_number)
        );

        INSERT INTO tracks (track_id, album_id, track_number, title, duration_seconds) VALUES
         (1,1,1,'Airbag',284),
         (2,1,2,'Paranoid Android',383),
         (3,1,3,'Exit Music (For a Film)',264),
         (4,2,1,'15 Step',238),
         (5,2,2,'Bodysnatchers',242),
         (6,2,3,'Nude',255),
         (7,3,1,'I''m That Girl',178),
         (8,3,2,'Cozy',196),
         (9,3,3,'Alien Superstar',183),
         (10,4,1,'Interlude: Shadow',204),
         (11,4,2,'Black Swan',200),
         (12,4,3,'ON',247);

        SELECT * FROM tracks;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Proving the Constraints Fire

    A constraint in the DDL is only a promise until you see it **refuse** bad
    data. Each statement below breaks one business rule; the database must reject
    every one (the cell checks that it does, so none of these rows can leak into
    the queries in Part 2).

    The first three are the deck's tests. The first is the new idea in this case
    study: not a foreign key or a `CHECK`, but the composite
    `UNIQUE (album_id, track_number)` enforcing R6.
    """)
    return


@app.cell
def _(albums, artists, tracks):
    import duckdb as _duckdb
    import pandas as _pd

    _tables_built = (albums, artists, tracks,)   # run only after Part 1 has built these tables
    _attempts = [
        ("R6", "a second track 1 on album 1",
         "INSERT INTO tracks (track_id, album_id, track_number, title, duration_seconds) VALUES (99, 1, 1, 'Duplicate Track 1', 200)"),
        ("R2", "an album for artist 999 (does not exist)",
         "INSERT INTO albums (album_id, artist_id, title) VALUES (99, 999, 'Orphan Album')"),
        ("R5", "a track lasting -5 seconds",
         "INSERT INTO tracks (track_id, album_id, track_number, title, duration_seconds) VALUES (98, 1, 4, 'Bad Duration', -5)"),
        ("R3", "a track with no album",
         "INSERT INTO tracks (track_id, album_id, track_number, title, duration_seconds) VALUES (97, NULL, 5, 'No Album', 180)"),
    ]
    _results = []
    for _rule, _what, _sql in _attempts:
        try:
            _duckdb.execute(_sql)
            _results.append((_rule, _what, "ACCEPTED — constraint missing!"))
        except Exception as _e:
            _results.append((_rule, _what, f"rejected: {type(_e).__name__}"))
    _proof = _pd.DataFrame(_results, columns=["rule", "bad data", "outcome"])
    # a missing table would also "reject" -- so accept only constraint / type errors
    assert _proof["outcome"].isin(["rejected: ConstraintException",
                                   "rejected: ConversionException"]).all(), _proof
    _proof
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 2 — Sample Queries

    Six business questions: two joins, an aggregation, a LEFT JOIN with COUNT, an
    anti-join, and a row-value subquery.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q1 — Albums by artist
    """)
    return


@app.cell
def _(albums, artists, mo):
    q1_albums_by_artist = mo.sql(
        f"""
        SELECT a.artist_name, 
               al.title, 
               al.release_year
        FROM artists a
        JOIN albums al ON al.artist_id = a.artist_id
        ORDER BY a.artist_name, al.release_year;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q2 — Tracklist for a specific album
    """)
    return


@app.cell
def _(albums, mo, tracks):
    q2_tracklist_for_album = mo.sql(
        f"""
        SELECT al.title AS album, 
               t.track_number, 
               t.title AS track, 
               t.duration_seconds
        FROM tracks t
        JOIN albums al ON al.album_id = t.album_id
        WHERE al.title = 'OK Computer'
        ORDER BY t.track_number;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q3 — Total duration per album (aggregation)
    """)
    return


@app.cell
def _(albums, mo, tracks):
    q3_album_total_duration = mo.sql(
        f"""
        SELECT al.title, 
               COUNT(*) AS num_tracks,
               SUM(t.duration_seconds) AS total_seconds,
               ROUND(SUM(t.duration_seconds) / 60.0, 1) AS total_minutes
        FROM albums al
        JOIN tracks t ON t.album_id = al.album_id
        GROUP BY al.title
        ORDER BY total_seconds DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q4 — Album count per artist (LEFT JOIN + COUNT)
    """)
    return


@app.cell
def _(albums, artists, mo):
    q4_albums_per_artist = mo.sql(
        f"""
        SELECT a.artist_name, 
               COUNT(al.album_id) AS num_albums
        FROM artists a
        LEFT JOIN albums al ON al.artist_id = a.artist_id
        GROUP BY a.artist_name
        ORDER BY num_albums DESC;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q5 — Artists with no albums yet (anti-join)
    """)
    return


@app.cell
def _(albums, artists, mo):
    q5_artists_no_albums = mo.sql(
        f"""
        SELECT a.artist_name
        FROM artists a
        LEFT JOIN albums al ON al.artist_id = a.artist_id
        WHERE al.album_id IS NULL;
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Q6 — Longest track per album (row-value subquery)
    """)
    return


@app.cell
def _(albums, mo, tracks):
    q6_longest_track_per_album = mo.sql(
        f"""
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
        """
    )
    return


if __name__ == "__main__":
    app.run()
