import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH, KEYS_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            niche TEXT DEFAULT '',
            tone TEXT DEFAULT '',
            audience TEXT DEFAULT '',
            reference_urls TEXT DEFAULT '',
            total_requested INTEGER DEFAULT 0,
            total_successful INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            created_at TEXT DEFAULT '',
            completed_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            video_number INTEGER NOT NULL,
            topic TEXT DEFAULT '',
            category TEXT DEFAULT 'facts',
            core_fact TEXT DEFAULT '',
            archetype TEXT DEFAULT '',
            hook TEXT DEFAULT '',
            full_script TEXT DEFAULT '',
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            pinned_comment TEXT DEFAULT '',
            voice_path TEXT DEFAULT '',
            thumbnail_path TEXT DEFAULT '',
            final_video_path TEXT DEFAULT '',
            duration_seconds REAL DEFAULT 0,
            file_size_mb REAL DEFAULT 0,
            status TEXT DEFAULT 'queued',
            error_message TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            completed_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT UNIQUE NOT NULL,
            value TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def create_batch(batch_id, niche, tone, audience,
                 reference_urls, total):
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO batches
           (batch_id, niche, tone, audience,
            reference_urls, total_requested, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (batch_id, niche, tone, audience,
         str(reference_urls), total,
         datetime.now().isoformat())
    )
    conn.commit()
    result = cursor.lastrowid
    conn.close()
    return result


def update_batch(batch_id, **kwargs):
    if not kwargs:
        return
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [batch_id]
    conn.execute(
        f"UPDATE batches SET {sets} WHERE batch_id = ?",
        vals
    )
    conn.commit()
    conn.close()


def create_video(batch_id, video_number):
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO videos (batch_id, video_number, created_at)
           VALUES (?, ?, ?)""",
        (batch_id, video_number, datetime.now().isoformat())
    )
    conn.commit()
    result = cursor.lastrowid
    conn.close()
    return result


def update_video(video_id, **kwargs):
    if not kwargs:
        return
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [video_id]
    conn.execute(
        f"UPDATE videos SET {sets} WHERE id = ?",
        vals
    )
    conn.commit()
    conn.close()


def get_batch(batch_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM batches WHERE batch_id = ?",
        (batch_id,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_batch_videos(batch_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM videos WHERE batch_id = ?
           ORDER BY video_number ASC""",
        (batch_id,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_video(video_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM videos WHERE id = ?",
        (video_id,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def save_setting(key, value):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO settings
           (key_name, value) VALUES (?, ?)""",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM settings WHERE key_name = ?",
        (key,)
    ).fetchone()
    conn.close()
    if row:
        return row['value']
    return default


def save_keys(groq_key, pexels_key, pixabay_key):
    data = {
        "groq_key": groq_key,
        "pexels_key": pexels_key,
        "pixabay_key": pixabay_key
    }
    try:
        with open(KEYS_PATH, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Could not save keys file: {e}")
    save_setting("groq_key", groq_key)
    save_setting("pexels_key", pexels_key)
    save_setting("pixabay_key", pixabay_key)


def load_keys():
    try:
        if os.path.exists(KEYS_PATH):
            with open(KEYS_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "groq_key": get_setting("groq_key", ""),
        "pexels_key": get_setting("pexels_key", ""),
        "pixabay_key": get_setting("pixabay_key", "")
    }


init_db()
