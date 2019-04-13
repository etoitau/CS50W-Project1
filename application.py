import os
import logging

from flask import Flask, session, render_template, request, redirect, jsonify
from flask.logging import create_logger
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import loadbabel, message, login_required, escape

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
        term = "%" + search_string + "%"
        log.info(f"select field: %s", select_field)
        log.info(f"search term: %s", term)
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
        log.info(f"pass_hash: %s", rows[0].pass_hash)
        log.info(f"check_password_hash: %r", check_password_hash(rows[0].pass_hash.strip(), request.form.get("password")))
        if len(rows) != 1 or not check_password_hash(rows[0].pass_hash.strip(), request.form.get("password")):
            return message("invalid username and/or password", "Error", 400)
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