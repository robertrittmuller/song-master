"""
Migration script to create the song_versions table.
Run this once to update your existing database.
"""
import sqlite3
from pathlib import Path

# Try both possible database paths
DB_PATHS = [
    Path("backend/data/song_master.db"),
    Path("backend/data/song-master.db"),
]

def create_song_versions_table():
    """Create song_versions table if it doesn't exist."""
    # Find which database exists
    db_path = None
    for path in DB_PATHS:
        if path.exists():
            db_path = path
            print(f"Found database at: {db_path}")
            break
    
    if not db_path:
        print("Error: No database file found. Please start the backend first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='song_versions'")
        if not cursor.fetchone():
            print("Creating song_versions table...")
            cursor.execute("""
                CREATE TABLE song_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    lyrics TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX ix_song_versions_id ON song_versions (id)")
            cursor.execute("CREATE INDEX ix_song_versions_song_id ON song_versions (song_id)")
            conn.commit()
            print("✓ Successfully created song_versions table")
        else:
            print("✓ song_versions table already exists")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_song_versions_table()
