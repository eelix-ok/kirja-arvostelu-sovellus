CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    title TEXT,
    review TEXT
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
