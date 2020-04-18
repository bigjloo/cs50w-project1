import os
import requests
import json

from flask import Flask, session, render_template, request, redirect, flash, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_wtf.csrf import CSRFProtect
from forms import RegistrationForm, SearchForm, LoginForm, ReviewForm


app = Flask(__name__)
csrf = CSRFProtect(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# set secret key
app.config["SECRET_KEY"] = "jN>fWH+>d$ZuNxAb@zy2-5 ^ LJ: SvgNX b.(~; V*j6O_+p9mZynZB=ZE: f[xZ!I"


@app.route("/", methods=["GET", "POST"])
def index():
    form = LoginForm()

    # login
    if request.method == "POST" and form.validate_on_submit():
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                          {"username": username, "password": password}).fetchone()
        if user is None:
            flash("Try log in again")
            return render_template("index.html", form=form)
        user_id = user.id
        session["user_id"] = user_id
        session["username"] = username
        return redirect(url_for("user", user_id=user_id))

    return render_template("index.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    # registration
    if request.method == "POST":
        if form.validate_on_submit():
            username = request.form.get("username")
            password = request.form.get("password")
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {
                "username": username, "password": password})
            db.commit()
            flash('Registration Successful')
            return redirect(url_for("index"))
        else:
            flash("Registration Error")
            return render_template("register.html", form=form)
    return render_template("register.html", form=form)


@app.route("/user/<int:user_id>")
def user(user_id):
    form = SearchForm()
    return render_template("search.html", form=form)


@app.route("/books", methods=["POST", "GET"])
def books():
    form = SearchForm()
    if request.method == "POST":
        search_type = request.form.get("search_select")
        search_value = request.form.get("search_value")
        books = db.execute(
            "SELECT * FROM books WHERE {} LIKE '%{}%';".format(search_type, search_value))
        if books.rowcount == 0:
            flash("Book not found. Please try again")
            form = SearchForm()
            return render_template("search.html", form=form)
        return render_template("books.html", form=form, books=books)
    return render_template("books.html", form=form)


@app.route("/book/<isbn_id>")
def book(isbn_id):
    form = ReviewForm()
    book = db.execute(
        "SELECT * FROM books WHERE isbn_id = :isbn_id", {"isbn_id": isbn_id}).fetchone()
    goodreadsData = requests.get("https://www.goodreads.com/book/review_counts.json",
                                 params={"isbns": isbn_id, "key": "VzAR63bf45MBzRSC1o1A"})
    if goodreadsData.status_code != 200:
        raise Exception(
            "ERROR: API REQUEST UNSUCCESSFUL, {}".format(res.status_code))
    user_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {
                             "user_id": session['user_id'], "book_id": book.id}).fetchone()
    if user_review is not None:
        user_review = user_review.review
    return render_template("book.html", book=book, form=form, data=goodreadsData, user_review=user_review)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for("index"))


@app.route('/review/<int:book_id>', methods=["POST"])
def review(book_id):
    rating = request.form.get("rating")
    review = request.form.get("text")
    if db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": session['user_id'], "book_id": book_id}).rowcount != 0:
        flash("Only one review allowed")
        book = db.execute(
            "SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
        form = ReviewForm()
        user_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {
            "user_id": session['user_id'], "book_id": book.id}).fetchone()
        user_review = user_review.review
        goodreadsData = requests.get("https://www.goodreads.com/book/review_counts.json",
                                     params={"isbns": book.isbn_id, "key": "VzAR63bf45MBzRSC1o1A"})
        if goodreadsData.status_code != 200:
            raise Exception(
                "ERROR: API REQUEST UNSUCCESSFUL, {}".format(res.status_code))
        return render_template("book.html", book=book, form=form, data=goodreadsData, user_review=user_review)
    else:
        db.execute("INSERT INTO reviews (user_id, book_id, rating, review) VALUES (:user_id, :book_id, :rating, :review)", {
            "user_id": session['user_id'], "book_id": book_id, "rating": rating, "review": review})
        db.commit()
        flash("Review Submitted!")
        return redirect(url_for('user', user_id=session['user_id']))


@app.route("/api/<string:isbn_id>")
def api(isbn_id):
    book = db.execute(
        "SELECT * FROM books WHERE isbn_id = :isbn_id", {"isbn_id": isbn_id}).fetchone()
    if book is None:
        return jsonify({"error": "No such book in database"}), 404
    goodreadsData = requests.get("https://www.goodreads.com/book/review_counts.json",
                                 params={"isbns": isbn_id, "key": "VzAR63bf45MBzRSC1o1A"})
    jsonData = json.loads(goodreadsData.text)
    averageRating = int(jsonData["books"][0]["average_rating"])
    ratingCount = jsonData["books"][0]["ratings_count"]
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": isbn_id,
        "review_count": ratingCount,
        "average_score": averageRating
    })
