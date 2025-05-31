-- SQLite database initialisation script
-- Defines basic tables for the orthophoto tagging backend

CREATE TABLE IF NOT EXISTS image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fotoladu_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    aasta TEXT,
    w INTEGER,
    h INTEGER,
    peakaust TEXT,
    kaust TEXT,
    fail TEXT,
    lend TEXT,
    fotonr TEXT,
    kaardileht TEXT,
    tyyp TEXT,
    allikas TEXT,
    UNIQUE(fotoladu_id)
);

CREATE TABLE IF NOT EXISTS location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    lat REAL,
    lon REAL,
    x REAL,
    y REAL,
    confidence REAL,
    source TEXT,
    FOREIGN KEY(image_id) REFERENCES image(id)
);

CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    state INTEGER,
    FOREIGN KEY(image_id) REFERENCES image(id)
);
