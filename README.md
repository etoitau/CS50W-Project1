# CS50W - Project 1
Web Programming with Python and JavaScript
## Etoitau Libaray

### Short Writeup - from specifications
In this project, you’ll build a book review website. Users will be able to register for your website and then log in using their username and password. Once they log in, they will be able to search for books, leave reviews for individual books, and see the reviews made by other people. You’ll also use the a third-party API by Goodreads, another book review website, to pull in ratings from a broader audience. Finally, users will be able to query for book details and book reviews programmatically via your website’s API.

### What's in each file
    
    .
    ├── static                  # static files
    │   ├── babel.txt           # text of 'The Library of Babel' by Borges. Blocks of this are used as the background
    │   ├── dark-honeycomb.png  # navbar background
    │   ├── favicon.ico         # icon
    │   └── styles.css          # stylesheet
    ├── templates               # html templates
    │   ├── book.html           # book info and review page
    │   ├── index.html          # default page if logged in. Search happens here
    │   ├── layout.html         # other pages extend this. Navbar, text background, etc
    │   ├── login.html          # login form
    │   ├── message.html        # for serving error (or other) messages
    │   ├── register.html       # form to register for new account
    │   └── reviews.html        # page with all of user's reviews
    ├── .gitignore              # exclude files only applicable to my machine
    ├── readme.md               # this
    ├── application.py          # main application file with routes defined
    ├── books.csv               # book data provided for project
    ├── create.sql              # run this to create necessary tables
    ├── helpers.py              # some functions that application.py imports and uses (get text for background, serve error messages, etc)
    ├── import.py               # run to put books.csv into database
    └── requirements.txt        # necessary to install these to run app

### Other info

https://github.com/etoitau/CS50W-Project1
https://youtu.be/kfyGZ5ltCzE