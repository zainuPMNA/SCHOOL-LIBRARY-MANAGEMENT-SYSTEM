from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from models import db, Book
import os
import urllib.request
import json

books_bp = Blueprint('books', __name__)

@books_bp.route('/download_template')
def download_template():
    from flask import Response
    csv_data = "Title,Author,ISBN,Call Number,Book Number,Shelf Number,Language,Subject,Category,Copies,Publisher,Year,Keywords,Price\n" \
               "To Kill a Mockingbird,Harper Lee,9780061120084,FIC LEE 1960,BK-001,Shelf F-1,English,Literature,Fiction,5,HarperPerennial,1960,classic novel,450.00\n" \
               "Brief Answers to the Big Questions,Stephen Hawking,9781473560567,SCI HAW 2018,BK-002,Shelf P-2,English,Science,Physics,3,John Murray,2018,science physics,599.00\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=books_import_template.csv"}
    )

@books_bp.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    if search_query:
        search = f"%{search_query}%"
        # Search by title, author, subject, category, publisher, isbn, call number, book number, shelf number, published year
        books = Book.query.filter(
            db.or_(
                Book.title.ilike(search),
                Book.author.ilike(search),
                Book.subject.ilike(search),
                Book.category.ilike(search),
                Book.publisher.ilike(search),
                Book.isbn.ilike(search),
                Book.call_number.ilike(search),
                Book.book_number.ilike(search),
                Book.shelf_number.ilike(search),
                db.cast(Book.published_year, db.String).ilike(search)
            )
        ).all()
    else:
        books = Book.query.all()
    return render_template('books/index.html', books=books, search_query=search_query)

def _suggest_call_number(category, author, published_year):
    cat = (category or "GEN").split(',')[0].strip()
    cat_code = ''.join([c for c in cat.upper() if c.isalnum()])[:4] or "GEN"
    auth_parts = (author or "UNK").strip().split()
    last_name = auth_parts[-1] if auth_parts else "UNK"
    auth_code = ''.join([c for c in last_name.upper() if c.isalnum()])[:3] or "UNK"
    year_code = str(published_year) if published_year else ""
    parts = [cat_code, auth_code]
    if year_code:
        parts.append(year_code)
    return " ".join(parts)

