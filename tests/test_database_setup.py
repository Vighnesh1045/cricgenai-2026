"""Smoke test for database_setup.py: rebuild the DB and sanity-check it."""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_setup import create_db  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "t20_wc_2026.db")

EXPECTED_TABLES = {
    "awards", "batting_stats", "bowling_stats", "key_scorecards",
    "matches", "points_table", "squads", "tournament_summary", "venues",
}


def test_create_db_builds_expected_tables_with_rows():
    create_db()

    assert os.path.exists(DB_PATH), "create_db() did not produce a database file"

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}

        missing = EXPECTED_TABLES - tables
        assert not missing, f"Missing expected tables: {missing}"

        for table in EXPECTED_TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            assert count > 0, f"Table '{table}' loaded but has no rows"
    finally:
        conn.close()


def test_indexes_created_on_key_scorecards_and_awards():
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_player_match" in indexes
        assert "idx_match_award" in indexes
    finally:
        conn.close()
