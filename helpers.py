import requests
import urllib.parse
import random

from flask import redirect, render_template, request, session
from functools import wraps


def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s


def loadbabel():
    with open('static/babel.txt', 'r') as file:
        data = file.read().replace('\n', ' ')
    length = len(data)
    # using text size 2vh, letter width is approx 1vw, so about 5000 chars should fill
    bglength = 8000
    start = random.randint(0,length - bglength) 
    return data[start:(start + bglength)]
    

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        response = requests.get(f"https://api.iextrading.com/1.0/stock/{urllib.parse.quote_plus(symbol)}/quote")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def message(message, title="Attention", code=200):
    """Render message to user."""
    return render_template("message.html", title=title, message=message, code=code, bgtext=loadbabel()), code


