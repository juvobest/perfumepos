import sqlite3
from app.database.connection import DATABASE_PATH

c = sqlite3.connect(str(DATABASE_PATH))

print("Database:", DATABASE_PATH)
print("Integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print(
    "Tables:",
    c.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0],
)

c.close()
