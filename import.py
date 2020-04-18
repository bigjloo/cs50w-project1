import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def create_tables():
    db.execute("CREATE TABLE books(id SERIAL PRIMARY KEY,isbn_id VARCHAR NOT NULL,author VARCHAR NOT NULL,title VARCHAR NOT NULL,year INT NOT NULL)")
    db.execute(
        "CREATE TABLE users(id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL")
    db.execute("CREATE TABLE reviews(id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users, book_id INTEGER REFERENCES books, rating INTEGER NOT NULL, review TEXT")
    db.commit()


def main():
    create_tables()
    with open("books.csv", "r") as file:
        books = csv.DictReader(file)

        for book in books:
            isbn = book["isbn"]
            year = int(book["year"])
            author = book["author"]
            title = book["title"]
            db.execute("INSERT INTO books (isbn_id, author, title, year) VALUES (:isbn_id, :author, :title, :year)",
                       {"isbn_id": isbn, "author": author, "title": title, "year": year})
        db.commit()


if __name__ == "__main__":
    main()
