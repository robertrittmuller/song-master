"""
Migration script to add album_art column to the songs table.
Run this once to update your existing database.
"""
import sqlite3
from pathlib import Path

# Try both possible database paths
DB_PATHS = [
    Path("backend/data/song_master.db"),
    Path("backend/data/song-master.db"),
]

def add_album_art_column():
    """Add album_art column to songs table if it doesn't exist."""
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
        # Check if column already exists
        cursor.execute("PRAGMA table_info(songs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "album_art" not in columns:
            print("Adding album_art column to songs table...")
            cursor.execute("ALTER TABLE songs ADD COLUMN album_art TEXT")
            conn.commit()
            print("✓ Successfully added album_art column")
        else:
            print("✓ album_art column already exists")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_album_art_column()

