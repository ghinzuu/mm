-- playlists
CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- playlist ↔ song relation
CREATE TABLE playlist_songs (
    playlist_id INTEGER,
    song_path TEXT,
    position INTEGER,
    PRIMARY KEY (playlist_id, song_path)
);
