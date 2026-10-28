import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .config import DB_PATH, OUTPUT_DIR


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS stories (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL, body TEXT NOT NULL, niche TEXT NOT NULL,
          community TEXT, source_url TEXT, rights_verified INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT NOT NULL CHECK(kind IN ('render','publish')),
          story_id INTEGER NOT NULL REFERENCES stories(id),
          parent_job_id INTEGER REFERENCES jobs(id),
          status TEXT NOT NULL DEFAULT 'queued',
          privacy TEXT DEFAULT 'private',
          output_file TEXT, youtube_id TEXT, title TEXT, description TEXT,
          error TEXT, auto_created INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        db.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', ('niches', json.dumps(['Confessions', 'Moral dilemmas', 'Unexpected endings'])))
        db.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', ('communities', json.dumps(['AmItheAsshole', 'TrueOffMyChest', 'tifu'])))
        db.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', ('autopilot', json.dumps({'enabled':False, 'auto_upload':False, 'upload_consent':False, 'privacy':'private', 'daily_limit':2})))
        cols = {r[1] for r in db.execute('PRAGMA table_info(jobs)')}
        if 'auto_created' not in cols:
            db.execute('ALTER TABLE jobs ADD COLUMN auto_created INTEGER NOT NULL DEFAULT 0')
        db.commit()


@contextmanager
def connect():
    db = sqlite3.connect(DB_PATH, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=20000')
    try:
        yield db
        db.commit()
    finally:
        db.close()


def rows(query: str, params=()):
    with connect() as db:
        return [dict(r) for r in db.execute(query, params).fetchall()]


def one(query: str, params=()):
    with connect() as db:
        row = db.execute(query, params).fetchone()
        return dict(row) if row else None
