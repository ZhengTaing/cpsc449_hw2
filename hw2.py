from fastapi import Depends, FastAPI, HTTPException                 # Import FastAPI and related modules.
from pydantic import BaseModel                                      # Import Pydantic BaseModel for input validation.
from typing import List                                             # Import List for type hinting.
from sqlalchemy import text,create_engine, Column, Integer, String       # SQLAlchemy utilities for ORM mapping.
from sqlalchemy.ext.declarative import declarative_base             # Base class for SQLAlchemy models.
from sqlalchemy.orm import sessionmaker, Session                    # Session and sessionmaker for database operations.


# SQLAlchemy configuration
DATABASE_URL = "mysql://user1:zzzz@localhost/book_management" 

# create SQLAlchemy engine and sessionmaker
engine = create_engine(DATABASE_URL, connect_args={"charset": "utf8mb4"})  # Create engine without SSL.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Session factory for managing DB sessions.

# base class for models
Base = declarative_base()  # Base class for defining SQLAlchemy models.

# data model for a book (SQLAlchemy)
class Book(Base):
    __tablename__ = "books"                                         #table name in the database  
    id = Column(Integer, primary_key=True, index=True)              #id column
    title = Column(String(255), nullable=False)                     #title column
    author = Column(String(255), nullable=False)                    #author column
    year_published = Column(Integer, nullable=False)                #year_published column
    isbn = Column(String(17), unique=True, nullable=False)          #isbn column; Allows for both ISBN-10 and ISBN-13 with or without hyphens

# created an instance of FASTAPI
app = FastAPI()

#databe session handling
def get_db():
    db = SessionLocal()         #establish a new session
    try:
        yield db                #yield session to caller
    finally:
        db.close()              #closes the session after use

# data model for a book (Pydantic - validates input data during CRUD operations)
class BookCreate(BaseModel):
    title: str                  #title field
    author: str                 #author field
    year_published: int         #year_published field
    isbn: str                   #isbn field
    
# pydantic schema for output data which include the book(item) id    
# inherits from BookCreate 
class BookOut(BookCreate):
    id:int                      #id field
    
    class Config:
        from_attributes = True         #converts ORM objects to dict; allows pydantic to work directly with SQLAlchemy


# initialize the database and automatically create the 'books' table in the database
Base.metadata.create_all(bind=engine)

#Routes

# [GET] FASTAPI decorator
@app.get("/books", response_model=List[BookOut])                        #endpoints to return(BookOut) all books in list format
def get_books(db:Session = Depends(get_db)):
    books = db.query(Book).all()                                        #retrieve all books from database
    return books                                                        #returns the book in list format

# [GET(specific)] FASTAPI decorator
@app.get("/books/{book_id}", response_model=BookOut)                    #endpoints to return specific book
def get_books(book_id:int,db:Session = Depends(get_db)):                #has book_id as parameter
    book = db.query(Book).filter(Book.id == book_id).first()            #checks for matching book_id and filter and retrieve info when matched
    if not book:
        raise HTTPException(status_code=404, detail= "Book not found")  #raise 404 if no book is found
    return book                                                         #returns the book data

# [POST] FASTAPI decorator
@app.post("/books", response_model=BookOut)                             #endpoints to accepts data input, returns the created book in database
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(
        title = book.title,                                             #set title
        author = book.author,                                           #set author
        year_published = book.year_published,                           #set year_published    
        isbn = book.isbn                                                #set isbn
    )
    db.add(db_book)                                                     #add new book to session
    db.commit()                                                         #commit session to save changes
    db.refresh(db_book)                                                 # get updated data with refresh
    return db_book

# [PUT] FASTAPI decorator
@app.put("/books/{book_id}", response_model=BookOut)                                    #endpoints to return updated book   
def update_book(book_id:int, updated_book: BookCreate, db: Session = Depends(get_db)):  
    db_book = db.query(Book).filter(Book.id == book_id).first()                         #query books by its ID
    if not db_book:                                                                     #raise 404 error if no book is found
        raise HTTPException(status_code=404, detail="Book not found")
    
    db_book.title = updated_book.title                                                  #update title                                                   
    db_book.author = updated_book.author                                                 #update author
    db_book.year_published = updated_book.year_published                                 #update year_published
    db_book.isbn = updated_book.isbn                                                     #update isbn    
    
    db.commit()                                                                         #commit session to save changes
    db.refresh(db_book)                                                                 #get updated data with refresh 
    return db_book
    

# [DELETE] FASTAPI decorator
@app.delete("/books/{book_id}")                                                         #endpoints to delete book by its ID
def delete_student(book_id: int, db: Session = Depends(get_db)):                        
    db_book = db.query(Book).filter(Book.id == book_id).first()                         #query database by book ID
    if not db_book:             
        raise HTTPException(status_code=404, detail="Book not found")                   #raise 404 error if book is not found 
    db.delete(db_book)                                                                  #delete book from session
    db.commit()                                                                         #commit session to save changes  
    
    total_books = db.query(Book).count() 
    if total_books ==0:
        db.execute(text("ALTER TABLE books AUTO_INCREMENT = 1;"))                       #add query to reset id back to 1 if table is empty
        db.commit()                                                                     #commit session to save changes  
    return{"message": f"Book with ID {book_id} have been deleted"}                      #return success message 

