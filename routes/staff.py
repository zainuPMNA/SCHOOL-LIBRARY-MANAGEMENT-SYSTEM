from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Response
from models import db, Staff
import os
import csv

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/download_template')
def download_template():
    csv_data = "Staff ID,Name,Designation,Department,Phone\n" \
               "EMP001,Dr. Rajesh Sharma,Teacher,Science,9876543210\n" \
               "EMP002,Sunita Patil,HOD,English,9876543211\n" \
               "EMP003,Vikram Deshmukh,Lab Assistant,Computer Science,9876543212\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=staff_import_template.csv"}
    )

@staff_bp.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    if search_query:
        search = f"%{search_query}%"
        staff_members = Staff.query.filter(
            db.or_(
                Staff.staff_id.ilike(search),
                Staff.name.ilike(search),
                Staff.designation.ilike(search),
                Staff.department.ilike(search),
                Staff.phone.ilike(search)
            )
        ).order_by(Staff.name).all()
    else:
        staff_members = Staff.query.order_by(Staff.name).all()
    return render_template('staff/index.html', staff_members=staff_members, search_query=search_query)

@staff_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        staff_id = request.form.get('staff_id', '').strip()
        name = request.form.get('name', '').strip()
        designation = request.form.get('designation', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()

        if not all([staff_id, name, designation, department]):
            flash("Staff ID, Name, Designation, and Department are required.", "danger")
            return redirect(url_for('staff.add'))

        existing = Staff.query.filter_by(staff_id=staff_id).first()
        if existing:
            flash(f"Staff Member with ID '{staff_id}' already exists.", "warning")
            return redirect(url_for('staff.add'))

        new_staff = Staff(
            staff_id=staff_id,
            name=name,
            designation=designation,
            department=department,
            phone=phone
        )
        db.session.add(new_staff)
        db.session.commit()
        flash(f"Staff member '{name}' added successfully!", "success")
        return redirect(url_for('staff.index'))

    return render_template('staff/add.html')

@staff_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    staff_member = Staff.query.get_or_404(id)
    if request.method == 'POST':
        staff_id = request.form.get('staff_id', '').strip()
        name = request.form.get('name', '').strip()
        designation = request.form.get('designation', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()

        if not all([staff_id, name, designation, department]):
            flash("Staff ID, Name, Designation, and Department are required.", "danger")
            return redirect(url_for('staff.edit', id=id))

        existing = Staff.query.filter(Staff.staff_id == staff_id, Staff.id != id).first()
        if existing:
            flash(f"Staff ID '{staff_id}' is already assigned to another staff member.", "warning")
            return redirect(url_for('staff.edit', id=id))

        staff_member.staff_id = staff_id
        staff_member.name = name
        staff_member.designation = designation
        staff_member.department = department
        staff_member.phone = phone
        db.session.commit()

        flash(f"Staff member '{name}' updated successfully!", "success")
        return redirect(url_for('staff.index'))

    return render_template('staff/edit.html', staff=staff_member)

@staff_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    staff_member = Staff.query.get_or_404(id)
    name = staff_member.name
    db.session.delete(staff_member)
    db.session.commit()
    flash(f"Staff member '{name}' deleted successfully.", "info")
    return redirect(url_for('staff.index'))

@staff_bp.route('/import', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('staff.index'))
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('staff.index'))

    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            added_count = 0
            skipped_count = 0
            with open(filepath, newline='', encoding='utf-8-sig', errors='replace') as csvfile:
                reader = csv.DictReader(csvfile)
                for index, raw_row in enumerate(reader):
                    row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
                    
                    staff_id = str(row.get('staff id', row.get('staff_id', row.get('emp_no', row.get('emp id', ''))))).strip()
                    name = str(row.get('name', row.get('staff name', ''))).strip()
                    designation = str(row.get('designation', row.get('role', 'Teacher'))).strip()
                    department = str(row.get('department', row.get('dept', 'General'))).strip()
                    phone = str(row.get('phone', row.get('mobile', ''))).strip()

                    if not all([staff_id, name]):
                        skipped_count += 1
                        continue

                    existing = Staff.query.filter_by(staff_id=staff_id).first()
                    if existing:
                        skipped_count += 1
                        continue

                    new_staff = Staff(
                        staff_id=staff_id,
                        name=name,
                        designation=designation or 'Teacher',
                        department=department or 'General',
                        phone=phone
                    )
                    db.session.add(new_staff)
                    added_count += 1

            db.session.commit()
            if added_count > 0:
                flash(f"Successfully imported {added_count} staff members.", "success")
            elif skipped_count > 0:
                flash(f"Import complete. {skipped_count} rows were skipped due to duplicate Staff ID or missing required data.", "warning")
            else:
                flash("No valid rows were found in the uploaded file.", "warning")
        except Exception as e:
            flash(f"Error processing CSV: {str(e)}", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        flash("Invalid file format. Please upload a CSV file.", "danger")

    return redirect(url_for('staff.index'))
