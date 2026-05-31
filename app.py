import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key


# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")


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
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
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

    sql = "SELECT password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])

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
@app.route("/create", methods=["POST"])
def create_review():
    title = request.form["title"]
    description = request.form["review"]
    genre = request.form["genre"]

    db.execute(
        "INSERT INTO reviews (title, review, genre) VALUES (?, ?, ?)",
        (title, description, genre)
    )

    flash("Arvostelu julkaistu!")
    return redirect("/")
