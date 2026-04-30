from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Book, Student, Circulation
from datetime import datetime, timedelta

circulation_bp = Blueprint('circulation', __name__)

@circulation_bp.route('/')
def index():
    # Show active issues
    active_issues = Circulation.query.filter(Circulation.return_date == None).all()
    # Calculate late days dynamically for display
    now = datetime.utcnow()
    for issue in active_issues:
        if now > issue.due_date:
            issue.current_late_days = (now - issue.due_date).days
        else:
            issue.current_late_days = 0
            
    return render_template('circulation/index.html', active_issues=active_issues)

@circulation_bp.route('/issue', methods=['GET', 'POST'])
def issue():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        book_id = request.form.get('book_id')
        
        book = Book.query.get(book_id)
        if book and book.copies > 0:
            due_date = datetime.utcnow() + timedelta(days=7)
            new_issue = Circulation(book_id=book_id, student_id=student_id, due_date=due_date)
            book.copies -= 1
            db.session.add(new_issue)
            db.session.commit()
            flash(f"Book '{book.title}' issued successfully. Due date is {due_date.strftime('%Y-%m-%d')}.", "success")
            return redirect(url_for('circulation.index'))
        else:
            flash("Book is out of stock or invalid selection.", "danger")
            
    students = Student.query.all()
    books = Book.query.filter(Book.copies > 0).all()
    return render_template('circulation/issue.html', students=students, books=books)

@circulation_bp.route('/return/<int:issue_id>', methods=['GET', 'POST'])
def return_book(issue_id):
    issue = Circulation.query.get_or_404(issue_id)
    
    now = datetime.utcnow()
    late_days = 0
    if now > issue.due_date:
        late_days = (now - issue.due_date).days

    if request.method == 'POST':
        reason = request.form.get('reason_for_delay')
        
        if late_days > 0 and not reason:
            flash("Reason for delay is required since the book is late.", "danger")
            return render_template('circulation/return.html', issue=issue, late_days=late_days)
            
        issue.return_date = now
        issue.late_days = late_days
        issue.reason_for_delay = reason
        
        # Increase book copies
        book = Book.query.get(issue.book_id)
        book.copies += 1
        
        db.session.commit()
        flash("Book returned successfully.", "success")
        return redirect(url_for('circulation.index'))
        
    return render_template('circulation/return.html', issue=issue, late_days=late_days)
