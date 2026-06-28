import sqlite3
import os
from flask import Flask, redirect, render_template, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key


# ---------------- CSRF ----------------
def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = os.urandom(16).hex()
    return session["csrf_token"]


def check_csrf():
    token = request.form.get("csrf_token")
    return token and token == session.get("csrf_token")


# ---------------- VALIDATION ----------------
ALLOWED_GENRES = {"fantasy", "scifi", "romance", "horror", "mystery"}


def validate_review(title, review_text):
    title = title.strip()
    review_text = review_text.strip()

    if len(title) < 2:
        return "Otsikko on liian lyhyt (min. 2 merkkiä)."

    if len(title) > 100:
        return "Otsikko on liian pitkä (max. 100 merkkiä)."

    if len(review_text) < 10:
        return "Arvostelu on liian lyhyt (min. 10 merkkiä)."

    if len(review_text) > 5000:
        return "Arvostelu on liian pitkä (max. 5000 merkkiä)."

    return None


def validate_user(username, password1, password2):
    username = username.strip()

    if len(username) < 3:
        return "Käyttäjänimen täytyy olla vähintään 3 merkkiä."

    if len(username) > 30:
        return "Käyttäjänimi on liian pitkä (max. 30 merkkiä)."

    if password1 != password2:
        return "Salasanat eivät täsmää."

    if len(password1) < 4:
        return "Salasanan täytyy olla vähintään 4 merkkiä."

    return None


