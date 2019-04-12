import os

from flask import Flask, session, render_template, request, redirect, jsonify
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


@app.route("/")
@login_required
def index():
    return render_template("search.html", bgtext=loadbabel())


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # upon submitting credentials
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return message("must provide username", "Error", 400)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return message("must provide password", "Error", 400)
        # Query database for username
        try:
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                              username=request.form.get("username")).fetchall()
        except:
            return message("couldn't get user", "Error", 500)
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form.get("password")):
            return message("invalid username and/or password", "Error", 400)
        # Remember which user has logged in
        session["user_id"] = rows[0].user_id
        # Redirect user to home page
        return redirect("/")
    # showing up to log in
    else:
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
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                              username=formusername).fetchall()
            # Ensure username does not already exist
            if len(rows):
                return message("username taken", "Error", 400)
        except:
            return message("couldn't get user", "Error", 500)
        try:
            # Add user to database
            db.execute('INSERT INTO "users" ("username","hash") VALUES (:username, :password)',
                       username=formusername, password=passhash)
            db.commit()
            # Get new user info
            newrow = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))
            # Remember user
            session["user_id"] = newrow[0].user_id
        except:
            return message("couldn't update database", "Error", 500)
        # Redirect user to home page
        return redirect("/")
    # upon coming to register
    else:
        return render_template("register.html", bgtext=loadbabel())