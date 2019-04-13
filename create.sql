/* Create tables by running this file:
heroku pg:psql --app etoitau-library < create.sql */

/* note username input field is limited in html to 16 char */
CREATE TABLE card (
    user_id SERIAL PRIMARY KEY,
    username CHAR(16) NOT NULL UNIQUE,
    pass_hash CHAR(128) NOT NULL
);

/* not ISBN numbers used to be 10 digits, now 13, let's say 16 
dates in csv to import are just four digit year */
CREATE TABLE book (
    book_id SERIAL PRIMARY KEY,
    isbn CHAR(16),
    title VARCHAR,
    author VARCHAR,
    pub_year SMALLINT
);

CREATE TABLE review (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES card,
    book_id INTEGER REFERENCES book,
    rating SMALLINT,
    review TEXT
);


