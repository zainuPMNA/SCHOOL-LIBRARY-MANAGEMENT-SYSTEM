from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from models import db, Student, Book, Circulation
import os
import zipfile
import io
from datetime import datetime

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/')
def index():
    return render_template('backup/index.html')

@backup_bp.route('/export')
def export_data():
    import csv
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Export Students
        students = Student.query.all()
        sf = io.StringIO()
        if students:
            writer = csv.DictWriter(sf, fieldnames=['id', 'roll_no', 'name', 'class_name', 'division'])
            writer.writeheader()
            for s in students:
                writer.writerow({'id': s.id, 'roll_no': s.roll_no, 'name': s.name, 'class_name': s.class_name, 'division': s.division})
        zf.writestr('students.csv', sf.getvalue())
        
        # Export Books
        books = Book.query.all()
        bf = io.StringIO()
        if books:
            writer = csv.DictWriter(bf, fieldnames=['id', 'title', 'author', 'language', 'subject', 'category', 'copies', 'publisher', 'published_year', 'keywords', 'price'])
            writer.writeheader()
            for b in books:
                writer.writerow({'id': b.id, 'title': b.title, 'author': b.author, 'language': b.language, 'subject': b.subject, 'category': b.category, 'copies': b.copies, 'publisher': b.publisher, 'published_year': b.published_year, 'keywords': b.keywords, 'price': b.price})
        zf.writestr('books.csv', bf.getvalue())
        
        # Export Circulation
        circulation = Circulation.query.all()
        cf = io.StringIO()
        if circulation:
            writer = csv.DictWriter(cf, fieldnames=['id', 'book_id', 'student_id', 'issue_date', 'due_date', 'return_date', 'late_days', 'reason_for_delay'])
            writer.writeheader()
            for c in circulation:
                writer.writerow({'id': c.id, 'book_id': c.book_id, 'student_id': c.student_id, 'issue_date': c.issue_date, 'due_date': c.due_date, 'return_date': c.return_date, 'late_days': c.late_days, 'reason_for_delay': c.reason_for_delay})
        zf.writestr('circulation.csv', cf.getvalue())
        
    memory_file.seek(0)
    filename = f"library_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )

@backup_bp.route('/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('backup.index'))
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('backup.index'))
        
    if file and file.filename.endswith('.zip'):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            import csv
            with zipfile.ZipFile(filepath, 'r') as zf:
                Circulation.query.delete()
                Student.query.delete()
                Book.query.delete()
                db.session.commit()
                
                if 'students.csv' in zf.namelist():
                    with zf.open('students.csv') as f:
                        text_file = io.TextIOWrapper(f, encoding='utf-8')
                        reader = csv.DictReader(text_file)
                        for row in reader:
                            new_student = Student(id=row.get('id'), roll_no=row.get('roll_no'), name=row.get('name'), class_name=row.get('class_name'), division=row.get('division'))
                            db.session.add(new_student)
                        db.session.commit()
                        
                if 'books.csv' in zf.namelist():
                    with zf.open('books.csv') as f:
                        text_file = io.TextIOWrapper(f, encoding='utf-8')
                        reader = csv.DictReader(text_file)
                        for row in reader:
                            new_book = Book(id=row.get('id'), title=row.get('title'), author=row.get('author'), language=row.get('language'), subject=row.get('subject'), category=row.get('category'), copies=row.get('copies'), publisher=row.get('publisher'), published_year=row.get('published_year') if row.get('published_year') else None, keywords=row.get('keywords'), price=row.get('price'))
                            db.session.add(new_book)
                        db.session.commit()
                        
                if 'circulation.csv' in zf.namelist():
                    with zf.open('circulation.csv') as f:
                        text_file = io.TextIOWrapper(f, encoding='utf-8')
                        reader = csv.DictReader(text_file)
                        for row in reader:
                            from datetime import datetime
                            issue_d = datetime.strptime(row.get('issue_date').split('.')[0], '%Y-%m-%d %H:%M:%S') if row.get('issue_date') else datetime.utcnow()
                            due_d = datetime.strptime(row.get('due_date').split('.')[0], '%Y-%m-%d %H:%M:%S') if row.get('due_date') else datetime.utcnow()
                            ret_d = datetime.strptime(row.get('return_date').split('.')[0], '%Y-%m-%d %H:%M:%S') if row.get('return_date') else None
                            new_circ = Circulation(id=row.get('id'), book_id=row.get('book_id'), student_id=row.get('student_id'), issue_date=issue_d, due_date=due_d, return_date=ret_d, late_days=row.get('late_days', 0), reason_for_delay=row.get('reason_for_delay'))
                            db.session.add(new_circ)
                        db.session.commit()
                        
            flash("Database restored successfully from backup.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error during restore: {str(e)}", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        flash("Invalid file format. Please upload a ZIP backup file.", "danger")
        
    return redirect(url_for('backup.index'))