def validate_comment(content):
    content = content.strip()

    if len(content) < 1:
        return "Kommentti ei voi olla tyhjä."

    if len(content) > 500:
        return "Kommentti on liian pitkä (max. 500 merkkiä)."

    return None


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

    generate_csrf_token()

    base_sql = """
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
        base_sql += " WHERE reviews.title LIKE ? GROUP BY reviews.id"
        reviews = db.query(base_sql, ["%" + search + "%"])

    elif genre:
        base_sql += " WHERE genres.name = ? GROUP BY reviews.id"
        reviews = db.query(base_sql, [genre])

    else:
        base_sql += " GROUP BY reviews.id"
        reviews = db.query(base_sql)

    comments = db.query("""
        SELECT comments.review_id,
               users.username,
               comments.content
        FROM comments
        JOIN users ON users.id = comments.user_id
    """)

    return render_template(
        "index.html",
        reviews=reviews,
        comments=comments,
        csrf_token=session.get("csrf_token")
    )


# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    generate_csrf_token()
    return render_template("register.html", csrf_token=session.get("csrf_token"), filled={})


@app.route("/create_user", methods=["POST"])
def create_user():
    if not check_csrf():
        flash("Turvallisuusvirhe (CSRF). Yritä uudelleen.")
        return redirect("/register")

    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    error = validate_user(username, password1, password2)
    if error:
        flash(error)
        return render_template("register.html", csrf_token=session.get("csrf_token"), filled={"username": username})

    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.strip(), generate_password_hash(password1))
        )
    except sqlite3.IntegrityError:
        flash("Käyttäjänimi on jo varattu.")
        return render_template("register.html", csrf_token=session.get("csrf_token"), filled={"username": username})

    flash("Tunnus luotu onnistuneesti! Voit kirjautua sisään.")
    return redirect("/login")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        generate_csrf_token()
        return render_template("login.html", csrf_token=session.get("csrf_token"), filled={})

    if not check_csrf():
        flash("Turvallisuusvirhe (CSRF).")
        return redirect("/login")

    username = request.form["username"]
    password = request.form["password"]

    if not username:
        flash("Käyttäjänimi ei voi olla tyhjä.")
        return render_template("login.html", csrf_token=session.get("csrf_token"), filled={})

    result = db.query(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username.strip(),)
    )

    if not result:
        flash("Käyttäjää ei löytynyt.")
        return render_template("login.html", csrf_token=session.get("csrf_token"), filled={"username": username})

    user_id, password_hash = result[0]

    if not check_password_hash(password_hash, password):
        flash("Väärä salasana.")
        return render_template("login.html", csrf_token=session.get("csrf_token"), filled={"username": username})

    session["username"] = username
    session["user_id"] = user_id
    flash("Kirjautuminen onnistui!")
    return redirect("/")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Kirjauduit ulos.")
    return redirect("/")


# ---------------- NEW REVIEW ----------------
@app.route("/new_review", methods=["GET"])
def new_review():
    generate_csrf_token()
    return render_template("new_review.html", csrf_token=session.get("csrf_token"))


# ---------------- CREATE REVIEW ----------------
@app.route("/create_review", methods=["POST"])
def create_review():
    if not check_csrf():
        flash("Turvallisuusvirhe (CSRF).")
        return redirect("/")

    user_id = get_user_id()
    if not user_id:
        flash("Sinun täytyy olla kirjautunut.")
        return redirect("/login")

    title = request.form["title"]
    review_text = request.form["review"]
    genres = request.form.getlist("genres")

    error = validate_review(title, review_text)
    if error:
        flash(error)
        return redirect("/new_review")

    review_id = db.execute(
        "INSERT INTO reviews (title, review, user_id) VALUES (?, ?, ?)",
        (title.strip(), review_text.strip(), user_id)
    )

    for g in genres:
        if g not in ALLOWED_GENRES:
            flash("Virheellinen genre valittu.")
            return redirect("/new_review")

        db.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g,))
        genre_id = db.query("SELECT id FROM genres WHERE name = ?", (g,))[0][0]

        db.execute("""
            INSERT INTO review_genres (review_id, genre_id)
            VALUES (?, ?)
        """, (review_id, genre_id))

    flash("Arvostelu lisätty onnistuneesti!")
    return redirect("/")


# ---------------- EDIT ----------------
@app.route("/edit/<int:id>")
def edit(id):
    user_id = get_user_id()

    review = db.query("""
        SELECT id, title, review
        FROM reviews
        WHERE id = ? AND user_id = ?
    """, (id, user_id))

    if not review:
        flash("Et voi muokata tätä arvostelua.")
        return redirect("/")

    review = review[0]

    genres = db.query("""
        SELECT genres.name
        FROM genres
        JOIN review_genres ON genres.id = review_genres.genre_id
        WHERE review_genres.review_id = ?
    """, (id,))

    genre_list = [g[0] for g in genres]

    return render_template(
        "edit.html",
        review=review,
        genres=genre_list,
        csrf_token=generate_csrf_token()
    )


# ---------------- UPDATE ----------------
@app.route("/update", methods=["POST"])
def update():
    if not check_csrf():
        flash("Turvallisuusvirhe (CSRF).")
        return redirect("/")

    user_id = get_user_id()
    if not user_id:
        flash("Et ole kirjautunut.")
        return redirect("/login")

    review_id = request.form["id"]
    title = request.form["title"]
    review_text = request.form["review"]
    genres = request.form.getlist("genres")

    error = validate_review(title, review_text)
    if error:
        flash(error)
        return redirect(f"/edit/{review_id}")

    owner = db.query(
        "SELECT user_id FROM reviews WHERE id = ?",
        (review_id,)
    )

    if not owner or owner[0][0] != user_id:
        flash("Ei oikeuksia muokata tätä.")
        return redirect("/")

    db.execute("""
        UPDATE reviews
        SET title = ?, review = ?
        WHERE id = ?
    """, (title.strip(), review_text.strip(), review_id))

    db.execute("DELETE FROM review_genres WHERE review_id = ?", (review_id,))

    for g in genres:
        if g not in ALLOWED_GENRES:
            flash("Virheellinen genre.")
            return redirect(f"/edit/{review_id}")

        db.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g,))
        genre_id = db.query("SELECT id FROM genres WHERE name = ?", (g,))[0][0]

        db.execute("""
            INSERT INTO review_genres (review_id, genre_id)
            VALUES (?, ?)
        """, (review_id, genre_id))

    flash("Muutokset tallennettu!")
    return redirect("/")


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not check_csrf():
        flash("Turvallisuusvirhe (CSRF).")
        return redirect("/")

    user_id = get_user_id()
    if not user_id:
        flash("Ei oikeuksia.")
        return redirect("/")

    review = db.query(
        "SELECT user_id FROM reviews WHERE id = ?",
        (id,)
    )

    if not review or review[0][0] != user_id:
        flash("Ei oikeuksia poistaa tätä.")
        return redirect("/")

    db.execute("DELETE FROM review_genres WHERE review_id = ?", (id,))
    db.execute("DELETE FROM reviews WHERE id = ?", (id,))

    flash("Arvostelu poistettu.")
    return redirect("/")


# ---------------- USER PAGE ----------------
@app.route("/user/<int:user_id>")
def user_page(user_id):

    user = db.query(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    )

    if not user:
        flash("Käyttäjää ei löytynyt.")
        return redirect("/")

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
        review_count=review_count,
        csrf_token=session.get("csrf_token")
    )


# ---------------- COMMENTS ----------------
@app.route("/add_comment", methods=["POST"])
def add_comment():
    if not check_csrf():
        flash("Turvallisuusvirhe (CSRF).")
        return redirect("/")

    user_id = get_user_id()
    if not user_id:
        flash("Sinun täytyy olla kirjautunut.")
        return redirect("/login")

    review_id = request.form["review_id"]
    content = request.form["content"]

    error = validate_comment(content)
    if error:
        flash(error)
        return redirect("/")

    db.execute("""
        INSERT INTO comments (review_id, user_id, content)
        VALUES (?, ?, ?)
    """, (review_id, user_id, content.strip()))

    flash("Kommentti lisätty.")
    return redirect("/")
