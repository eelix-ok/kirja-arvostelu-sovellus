import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key


# ---------------- HOME (READ + SEARCH) ----------------
@app.route("/")
def index():
    search = request.args.get("search")
    genre = request.args.get("genre")

    if search:
        reviews = db.query("""
            SELECT reviews.id, reviews.title, reviews.review,
                   GROUP_CONCAT(genres.name, ', ') AS genres
            FROM reviews
            LEFT JOIN review_genres ON reviews.id = review_genres.review_id
            LEFT JOIN genres ON genres.id = review_genres.genre_id
            WHERE reviews.title LIKE ?
            GROUP BY reviews.id
        """, ["%" + search + "%"])

    elif genre:
        reviews = db.query("""
            SELECT reviews.id, reviews.title, reviews.review,
                   GROUP_CONCAT(genres.name, ', ') AS genres
            FROM reviews
            LEFT JOIN review_genres ON reviews.id = review_genres.review_id
            LEFT JOIN genres ON genres.id = review_genres.genre_id
            WHERE genres.name = ?
            GROUP BY reviews.id
        """, [genre])

    else:
        reviews = db.query("""
            SELECT reviews.id, reviews.title, reviews.review,
                   GROUP_CONCAT(genres.name, ', ') AS genres
            FROM reviews
            LEFT JOIN review_genres ON reviews.id = review_genres.review_id
            LEFT JOIN genres ON genres.id = review_genres.genre_id
            GROUP BY reviews.id
        """)

    return render_template("index.html", reviews=reviews)


# ---------------- NEW REVIEW PAGE ----------------
@app.route("/new_review")
def new_review():
    return render_template("new_review.html")


# ---------------- REGISTER PAGE ----------------
@app.route("/register")
def register():
    return render_template("register.html")


# ---------------- CREATE USER ----------------
@app.route("/create_user", methods=["POST"])
def create_user():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"

    password_hash = generate_password_hash(password1)

    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return redirect("/login")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    result = db.query(
        "SELECT password_hash FROM users WHERE username = ?",
        [username]
    )

    if not result:
        return "VIRHE: käyttäjää ei löydy"

    password_hash = result[0][0]

    if check_password_hash(password_hash, password):
        session["username"] = username
        return redirect("/")
    else:
        return "VIRHE: väärä salasana"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


# ---------------- CREATE REVIEW ----------------
@app.route("/create_review", methods=["POST"])
def create_review():
    title = request.form["title"].strip()
    review = request.form["review"].strip()
    genres = request.form.getlist("genres")

    if not title or not review or not genres:
        return "VIRHE: kaikki kentät ovat pakollisia"

    db.execute(
        "INSERT INTO reviews (title, review) VALUES (?, ?)",
        (title, review)
    )

    review_id = db.query("SELECT last_insert_rowid()")[0][0]

    for g in genres:
        db.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g,))

        genre_id = db.query(
            "SELECT id FROM genres WHERE name = ?",
            (g,)
        )[0][0]

        db.execute(
            "INSERT INTO review_genres (review_id, genre_id) VALUES (?, ?)",
            (review_id, genre_id)
        )

    return redirect("/")


# ---------------- EDIT ----------------
@app.route("/edit/<int:id>")
def edit(id):
    review = db.query(
        "SELECT id, title, review, genre FROM reviews WHERE id = ?",
        [id]
    )

    if not review:
        return "Arvostelua ei löytynyt"

    return render_template("edit.html", review=review[0])


# ---------------- UPDATE ----------------
@app.route("/update", methods=["POST"])
def update():
    db.execute("""
        UPDATE reviews
        SET title = ?, review = ?, genre = ?
        WHERE id = ?
    """, [
        request.form["title"],
        request.form["review"],
        request.form["genre"],
        request.form["id"]
    ])

    return redirect("/")


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    db.execute("DELETE FROM reviews WHERE id = ?", [id])
    return redirect("/")
