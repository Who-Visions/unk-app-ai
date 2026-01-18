"""Clear test trades from the database."""
import sqlite3

conn = sqlite3.connect("data/trades.sqlite")
cur = conn.cursor()
cur.execute("DELETE FROM trades WHERE symbol LIKE '%TEST%'")
deleted = cur.rowcount
conn.commit()
conn.close()
print(f"Deleted {deleted} test trades")
