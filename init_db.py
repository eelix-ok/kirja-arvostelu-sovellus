import sqlite3

con = sqlite3.connect("database.db")

with open("schema.sql") as f:
    con.executescript(f.read())

con.close()

print("Database initialized!")
