import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    # skip header row
    next(reader)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO book (isbn, title, author, pub_year) VALUES (:isbn, :title, :author, :pub_year)",
                    {"isbn": isbn, "title": title, "author": author, "pub_year": int(year)})
    db.commit()
    return(db.execute("SELECT COUNT(*) FROM book"))


if __name__== "__main__":
    main()