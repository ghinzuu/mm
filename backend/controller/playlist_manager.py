import sqlite3

class PlaylistDB:
    def __init__(self, path="playlists.db"):
        self.conn = sqlite3.connect(path)
        self.init_db()

    def init_db(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        self.conn.commit()

    def list_playlists(self):
        c = self.conn.cursor()
        return [row[0] for row in c.execute("SELECT name FROM playlists ORDER BY name")]

    def add_playlist(self, name):
        c = self.conn.cursor()
        c.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
        self.conn.commit()

    def delete_playlist(self, name):
        c = self.conn.cursor()
        c.execute("DELETE FROM playlists WHERE name=?", (name,))
        self.conn.commit()
