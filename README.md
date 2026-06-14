Kirja-arvostelu-sovellus on Flaskilla toteutettu web-sovellus, jossa käyttäjät voivat rekisteröityä, kirjautua sisään ja lisätä kirja-arvosteluja.

Käyttäjä voi:

- Lisätä kirjan nimen ja arvostelun
- Valita yhden tai useamman genren
- Muokata ja poistaa omia arvosteluja
- Kommentoida muiden käyttäjien arvosteluja
- Tarkastella käyttäjäprofiileja ja tilastoja


Ominaisuudet

- Käyttäjän rekisteröityminen
- Kirjautuminen ja uloskirjautuminen
- Kirja-arvostelun lisääminen (otsikko, arvostelu, genre(t))
- Arvostelujen selaaminen etusivulla
- Arvostelujen muokkaaminen ja poistaminen (vain omat)

Käyttäjäprofiilisivu:
- käyttäjän arvostelut
- arvostelujen määrä
 
Kommenttijärjestelmä:
- käyttäjät voivat kommentoida arvosteluja
- kommentit näkyvät arvostelun alla

Tietokannan rakenne

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

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    review_id INTEGER,
    user_id INTEGER,
    content TEXT,
    FOREIGN KEY (review_id) REFERENCES reviews(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

Asennus ja käynnistys
1. Kloonaa projekti
- git clone https://github.com/eelix-ok/kirja-arvostelu-sovellus.git
- cd kirja-arvostelu-sovellus
- 
2. Luo virtuaaliympäristö
- python -m venv venv
- source venv/Scripts/activate

3. Asenna riippuvuudet
- pip install flask

4. Alusta tietokanta
- python init_db.py

5. Käynnistä sovellus
- flask run

Avaa selaimessa:

http://127.0.0.1:5000
