import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key

def get_user_id():
    username = session.get("username")
    if not username:
        return None

    user = db.query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )

    if not user:
        return None

    return user[0][0]


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
    if "username" not in session:
        return "Ei kirjautunut", 403

    title = request.form["title"].strip()
    review = request.form["review"].strip()
    genres = request.form.getlist("genres")

    if not title or not review:
        return "VIRHE: title ja review pakollisia"

    username = session.get("username")

    if not username:
        return "Ei kirjautunut", 403

    user = db.query(
    "SELECT id FROM users WHERE username = ?",
    (username,)
    )

    if len(user) == 0:
        return "Käyttäjää ei löydy (rekisteröidy uudelleen)", 403

    user_id = user[0][0]

    review_id = db.execute(
        "INSERT INTO reviews (title, review, user_id) VALUES (?, ?, ?)",
        (title, review, user_id)
    )

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
    print("SESSION:", session.get("username"))
    print("USER_ID:", get_user_id())
    print("REVIEW USER_ID:", db.query(
    "SELECT user_id FROM reviews WHERE id = ?",
    (id,)
))
    user_id = get_user_id()
    if not user_id:
        return "Ei oikeuksia", 403

    review = db.query("""
        SELECT reviews.id, reviews.title, reviews.review,
               GROUP_CONCAT(genres.name, ', ') AS genres
        FROM reviews
        LEFT JOIN review_genres ON reviews.id = review_genres.review_id
        LEFT JOIN genres ON genres.id = review_genres.genre_id
        WHERE reviews.id = ? AND reviews.user_id = ?
        GROUP BY reviews.id
    """, (id, user_id))

    if not review:
        return "Ei oikeuksia tai ei löydy", 403

    return render_template("edit.html", review=review[0])

# ---------------- UPDATE ----------------
@app.route("/update", methods=["POST"])
def update():
    user_id = get_user_id()
    if not user_id:
        return "Ei oikeuksia", 403

    review_id = request.form["id"]
    title = request.form["title"].strip()
    review = request.form["review"].strip()
    genres = request.form.getlist("genres")

    updated = db.execute("""
        UPDATE reviews
        SET title = ?, review = ?
        WHERE id = ? AND user_id = ?
    """, (title, review, review_id, user_id))

    if updated == 0:
        return "Ei oikeuksia", 403

    db.execute("DELETE FROM review_genres WHERE review_id = ?", (review_id,))

    for g in genres:
        db.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g,))

        genre_id = db.query(
            "SELECT id FROM genres WHERE name = ?",
            (g,)
        )[0][0]

        db.execute("""
            INSERT INTO review_genres (review_id, genre_id)
            VALUES (?, ?)
        """, (review_id, genre_id))

    return redirect("/")
# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    user_id = get_user_id()

    if not user_id:
        return "Ei oikeuksia", 403

    db.execute("DELETE FROM review_genres WHERE review_id = ?", (id,))

    deleted = db.execute("""
        DELETE FROM reviews
        WHERE id = ? AND user_id = ?
    """, (id, user_id))

    if deleted == 0:
        return "Ei oikeuksia", 403

    return redirect("/")
