from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    division = db.Column(db.String(50), nullable=False)
    
    # Relationship to Circulation
    circulations = db.relationship('Circulation', backref='student', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.roll_no} - {self.name}>"

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    copies = db.Column(db.Integer, nullable=False, default=1)
    publisher = db.Column(db.String(255), nullable=True)
    published_year = db.Column(db.Integer, nullable=True)
    keywords = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)

    # Relationship to Circulation
    circulations = db.relationship('Circulation', backref='book', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book {self.title}>"

class Circulation(db.Model):
    __tablename__ = 'circulation'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    late_days = db.Column(db.Integer, nullable=False, default=0)
    reason_for_delay = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Circulation Book:{self.book_id} Student:{self.student_id}>"
