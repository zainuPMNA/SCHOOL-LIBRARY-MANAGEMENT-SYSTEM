from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Book, Student, Staff, Circulation
from datetime import datetime, timedelta

circulation_bp = Blueprint('circulation', __name__)

DAILY_FINE_RATE = 5.0  # ₹5 per late day
MAX_ACTIVE_BOOKS_PER_STUDENT = 3
MAX_ACTIVE_BOOKS_PER_STAFF = 5

@circulation_bp.route('/')
def index():
    # Show active issues
    active_issues = Circulation.query.filter(Circulation.return_date == None).order_by(Circulation.issue_date.desc()).all()
    
    # Calculate late days dynamically for display
    now = datetime.utcnow()
    for issue in active_issues:
        if now > issue.due_date:
            issue.current_late_days = (now - issue.due_date).days
            issue.calculated_fine = issue.current_late_days * DAILY_FINE_RATE
        else:
            issue.current_late_days = 0
            issue.calculated_fine = 0.0

    # Also query unpaid fines history for management
    unpaid_fines = Circulation.query.filter(Circulation.fine_status == 'Unpaid').all()

    return render_template('circulation/index.html', active_issues=active_issues, unpaid_fines=unpaid_fines, daily_fine_rate=DAILY_FINE_RATE)

@circulation_bp.route('/issue', methods=['GET', 'POST'])
def issue():
    if request.method == 'POST':
        borrower_type = request.form.get('borrower_type', 'student')
        book_id = request.form.get('book_id')
        book = Book.query.get(book_id)

        if not book:
            flash("Invalid book selection.", "danger")
            return redirect(url_for('circulation.issue'))

        if book.copies <= 0:
            flash(f"Book '{book.title}' is currently out of stock.", "danger")
            return redirect(url_for('circulation.issue'))

        if borrower_type == 'staff':
            staff_id = request.form.get('staff_id')
            staff = Staff.query.get(staff_id)
            if not staff:
                flash("Invalid staff selection.", "danger")
                return redirect(url_for('circulation.issue'))

            # Check staff limit
            active_count = Circulation.query.filter_by(staff_id=staff.id, return_date=None).count()
            if active_count >= MAX_ACTIVE_BOOKS_PER_STAFF:
                flash(f"Limit Reached: Staff member {staff.name} already has {active_count} active book loans (Maximum allowed is {MAX_ACTIVE_BOOKS_PER_STAFF}).", "danger")
                return redirect(url_for('circulation.issue'))

            # Check staff unpaid fines
            unpaid_fine_exists = Circulation.query.filter_by(staff_id=staff.id, fine_status='Unpaid').first()
            if unpaid_fine_exists:
                flash(f"Blocked: Staff member {staff.name} has pending unpaid fines.", "danger")
                return redirect(url_for('circulation.issue'))

            due_date = datetime.utcnow() + timedelta(days=14)
            new_issue = Circulation(book_id=book.id, staff_id=staff.id, due_date=due_date)
            book.copies -= 1
            db.session.add(new_issue)
            db.session.commit()

            flash(f"Book '{book.title}' issued to Staff member {staff.name}. Due date is {due_date.strftime('%Y-%m-%d')}.", "success")
            return redirect(url_for('circulation.index'))

        else:
            student_id = request.form.get('student_id')
            student = Student.query.get(student_id)
            if not student:
                flash("Invalid student selection.", "danger")
                return redirect(url_for('circulation.issue'))

            # Check student limit
            active_count = Circulation.query.filter_by(student_id=student.id, return_date=None).count()
            if active_count >= MAX_ACTIVE_BOOKS_PER_STUDENT:
                flash(f"Limit Reached: Student {student.name} already has {active_count} active book loans (Maximum allowed is {MAX_ACTIVE_BOOKS_PER_STUDENT}).", "danger")
                return redirect(url_for('circulation.issue'))

            # Check student unpaid fines
            unpaid_fine_exists = Circulation.query.filter_by(student_id=student.id, fine_status='Unpaid').first()
            if unpaid_fine_exists:
                flash(f"Blocked: Student {student.name} has pending unpaid fines. Please settle fines before issuing new books.", "danger")
                return redirect(url_for('circulation.issue'))

            due_date = datetime.utcnow() + timedelta(days=7)
            new_issue = Circulation(book_id=book.id, student_id=student.id, due_date=due_date)
            book.copies -= 1
            db.session.add(new_issue)
            db.session.commit()
            
            flash(f"Book '{book.title}' issued to Student {student.name}. Due date is {due_date.strftime('%Y-%m-%d')}.", "success")
            return redirect(url_for('circulation.index'))
            
    students = Student.query.order_by(Student.name).all()
    staff_members = Staff.query.order_by(Staff.name).all()
    books = Book.query.filter(Book.copies > 0).order_by(Book.title).all()
    return render_template('circulation/issue.html', 
                           students=students, 
                           staff_members=staff_members, 
                           books=books, 
                           max_student_limit=MAX_ACTIVE_BOOKS_PER_STUDENT,
                           max_staff_limit=MAX_ACTIVE_BOOKS_PER_STAFF)

