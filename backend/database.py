from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / "claims_analytics.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, uploaded_at TEXT NOT NULL,
                row_count INTEGER NOT NULL, column_count INTEGER NOT NULL,
                target_column TEXT, metadata_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, significance_level REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_run_id TEXT NOT NULL,
                feature_name TEXT NOT NULL, chi_square REAL NOT NULL, p_value REAL NOT NULL,
                degrees_of_freedom INTEGER NOT NULL, significant INTEGER NOT NULL
            );
            """
        )
