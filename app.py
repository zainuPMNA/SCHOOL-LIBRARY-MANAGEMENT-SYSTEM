from flask import Flask, render_template, session, request, redirect, url_for
from config import Config
from models import db, User
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.students import students_bp
    from routes.staff import staff_bp
    from routes.books import books_bp
    from routes.circulation import circulation_bp
    from routes.backup import backup_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(circulation_bp, url_prefix='/circulation')
    app.register_blueprint(backup_bp, url_prefix='/backup')

    # Global login protection
    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'static']
        if request.endpoint and request.endpoint not in allowed_routes and 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))

    @app.context_processor
    def inject_user():
        role = session.get('role', '')
        is_chief = role in ['chief_librarian', 'admin']
        return dict(
            current_user_name=session.get('username'),
            current_user_role=role,
            is_chief_librarian=is_chief,
            user_role_display='Chief Librarian' if is_chief else 'Librarian'
        )

    # Create tables and seed default Chief Librarian user if empty
    with app.app_context():
        db.create_all()

        # Ensure circulation table schema supports both Student and Staff borrowing
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'circulation' in inspector.get_table_names():
                cols = {c['name']: c for c in inspector.get_columns('circulation')}
                needs_recreate = False
                if 'staff_id' not in cols or cols.get('student_id', {}).get('nullable') is False:
                    needs_recreate = True

                if needs_recreate:
                    with db.engine.connect() as conn:
                        conn.execute(text("PRAGMA foreign_keys=OFF;"))
                        conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS circulation_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                book_id INTEGER NOT NULL REFERENCES books(id),
                                student_id INTEGER REFERENCES students(id),
                                staff_id INTEGER REFERENCES staff(id),
                                issue_date DATETIME NOT NULL,
                                due_date DATETIME NOT NULL,
                                return_date DATETIME,
                                late_days INTEGER NOT NULL DEFAULT 0,
                                reason_for_delay TEXT,
                                fine_amount FLOAT NOT NULL DEFAULT 0.0,
                                fine_status VARCHAR(20) NOT NULL DEFAULT 'None',
                                renew_count INTEGER NOT NULL DEFAULT 0
                            );
                        """))
                        # Copy existing records
                        conn.execute(text("""
                            INSERT INTO circulation_new (id, book_id, student_id, issue_date, due_date, return_date, late_days, reason_for_delay, fine_amount, fine_status, renew_count)
                            SELECT id, book_id, student_id, issue_date, due_date, return_date, late_days, reason_for_delay, fine_amount, fine_status, renew_count FROM circulation;
                        """))
                        conn.execute(text("DROP TABLE circulation;"))
                        conn.execute(text("ALTER TABLE circulation_new RENAME TO circulation;"))
                        conn.execute(text("PRAGMA foreign_keys=ON;"))
                        conn.commit()
                    print("Successfully migrated circulation table schema for Staff & Student borrowing.")
                if 'books' in inspector.get_table_names():
                    book_cols = [c['name'] for c in inspector.get_columns('books')]
                    with db.engine.connect() as conn:
                        if 'call_number' not in book_cols:
                            conn.execute(text("ALTER TABLE books ADD COLUMN call_number VARCHAR(100);"))
                            print("Successfully added call_number column to books table.")
                        if 'book_number' not in book_cols:
                            conn.execute(text("ALTER TABLE books ADD COLUMN book_number VARCHAR(50);"))
                            print("Successfully added book_number column to books table.")
                        if 'shelf_number' not in book_cols:
                            conn.execute(text("ALTER TABLE books ADD COLUMN shelf_number VARCHAR(50);"))
                            print("Successfully added shelf_number column to books table.")
                        conn.commit()

            # Backfill call numbers, book numbers, and shelf numbers for any existing books
            from models import Book
            existing_books = Book.query.all()
            if existing_books:
                updated_count = 0
                for b in existing_books:
                    changed = False
                    if not b.call_number:
                        b.call_number = b.generate_default_call_number()
                        changed = True
                    if not b.book_number:
                        b.book_number = b.generate_default_book_number()
                        changed = True
                    if not b.shelf_number:
                        b.shelf_number = b.generate_default_shelf_number()
                        changed = True
                    if changed:
                        updated_count += 1
                if updated_count > 0:
                    db.session.commit()
                    print(f"Auto-generated classification metadata (call no, book no, shelf no) for {updated_count} books.")

        except Exception as e:
            print(f"Migration check note: {e}")

        if User.query.count() == 0:
            admin_user = User(username='admin', role='chief_librarian')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Seeded default Chief Librarian user (admin / admin123)")

        from models import Staff
        if Staff.query.count() == 0:
            sample_staff = [
                Staff(staff_id='EMP101', name='Dr. Rajesh Sharma', designation='Senior Teacher', department='Science (Physics)', phone='9876543210'),
                Staff(staff_id='EMP102', name='Mrs. Sunita Patil', designation='Head of Department (HOD)', department='English Literature', phone='9876543211'),
                Staff(staff_id='EMP103', name='Mr. Vikram Deshmukh', designation='Assistant Teacher', department='Mathematics', phone='9876543212'),
                Staff(staff_id='EMP104', name='Ms. Ananya Kulkarni', designation='Computer Teacher', department='Information Technology', phone='9876543213'),
                Staff(staff_id='EMP105', name='Mr. Suresh Jadhav', designation='Physical Education Teacher', department='Sports & Health', phone='9876543214'),
                Staff(staff_id='EMP106', name='Mrs. Priya Joshi', designation='Senior Teacher', department='Chemistry', phone='9876543215'),
                Staff(staff_id='EMP107', name='Mr. Amit Verma', designation='Assistant Teacher', department='Social Studies & History', phone='9876543216'),
                Staff(staff_id='EMP108', name='Mrs. Rekha Nair', designation='Primary Teacher', department='Languages (Hindi/Marathi)', phone='9876543217'),
                Staff(staff_id='EMP109', name='Mr. Sachin More', designation='Art & Fine Arts Teacher', department='Cultural & Arts', phone='9876543218'),
                Staff(staff_id='EMP110', name='Dr. Meena Shinde', designation='Head of Department (HOD)', department='Biology & Life Sciences', phone='9876543219'),
            ]
            db.session.add_all(sample_staff)
            db.session.commit()
            print("Seeded sample school teachers and staff records.")

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

