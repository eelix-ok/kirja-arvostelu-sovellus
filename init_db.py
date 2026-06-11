import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()

cur.executescript("""
DROP TABLE IF EXISTS review_genres;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    title TEXT,
    review TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE genres (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE review_genres (
    review_id INTEGER,
    genre_id INTEGER,
    FOREIGN KEY (review_id) REFERENCES reviews(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);
""")

con.commit()
con.close()

print("Database reset + updated!")
