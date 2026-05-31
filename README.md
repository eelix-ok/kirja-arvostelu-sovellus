# Kirja-arvostelu-sovellus

## Sovelluksen kuvaus

Kirja-arvostelu-sovellus on Flaskilla toteutettu web-sovellus, jossa käyttäjät voivat rekisteröityä, kirjautua sisään ja lisätä kirja-arvosteluja. Sovelluksessa käyttäjä voi kirjoittaa kirjan nimen, arvostelun sekä valita genren.

Sovellus käyttää SQLite-tietokantaa käyttäjien ja arvostelujen tallentamiseen.

---

## Ominaisuudet

- Käyttäjän rekisteröityminen
- Kirjautuminen ja uloskirjautuminen
- Kirja-arvostelun lisääminen (otsikko, arvostelu, genre)
- Arvostelut tallennetaan SQLite-tietokantaan
- Viestit onnistuneista toiminnoista

---

## Asennus ja käynnistys

### 1. Kloonaa projekti

bash
git clone <https://github.com/eelix-ok/kirja-arvostelu-sovellus/>
cd kirja-arvostelu-sovellus

### 2. Aktivoi venv

python -m venv venv
source venv/Scripts/activate

### 3. Asenna flask

pip install flask

### 4. Tee tietokanta

python init_db.py

Tietokannan rakenne:

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    title TEXT,
    review TEXT,
    genre TEXT
);

### 5. Käynnistä sovellus

flask run

Ja siirry saamaasi osoitteeseen

