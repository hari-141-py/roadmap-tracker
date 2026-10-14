from __future__ import annotations

import json
import os
import sqlite3
import sys
import webbrowser
from datetime import date
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

FROZEN = getattr(sys, "frozen", False)
# Bundled files (templates/static) live in PyInstaller's temp folder when frozen.
RES_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def default_data_dir() -> Path:
    if FROZEN:  # installed .exe: keep data in the user's profile, never next to the exe
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "DevOpsTracker"
    return Path(__file__).resolve().parent / "instance"


DATA_DIR = Path(os.environ.get("DEVOPS_TRACKER_DATA", default_data_dir()))
DB_PATH = Path(os.environ.get("DEVOPS_TRACKER_DB", DATA_DIR / "tracker.sqlite3"))
BACKUP_DIR = DB_PATH.parent / "backups"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

MAX_STATE_BYTES = 5_000_000
KEEP_BACKUPS = 14

app = Flask(
    __name__,
    template_folder=str(RES_DIR / "templates"),
    static_folder=str(RES_DIR / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tracker_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO tracker_state (id, state_json)
            VALUES (1, '{}')
        """)


def read_state() -> tuple[dict, str | None]:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT state_json, updated_at FROM tracker_state WHERE id = 1"
        ).fetchone()
    try:
        state = json.loads(row["state_json"]) if row else {}
    except (TypeError, json.JSONDecodeError):
        state = {}
    return state, (row["updated_at"] if row else None)


def daily_backup():
    """Keep one snapshot per day (last 14 days) next to the database."""
    target = BACKUP_DIR / f"tracker-{date.today().isoformat()}.sqlite3"
    if target.exists():
        return
    try:
        with connect_db() as src, sqlite3.connect(target) as dst:
            src.backup(dst)
        for old in sorted(BACKUP_DIR.glob("tracker-*.sqlite3"))[:-KEEP_BACKUPS]:
            old.unlink(missing_ok=True)
    except (sqlite3.Error, OSError):
        pass


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def get_state():
    state, updated = read_state()
    return jsonify({"state": state, "updated_at": updated})


@app.put("/api/state")
def put_state():
    if not request.is_json:
        return jsonify({"error": "Send a JSON request body."}), 415

    state = request.get_json(silent=True)
    if not isinstance(state, dict):
        return jsonify({"error": "The tracker state must be a JSON object."}), 400

    try:
        serialized = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return jsonify({"error": "Tracker state could not be encoded as JSON."}), 400

    if len(serialized.encode("utf-8")) > MAX_STATE_BYTES:
        return jsonify({"error": "Tracker state is too large."}), 413

    daily_backup()  # snapshot the previous state before the first save of the day
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO tracker_state (id, state_json, updated_at)
            VALUES (1, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
        """, (serialized,))
    return jsonify({"ok": True})


@app.get("/api/backup")
def backup():
    state, _ = read_state()
    body = json.dumps(state, ensure_ascii=False, indent=1)
    return Response(
        body,
        mimetype="application/json",
        headers={"Content-Disposition": 'attachment; filename="devops-tracker-backup.json"'},
    )


@app.post("/api/open")
def open_link():
    """Desktop app only: open a resource link in the user's default browser."""
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", ""))
    if (
        os.environ.get("DEVOPS_TRACKER_DESKTOP") == "1"
        and request.remote_addr in ("127.0.0.1", "::1")
        and url.lower().startswith(("http://", "https://"))
    ):
        webbrowser.open(url)
        return jsonify({"opened": True})
    return jsonify({"opened": False})


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "database": "sqlite"})


init_db()

if __name__ == "__main__":
    # Local development only. For deployment, use a production WSGI server.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
