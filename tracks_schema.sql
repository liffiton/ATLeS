CREATE TABLE Tracks (
    key text PRIMARY KEY UNIQUE,
    lines integer,
    acquired real,
    missing real,
    lost real,
    heat text
)
