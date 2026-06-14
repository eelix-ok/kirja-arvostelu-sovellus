import sqlite3
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key


# ---------------- HELPERS ----------------
def get_user_id():
    if "user_id" in session:
        return session["user_id"]

    username = session.get("username")
    if not username:
        return None

    user = db.query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )

    if not user:
        return None

    session["user_id"] = user[0][0]
    return user[0][0]


# ---------------- HOME ----------------
@app.route("/")
def index():
    search = request.args.get("search")
    genre = request.args.get("genre")

    sql = """
        SELECT reviews.id,
               reviews.title,
               reviews.review,
               users.id,
               users.username,
               GROUP_CONCAT(genres.name, ', ') AS genres
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        LEFT JOIN review_genres ON reviews.id = review_genres.review_id
        LEFT JOIN genres ON genres.id = review_genres.genre_id
    """

    if search:
        sql += " WHERE reviews.title LIKE ? GROUP BY reviews.id"
        reviews = db.query(sql, ["%" + search + "%"])

    elif genre:
        sql += " WHERE genres.name = ? GROUP BY reviews.id"
        reviews = db.query(sql, [genre])

    else:
        sql += " GROUP BY reviews.id"
        reviews = db.query(sql)

    return render_template("index.html", reviews=reviews)


# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    return render_template("register.html")


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
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username,)
    )

    if not result:
        return "VIRHE: käyttäjää ei löydy"

    user_id, password_hash = result[0]

    if check_password_hash(password_hash, password):
        session["username"] = username
        session["user_id"] = user_id
        return redirect("/")
    else:
        return "VIRHE: väärä salasana"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- NEW REVIEW PAGE ----------------
@app.route("/new_review", methods=["GET"])
def new_review():
    return render_template("new_review.html")


# ---------------- CREATE REVIEW ----------------
@app.route("/create_review", methods=["POST"])
def create_review():
    user_id = get_user_id()

    if not user_id:
        return "Ei kirjautunut", 403

    title = request.form["title"].strip()
    review_text = request.form["review"].strip()
    genres = request.form.getlist("genres")

    review_id = db.execute(
        "INSERT INTO reviews (title, review, user_id) VALUES (?, ?, ?)",
        (title, review_text, user_id)
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
    user_id = get_user_id()

    review = db.query(
        "SELECT id, title, review, user_id FROM reviews WHERE id = ?",
        (id,)
    )

    if not review:
        return "Ei löydy", 404

    review = review[0]

    if review[3] != user_id:
        return "Ei oikeuksia", 403

    genres = db.query("""
        SELECT genres.name
        FROM genres
        JOIN review_genres ON genres.id = review_genres.genre_id
        WHERE review_genres.review_id = ?
    """, (id,))

    review = list(review) + [", ".join([g[0] for g in genres])]

    return render_template("edit.html", review=review)


# ---------------- UPDATE ----------------
@app.route("/update", methods=["POST"])
def update():
    user_id = get_user_id()

    review_id = request.form["id"]
    title = request.form["title"]
    review_text = request.form["review"]
    genres = request.form.getlist("genres")

    updated = db.execute("""
        UPDATE reviews
        SET title = ?, review = ?
        WHERE id = ? AND user_id = ?
    """, (title, review_text, review_id, user_id))

    if updated == 0:
        return "Ei oikeuksia", 403

    db.execute("DELETE FROM review_genres WHERE review_id = ?", (review_id,))

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


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    user_id = get_user_id()

    if not user_id:
        return "Ei oikeuksia", 403

    review = db.query(
        "SELECT user_id FROM reviews WHERE id = ?",
        (id,)
    )

    if not review:
        return "Ei löydy", 404

    if review[0][0] != user_id:
        return "Ei oikeuksia", 403

    db.execute("DELETE FROM review_genres WHERE review_id = ?", (id,))
    db.execute("DELETE FROM reviews WHERE id = ?", (id,))

    return redirect("/")


# ---------------- USER PAGE ----------------
@app.route("/user/<int:user_id>")
def user_page(user_id):

    user = db.query(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    )

    if not user:
        return "Käyttäjää ei löytynyt", 404

    user = user[0]

    reviews = db.query("""
        SELECT reviews.id,
            reviews.title,
            reviews.review,
            GROUP_CONCAT(genres.name, ', ') AS genres
        FROM reviews
        LEFT JOIN review_genres ON reviews.id = review_genres.review_id
        LEFT JOIN genres ON genres.id = review_genres.genre_id
        WHERE reviews.user_id = ?
        GROUP BY reviews.id
        ORDER BY reviews.id DESC
    """, (user_id,))

    review_count = db.query("""
        SELECT COUNT(*)
        FROM reviews
        WHERE user_id = ?
    """, (user_id,))[0][0]

    return render_template(
        "user.html",
        user=user,
        reviews=reviews,
        review_count=review_count
    )
