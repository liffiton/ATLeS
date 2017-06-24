CREATE TABLE IF NOT EXISTS Boxes (
    name TEXT PRIMARY KEY UNIQUE,
    ip TEXT NOT NULL,
    port INTEGER NOT NULL,
    local BOOLEAN NOT NULL CHECK (local in (0,1)),
    user TEXT,
    connected BOOLEAN NOT NULL CHECK (connected IN (0,1)),
    hasdisplay BOOLEAN NOT NULL CHECK (hasdisplay IN (0,1)),
    gitshort TEXT,
    gitlong TEXT,
    error TEXT
)

CREATE TABLE IF NOT EXISTS Tracks (
    key text PRIMARY KEY UNIQUE,
    lines integer,
    acquired real,
    missing real,
    lost real,
    heat text,
    invalid_heat text
)
