"""
Migration script to add live_feedback column to the songs table.
Run this once to update your existing database.
"""
import sqlite3
from pathlib import Path

# Try both possible database paths
DB_PATHS = [
    Path("backend/data/song_master.db"),
    Path("backend/data/song-master.db"),
]

def add_live_feedback_column():
    """Add live_feedback column to songs table if it doesn't exist."""
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
        
        if "live_feedback" not in columns:
            print("Adding live_feedback column to songs table...")
            cursor.execute("ALTER TABLE songs ADD COLUMN live_feedback TEXT")
            conn.commit()
            print("✓ Successfully added live_feedback column")
        else:
            print("✓ live_feedback column already exists")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_live_feedback_column()
