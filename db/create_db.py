"""Initialize SQLite database using the SQL script."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name('init.sql')
DB_PATH = Path(__file__).with_name('fotoladu.sqlite.db')


def init_db(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> None:
    sql = schema_path.read_text()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
    print(f"Database initialised at {db_path}")


if __name__ == '__main__':
    init_db()
