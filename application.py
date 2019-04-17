import os
import logging
import requests

from flask import Flask, session, render_template, request, redirect, jsonify
from flask.logging import create_logger
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import loadbabel, message, login_required

app = Flask(__name__)

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

# Set up logging
log = create_logger(app)
log.setLevel(logging.INFO)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Search page"""
    if request.method == "POST":
        log.info("index as POST")
        # Ensure select_field was submitted
        select_field = request.form.get("select_field")
        if not select_field:
            return message("must select field to search on", "Error", 400)
        # Ensure search_string was submitted
        search_string = request.form.get("search_string")
        if not search_string:
            return message("must input something to search for", "Error", 400)
        # add wildcards to search
        term = "%" + search_string + "%"
        log.info(f"select field: %s", select_field)
        log.info(f"search term: %s", term)
        log.info(f"select field valid?: %r", select_field in {"isbn", "author", "title", "pub_year"})
        # make sure nothing fishy gets into the database command and construct command in text since can't use placeholders for column
        if select_field not in {"isbn", "author", "title", "pub_year"}:
            return message("something wrong with search field", "Error", 400)
        if select_field != "pub_year":
            command = "SELECT * FROM book WHERE " + select_field + " LIKE :term"
        else:
            command = "SELECT * FROM book WHERE CAST(pub_year AS TEXT) LIKE :term"
        log.info(f"command: %s", command)
        search_results = db.execute(command, {"term": term}).fetchall()
        log.debug("Search results:")
        log.debug(search_results)
        return render_template("index.html", bgtext=loadbabel(), select_field=select_field, search_string=search_string, search_results=search_results)
    else:
        log.info("index as GET")
        return render_template("index.html", bgtext=loadbabel())

@app.route("/api/<isbn>")
def api(isbn):
    """api to serve book and review info"""
    log.info("api called for isbn: %s", isbn)
    # get in books, check exists, get info
    api_book = db.execute("SELECT * FROM book WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    log.debug("database found book:")
    log.debug(api_book)
    if not api_book:
        return jsonify({"Error": "No book with that isbn found"}), 404
    # get in reviews, and cout rows, get average
    num_reviews, = db.execute("SELECT COUNT(*) FROM review WHERE book_id = :book_id", {"book_id":api_book.book_id}).fetchone()
    log.debug("api reviews found: %r", num_reviews)
    if num_reviews:
        avg_rating, = db.execute("SELECT AVG(rating) FROM review WHERE book_id = :book_id", {"book_id":api_book.book_id}).fetchone()
        avg_rating = float(avg_rating)
        log.debug("api found avg rating: %r", avg_rating)
    else:
        avg_rating = "NA"
    return jsonify({
        "title": api_book.title,
        "author": api_book.author,
        "year": api_book.pub_year,
        "isbn": api_book.isbn.strip(),
        "review_count": num_reviews,
        "average_score": avg_rating
    })

@app.route("/book/<int:book_id>", methods=["GET"])
@login_required
def book(book_id):  
    """book page with info and reviews"""
    log.info(f"book route with id: %i", book_id)  
    # check valid book
    if not book_id:
        return message("no book specified", "Error", 400)
    # get book info
    result = db.execute("SELECT * FROM book WHERE book_id = :book_id", {"book_id": book_id}).fetchone()
    log.debug("database got result:")
    log.debug(result)
    log.debug("send to api Key: %s", os.environ['GRKEY'])
    log.debug("send to api isbn: %s", result.isbn.strip())
    # get info from goodreads api
    try:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.environ['GRKEY'], "isbns": result.isbn.strip()})
        log.debug("api got:")
        log.debug(res.json())
        gr_num = res.json()["books"][0]["work_ratings_count"]
        gr_avg = res.json()["books"][0]["average_rating"]
        log.debug("average rating: %s and number of ratings %i", gr_avg, gr_num)
    except:
        gr_num = 0
    # get username to give to template
    user_id = session.get("user_id") 
    username, = db.execute("SELECT username FROM card WHERE user_id = :user_id", {"user_id": user_id}).fetchone()
    log.debug("database got username:")
    log.debug(username)
    # get this user's review of book if exists
    user_rev = db.execute("SELECT * FROM review WHERE user_id = :user_id AND book_id = :book_id", {"user_id": user_id, "book_id": book_id}).fetchone()
    log.debug("database got user review for this book:")
    log.debug(user_rev)
    # get all other reviews for book if exist
    book_revs = db.execute("SELECT username, rating, review FROM review JOIN card ON card.user_id = review.user_id WHERE book_id = :book_id AND username != :username", 
                            {"username": username, "book_id": book_id}).fetchall()
    log.debug("database got reviews from other users for this book:")
    log.debug(book_revs)
    if not book_revs:
        book_revs = 0
    return render_template("book.html", book=result, gr_num=gr_num, gr_avg=gr_avg, username=username, user_rev=user_rev, book_revs=book_revs, bgtext=loadbabel())


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # upon submitting credentials
    if request.method == "POST":
        log.info("login as POST")
        # Ensure username was submitted
        if not request.form.get("username"):
            return message("must provide username", "Error", 400)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return message("must provide password", "Error", 400)
        # Query database for username
        try:
            rows = db.execute("SELECT * FROM card WHERE username = :username",
                              {"username":request.form.get("username")}).fetchall()
        except:
            return message("couldn't get user", "Error", 500)
        # Ensure username exists and password is correct
        log.info(f"len(rows): %i", len(rows))
        if len(rows):
            log.info(f"pass_hash: %s", rows[0].pass_hash)
            log.info(f"check_password_hash: %r", check_password_hash(rows[0].pass_hash.strip(), request.form.get("password")))
        if len(rows) != 1:
            return message("invalid username", "Error", 400)
        if not check_password_hash(rows[0].pass_hash.strip(), request.form.get("password")):
            return message("invalid password", "Error", 400)
        # Remember which user has logged in
        session["user_id"] = rows[0].user_id
        # Redirect user to home page
        return redirect("/")
    # showing up to log in
    else:
        log.info("login as GET")
        return render_template("login.html", bgtext=loadbabel())


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()
    # upon submitting registration form
    if request.method == "POST":
        formusername = request.form.get("username")
        log.info(f"formusername is: %s", formusername)
        password = request.form.get("password")
        confpass = request.form.get("confirmation")
        passhash = generate_password_hash(request.form.get("password"))
        # Ensure username was submitted
        if not formusername:
            return message("must provide username", "Error", 400)
        # Ensure password was submitted
        elif not password:
            return message("must provide password", "Error", 400)
        # Ensure password matches confirmation
        elif password != confpass:
            return message("passwords do not match", "Error", 400)
        # Query database for username
        try:
            # Ensure username does not already exist
            user_lookup =  db.execute("SELECT * FROM card WHERE username = :username", 
                            {"username":formusername}).fetchall()
            log.info(user_lookup)
            if len(user_lookup):
                return message("username taken", "Error", 400)
        except:
            return message("couldn't get user", "Error", 500)
        try:
            # Add user to database
            db.execute('INSERT INTO "card" ("username","pass_hash") VALUES (:username, :pass_hash)',
                       {"username":formusername, "pass_hash":passhash})
            db.commit()
            # Get new user info
            newrow = db.execute("SELECT * FROM card WHERE username = :username",
                                {"username":request.form.get("username")}).fetchall()
            log.info("new card row created:")
            log.info(newrow)
            # Remember user
            session["user_id"] = newrow[0].user_id
        except:
            return message("couldn't update database", "Error", 500)
        # Redirect user to home page
        return redirect("/")
    # upon coming to register
    else:
        return render_template("register.html", bgtext=loadbabel())


@app.route("/reviews", methods=["GET", "POST"])
@login_required
def reviews():
    """show all user reviews"""
    user_id = session.get("user_id")
    if request.method == "POST":
        log.info("reviews as POST")
        # get form input
        book_id = request.form.get("book_id")
        rating = request.form.get("rating")
        review = request.form.get("review")
        log.debug("\nuser with id: %r submitted: \nbook_id: %r\nrating: %r\nreview: %r", user_id, book_id, rating, review)
        # add to database
        try:
            db.execute('INSERT INTO "review" ("user_id","book_id","rating","review") VALUES (:user_id, :book_id, :rating, :review)',
                        {"user_id":user_id, "book_id":book_id, "rating":rating, "review":review})
            db.commit()
        except:
            return message("couldn't add review to database", "Error", 500)
        # Redirect user to reviews page as GET
        return redirect("/reviews")
    else:
        log.info("reviews as GET")
        # lookup all current user's username and reviews, pass to template
        username, = db.execute("SELECT username FROM card WHERE user_id = :user_id", {"user_id": user_id}).fetchone()
        log.debug("database got username: %s", username)
        book_revs = db.execute("SELECT review.book_id, title, author, rating, review FROM review JOIN book ON review.book_id = book.book_id WHERE user_id = :user_id", 
                            {"user_id":user_id}).fetchall()
        log.debug("database got user reviews:")
        log.debug(book_revs)
        return render_template("reviews.html", username=username, book_revs=book_revs, bgtext=loadbabel())