@books_bp.route('/isbn_lookup/<isbn>')
def isbn_lookup(isbn):
    import ssl
    clean_isbn = isbn.replace('-', '').replace(' ', '').strip()
    if not clean_isbn:
        return jsonify({'success': False, 'message': 'Please provide a valid ISBN.'})

    ctx = ssl._create_unverified_context()

    # Provider 1: Open Library API (Very reliable, no strict rate limits)
    url_ol = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&jscmd=data&format=json"
    try:
        req = urllib.request.Request(url_ol, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            key = f"ISBN:{clean_isbn}"
            if key in data and data[key]:
                book_info = data[key]
                title = book_info.get('title', '')
                authors = ", ".join([a.get('name', '') for a in book_info.get('authors', [])])
                publishers = ", ".join([p.get('name', '') for p in book_info.get('publishers', [])])
                pub_date = book_info.get('publish_date', '')
                published_year = int(pub_date[-4:]) if pub_date and pub_date[-4:].isdigit() else None
                cover_url = book_info.get('cover', {}).get('medium') or book_info.get('cover', {}).get('large') or ''
                subjects = ", ".join([s.get('name', '') for s in book_info.get('subjects', [])[:2]])
                cat_val = subjects or 'General'
                suggested_call = _suggest_call_number(cat_val, authors, published_year)

                return jsonify({
                    'success': True,
                    'title': title,
                    'author': authors,
                    'publisher': publishers,
                    'published_year': published_year,
                    'category': cat_val,
                    'cover_url': cover_url,
                    'isbn': clean_isbn,
                    'call_number': suggested_call
                })
    except Exception as e:
        print(f"Open Library Lookup Error: {e}")

    # Provider 2: Google Books API (Fallback)
    url_gb = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}"
    try:
        req = urllib.request.Request(url_gb, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('totalItems', 0) > 0:
                volume = data['items'][0]['volumeInfo']
                authors = ", ".join(volume.get('authors', []))
                publisher = volume.get('publisher', '')
                pub_date = volume.get('publishedDate', '')
                published_year = int(pub_date[:4]) if pub_date and pub_date[:4].isdigit() else None
                title = volume.get('title', '')
                image_links = volume.get('imageLinks', {})
                cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail') or ''
                if cover_url.startswith('http://'):
                    cover_url = cover_url.replace('http://', 'https://')
                categories = ", ".join(volume.get('categories', []))
                suggested_call = _suggest_call_number(categories, authors, published_year)
                
                return jsonify({
                    'success': True,
                    'title': title,
                    'author': authors,
                    'publisher': publisher,
                    'published_year': published_year,
                    'category': categories,
                    'cover_url': cover_url,
                    'isbn': clean_isbn,
                    'call_number': suggested_call
                })
    except Exception as e:
        print(f"Google Books Lookup Error: {e}")

    return jsonify({'success': False, 'message': 'Book details not found for this ISBN.'})



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
        isbn = request.form.get('isbn')
        call_number = request.form.get('call_number', '').strip()
        book_number = request.form.get('book_number', '').strip()
        shelf_number = request.form.get('shelf_number', '').strip()
        cover_url = request.form.get('cover_url')

        new_book = Book(
            title=title, author=author, language=language, subject=subject,
            category=category, copies=copies, publisher=publisher,
            published_year=published_year, keywords=keywords, price=price,
            isbn=isbn, call_number=call_number if call_number else None,
            book_number=book_number if book_number else None,
            shelf_number=shelf_number if shelf_number else None,
            cover_url=cover_url
        )
        if not new_book.call_number:
            new_book.call_number = new_book.generate_default_call_number()

        db.session.add(new_book)
        db.session.commit()

        # Set default book_number and shelf_number if not provided
        if not new_book.book_number:
            new_book.book_number = new_book.generate_default_book_number()
        if not new_book.shelf_number:
            new_book.shelf_number = new_book.generate_default_shelf_number()
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

                    call_num = str(row.get('call number', row.get('call_number', row.get('call no', row.get('callno', ''))))).strip()
                    book_num = str(row.get('book number', row.get('book_number', row.get('book no', row.get('bookno', row.get('accession no', '')))))).strip()
                    shelf_num = str(row.get('shelf number', row.get('shelf_number', row.get('shelf no', row.get('shelfno', row.get('rack no', '')))))).strip()
                    
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
                        price=price,
                        isbn=str(row.get('isbn', '')).strip(),
                        call_number=call_num if call_num else None,
                        book_number=book_num if book_num else None,
                        shelf_number=shelf_num if shelf_num else None,
                        cover_url=str(row.get('cover_url', row.get('cover', ''))).strip()
                    )
                    if not new_book.call_number:
                        new_book.call_number = new_book.generate_default_call_number()

                    db.session.add(new_book)
                    db.session.flush()

                    if not new_book.book_number:
                        new_book.book_number = new_book.generate_default_book_number()
                    if not new_book.shelf_number:
                        new_book.shelf_number = new_book.generate_default_shelf_number()

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
        book.isbn = request.form.get('isbn')
        call_number = request.form.get('call_number', '').strip()
        book_number = request.form.get('book_number', '').strip()
        shelf_number = request.form.get('shelf_number', '').strip()

        book.call_number = call_number if call_number else book.generate_default_call_number()
        book.book_number = book_number if book_number else book.generate_default_book_number()
        book.shelf_number = shelf_number if shelf_number else book.generate_default_shelf_number()

        book.cover_url = request.form.get('cover_url')
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

