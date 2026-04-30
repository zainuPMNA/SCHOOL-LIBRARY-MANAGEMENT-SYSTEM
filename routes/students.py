from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Student
import os

students_bp = Blueprint('students', __name__)

@students_bp.route('/')
def index():
    students = Student.query.all()
    return render_template('students/index.html', students=students)

@students_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        name = request.form.get('name')
        class_name = request.form.get('class_name')
        division = request.form.get('division')

        existing = Student.query.filter_by(name=name, roll_no=roll_no, class_name=class_name, division=division).first()
        if existing:
            flash("It is repeated", "danger")
        else:
            new_student = Student(roll_no=roll_no, name=name, class_name=class_name, division=division)
            db.session.add(new_student)
            db.session.commit()
            flash("Student added successfully!", "success")
            return redirect(url_for('students.index'))
            
    return render_template('students/add.html')

@students_bp.route('/import', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('students.index'))
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('students.index'))
    
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            import csv
            added_count = 0
            missing_cols_count = 0
            with open(filepath, newline='', encoding='utf-8-sig', errors='replace') as csvfile:
                reader = csv.DictReader(csvfile)
                for index, raw_row in enumerate(reader):
                    row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
                    
                    roll_no = str(row.get('roll no', row.get('roll_no', row.get('roll', '')))).strip()
                    name = str(row.get('name', row.get('student name', ''))).strip()
                    class_name = str(row.get('class', row.get('class name', ''))).strip()
                    division = str(row.get('division', row.get('div', ''))).strip()
                    
                    if not all([roll_no, name, class_name, division]):
                        missing_cols_count += 1
                        continue
                    
                    existing = Student.query.filter_by(name=name, roll_no=roll_no, class_name=class_name, division=division).first()
                    if existing:
                        flash(f"Row {index+2} (Roll No: {roll_no}) is repeated. Skipped.", "warning")
                    else:
                        new_student = Student(roll_no=roll_no, name=name, class_name=class_name, division=division)
                        db.session.add(new_student)
                        added_count += 1
            
            db.session.commit()
            if added_count > 0:
                flash(f"Successfully imported {added_count} students.", "success")
            elif missing_cols_count > 0:
                flash(f"Failed to import. {missing_cols_count} rows were skipped due to missing data in one of the required columns (Roll No, Name, Class, Division).", "warning")
            else:
                flash("No valid rows were found or all were duplicates.", "warning")
        except Exception as e:
            print(f"CSV Import Error: {str(e)}")
            flash(f"Error processing CSV: {str(e)}", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
    else:
        flash("Invalid file format. Please upload a CSV.", "danger")
        
    return redirect(url_for('students.index'))

@students_bp.route('/promote', methods=['GET', 'POST'])
def promote():
    source_class = request.args.get('source_class')
    classes = db.session.query(Student.class_name).distinct().all()
    classes = [c[0] for c in classes]

    students_to_promote = []
    if source_class:
        students_to_promote = Student.query.filter_by(class_name=source_class).all()

    if request.method == 'POST':
        action = request.form.get('action')
        selected_ids = request.form.getlist('student_ids')
        
        if not selected_ids:
            flash("No students selected.", "warning")
            return redirect(url_for('students.promote', source_class=source_class))
            
        if action == 'promote':
            target_class = request.form.get('target_class')
            if not target_class:
                flash("Please provide a target class to promote to.", "danger")
                return redirect(url_for('students.promote', source_class=source_class))
                
            students = Student.query.filter(Student.id.in_(selected_ids)).all()
            for s in students:
                s.class_name = target_class
            db.session.commit()
            flash(f"Successfully promoted {len(students)} students to {target_class}.", "success")
            
        elif action == 'delete':
            students = Student.query.filter(Student.id.in_(selected_ids)).all()
            for s in students:
                db.session.delete(s)
            db.session.commit()
            flash(f"Successfully deleted {len(students)} students.", "success")
            
        return redirect(url_for('students.promote', source_class=source_class))
        
    return render_template('students/promote.html', classes=classes, source_class=source_class, students=students_to_promote)

@students_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.roll_no = request.form.get('roll_no')
        student.name = request.form.get('name')
        student.class_name = request.form.get('class_name')
        student.division = request.form.get('division')
        db.session.commit()
        flash("Student updated successfully!", "success")
        return redirect(url_for('students.index'))
    return render_template('students/edit.html', student=student)

@students_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for('students.index'))