@circulation_bp.route('/renew/<int:issue_id>', methods=['POST'])
def renew_book(issue_id):
    issue = Circulation.query.get_or_404(issue_id)
    now = datetime.utcnow()

    if issue.return_date:
        flash("Cannot renew a book that has already been returned.", "warning")
        return redirect(url_for('circulation.index'))

    if now > issue.due_date:
        flash("Cannot renew an overdue book. Please return the book and settle any fines.", "danger")
        return redirect(url_for('circulation.index'))

    if issue.renew_count >= 2:
        flash("Maximum 2 renewals reached for this issue.", "warning")
        return redirect(url_for('circulation.index'))

    issue.due_date = issue.due_date + timedelta(days=7)
    issue.renew_count += 1
    db.session.commit()

    flash(f"Book loan renewed successfully! New due date is {issue.due_date.strftime('%Y-%m-%d')}.", "success")
    return redirect(url_for('circulation.index'))

@circulation_bp.route('/return/<int:issue_id>', methods=['GET', 'POST'])
def return_book(issue_id):
    issue = Circulation.query.get_or_404(issue_id)
    
    now = datetime.utcnow()
    late_days = 0
    if now > issue.due_date:
        late_days = (now - issue.due_date).days
    
    fine_amount = late_days * DAILY_FINE_RATE

    if request.method == 'POST':
        reason = request.form.get('reason_for_delay')
        fine_action = request.form.get('fine_action', 'None') # 'Pay', 'Unpaid', 'Waive', 'None'
        
        if late_days > 0 and not reason:
            flash("Reason for delay is required since the book is late.", "danger")
            return render_template('circulation/return.html', issue=issue, late_days=late_days, fine_amount=fine_amount)
            
        issue.return_date = now
        issue.late_days = late_days
        issue.reason_for_delay = reason
        issue.fine_amount = fine_amount
        
        if late_days > 0:
            if fine_action == 'Pay':
                issue.fine_status = 'Paid'
            elif fine_action == 'Waive':
                issue.fine_status = 'Waived'
            else:
                issue.fine_status = 'Unpaid'
        else:
            issue.fine_status = 'None'

        # Return copy to inventory
        book = Book.query.get(issue.book_id)
        book.copies += 1
        
        db.session.commit()
        flash(f"Book '{book.title}' returned successfully.", "success")
        return redirect(url_for('circulation.index'))
        
    return render_template('circulation/return.html', issue=issue, late_days=late_days, fine_amount=fine_amount)

@circulation_bp.route('/pay_fine/<int:issue_id>', methods=['POST'])
def pay_fine(issue_id):
    issue = Circulation.query.get_or_404(issue_id)
    issue.fine_status = 'Paid'
    db.session.commit()
    flash(f"Fine of ₹{issue.fine_amount:.2f} marked as PAID for {issue.borrower_name}.", "success")
    return redirect(url_for('circulation.index'))

@circulation_bp.route('/waive_fine/<int:issue_id>', methods=['POST'])
def waive_fine(issue_id):
    issue = Circulation.query.get_or_404(issue_id)
    issue.fine_status = 'Waived'
    db.session.commit()
    flash(f"Fine of ₹{issue.fine_amount:.2f} WAIVED for {issue.borrower_name}.", "info")
    return redirect(url_for('circulation.index'))

