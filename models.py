from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='admin') # admin or librarian
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_chief_librarian(self):
        return self.role in ['chief_librarian', 'admin']

    @property
    def role_display(self):
        return 'Chief Librarian' if self.is_chief_librarian() else 'Librarian'

    def __repr__(self):
        return f"<User {self.username}>"

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

class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Circulation
    circulations = db.relationship('Circulation', backref='staff', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Staff {self.staff_id} - {self.name}>"

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
    isbn = db.Column(db.String(50), nullable=True)
    call_number = db.Column(db.String(100), nullable=True)
    book_number = db.Column(db.String(50), nullable=True)
    shelf_number = db.Column(db.String(50), nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)

    # Relationship to Circulation
    circulations = db.relationship('Circulation', backref='book', lazy=True, cascade="all, delete-orphan")

    def generate_default_call_number(self):
        cat = (self.category or self.subject or "GEN").strip()
        cat_code = ''.join([c for c in cat.upper() if c.isalnum()])[:4] or "GEN"

        auth_parts = (self.author or "UNK").strip().split()
        last_name = auth_parts[-1] if auth_parts else "UNK"
        auth_code = ''.join([c for c in last_name.upper() if c.isalnum()])[:3] or "UNK"

        year_code = str(self.published_year) if self.published_year else (str(self.id) if self.id else "")

        parts = [cat_code, auth_code]
        if year_code:
            parts.append(year_code)
        return " ".join(parts)

    def generate_default_book_number(self):
        num_id = self.id or 1
        return f"BK-{num_id:03d}"

    def generate_default_shelf_number(self):
        cat_first = (self.category or self.subject or "A")[0].upper()
        if not cat_first.isalpha():
            cat_first = "A"
        shelf_num = (self.id % 5) + 1 if self.id else 1
        return f"Shelf {cat_first}-{shelf_num}"

    def __repr__(self):
        return f"<Book {self.title}>"

class Circulation(db.Model):
    __tablename__ = 'circulation'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    late_days = db.Column(db.Integer, nullable=False, default=0)
    reason_for_delay = db.Column(db.Text, nullable=True)
    fine_amount = db.Column(db.Float, nullable=False, default=0.0)
    fine_status = db.Column(db.String(20), nullable=False, default='None') # None, Unpaid, Paid, Waived
    renew_count = db.Column(db.Integer, nullable=False, default=0)

    @property
    def borrower_type(self):
        return 'Staff' if self.staff_id else 'Student'

    @property
    def borrower_name(self):
        if self.staff:
            return self.staff.name
        elif self.student:
            return self.student.name
        return "Unknown"

    @property
    def borrower_info(self):
        if self.staff:
            return f"Staff: {self.staff.name} ({self.staff.designation}, {self.staff.department})"
        elif self.student:
            return f"Student: {self.student.name} (Class {self.student.class_name}-{self.student.division})"
        return "Unknown"

    def __repr__(self):
        return f"<Circulation Book:{self.book_id} Borrower:{self.borrower_name}>"

