"""
Script to populate album_art field for existing songs if cover art files exist.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("backend/data/song_master.db")
SONGS_DIR = Path("songs")

def populate_album_art():
    """Update album_art field for songs that have existing cover art files."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all songs without album art
        cursor.execute("SELECT id, title FROM songs WHERE album_art IS NULL OR album_art = ''")
        songs = cursor.fetchall()
        
        updated_count = 0
        for song_id, title in songs:
            # Generate possible cover art filenames
            # Replace spaces with underscores
            filename = f"{title.replace(' ', '_')}_cover.jpg"
            cover_path = SONGS_DIR / filename
            
            if cover_path.exists():
                # Update the database with the relative path
                relative_path = f"songs/{filename}"
                cursor.execute(
                    "UPDATE songs SET album_art = ? WHERE id = ?",
                    (relative_path, song_id)
                )
                print(f"✓ Updated '{title}' (ID: {song_id}) with album art: {relative_path}")
                updated_count += 1
            else:
                print(f"✗ No cover art found for '{title}' (expected: {cover_path})")
        
        conn.commit()
        
        if updated_count > 0:
            print(f"\n✓ Successfully updated {updated_count} song(s) with album art")
        else:
            print("\nℹ No songs were updated (no matching cover art files found)")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_album_art()
