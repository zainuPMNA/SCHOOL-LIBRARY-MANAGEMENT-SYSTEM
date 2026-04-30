from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Book
import os

books_bp = Blueprint('books', __name__)

@books_bp.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    if search_query:
        search = f"%{search_query}%"
        # Search by title, subject, category, publisher, published year
        books = Book.query.filter(
            db.or_(
                Book.title.ilike(search),
                Book.subject.ilike(search),
                Book.category.ilike(search),
                Book.publisher.ilike(search),
                db.cast(Book.published_year, db.String).ilike(search)
            )
        ).all()
    else:
        books = Book.query.all()
    return render_template('books/index.html', books=books, search_query=search_query)

@books_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        language = request.form.get('language')
        subject = request.form.get('subject')
        category = request.form.get('category')
        copies = request.form.get('copies', type=int)
        publisher = request.form.get('publisher')
        published_year = request.form.get('published_year', type=int)
        keywords = request.form.get('keywords')
        price = request.form.get('price', type=float)

        new_book = Book(
            title=title, author=author, language=language, subject=subject,
            category=category, copies=copies, publisher=publisher,
            published_year=published_year, keywords=keywords, price=price
        )
        db.session.add(new_book)
        db.session.commit()
        flash("Book added successfully!", "success")
        return redirect(url_for('books.index'))
            
    return render_template('books/add.html')

@books_bp.route('/import', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('books.index'))
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('books.index'))
    
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
                    
                    title = str(row.get('book title', row.get('title', ''))).strip()
                    if not title or title.lower() == 'nan':
                        missing_cols_count += 1
                        continue
                    
                    try:
                        price = float(row.get('price', 0.0))
                    except ValueError:
                        price = 0.0
                        
                    try:
                        copies_str = str(row.get('no. of copies', row.get('copies', '1'))).strip()
                        copies = int(copies_str) if copies_str else 1
                    except ValueError:
                        copies = 1
                        
                    year_val = str(row.get('published year', row.get('year', ''))).strip()
                    try:
                        pub_year = int(year_val) if year_val else None
                    except ValueError:
                        pub_year = None
                    
                    new_book = Book(
                        title=title,
                        author=str(row.get('author name', row.get('author', ''))).strip(),
                        language=str(row.get('language', '')).strip(),
                        subject=str(row.get('subject', '')).strip(),
                        category=str(row.get('category', '')).strip(),
                        copies=copies,
                        publisher=str(row.get('publisher', '')).strip(),
                        published_year=pub_year,
                        keywords=str(row.get('keywords', '')).strip(),
                        price=price
                    )
                    db.session.add(new_book)
                    added_count += 1
            
            db.session.commit()
            if added_count > 0:
                flash(f"Successfully imported {added_count} books.", "success")
            elif missing_cols_count > 0:
                flash(f"Failed to import. {missing_cols_count} rows were skipped due to missing Title.", "warning")
            else:
                flash("No valid rows were found.", "warning")
        except Exception as e:
            print(f"CSV Import Error: {str(e)}")
            flash(f"Error processing CSV: {str(e)}", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
    else:
        flash("Invalid file format. Please upload a CSV.", "danger")
        
    return redirect(url_for('books.index'))

@books_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.language = request.form.get('language')
        book.subject = request.form.get('subject')
        book.category = request.form.get('category')
        book.copies = request.form.get('copies', type=int)
        book.publisher = request.form.get('publisher')
        book.published_year = request.form.get('published_year', type=int)
        book.keywords = request.form.get('keywords')
        book.price = request.form.get('price', type=float)
        db.session.commit()
        flash("Book updated successfully!", "success")
        return redirect(url_for('books.index'))
    return render_template('books/edit.html', book=book)

@books_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully!", "success")
    return redirect(url_for('books.index'))
