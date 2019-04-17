import requests
import urllib.parse
import random

from flask import redirect, render_template, request, session
from functools import wraps


def loadbabel():
    """get block of text to use as page background"""
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


def message(message, title="Attention", code=200):
    """Render message to user."""
    return render_template("message.html", title=title, message=message, code=code, bgtext=loadbabel()), code


