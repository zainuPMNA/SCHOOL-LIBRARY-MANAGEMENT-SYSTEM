from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db, User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def chief_librarian_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        if session.get('role') not in ['chief_librarian', 'admin']:
            flash("Access denied. Only Chief Librarian can perform this action.", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/accounts', methods=['GET', 'POST'])
@chief_librarian_required
def accounts():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'librarian').strip()

        if not username or not password:
            flash("Username and Password are required.", "danger")
            return redirect(url_for('auth.accounts'))

        if role not in ['librarian', 'chief_librarian']:
            role = 'librarian'

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f"User with username '{username}' already exists.", "warning")
            return redirect(url_for('auth.accounts'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"Account for '{username}' ({'Chief Librarian' if role == 'chief_librarian' else 'Librarian'}) created successfully!", "success")
        return redirect(url_for('auth.accounts'))

    all_users = User.query.order_by(User.id.asc()).all()
    return render_template('auth/accounts.html', users=all_users)

@auth_bp.route('/accounts/<int:user_id>/edit', methods=['POST'])
@chief_librarian_required
def edit_account(user_id):
    target_user = User.query.get_or_404(user_id)
    new_username = request.form.get('username', '').strip()
    new_password = request.form.get('new_password', '').strip()
    new_role = request.form.get('role', 'librarian').strip()

    if not new_username:
        flash("Username cannot be empty.", "danger")
        return redirect(url_for('auth.accounts'))

    # Check if username is taken by another user
    existing = User.query.filter(User.username == new_username, User.id != user_id).first()
    if existing:
        flash(f"Username '{new_username}' is already in use by another account.", "danger")
        return redirect(url_for('auth.accounts'))

    target_user.username = new_username

    if new_role in ['librarian', 'chief_librarian']:
        target_user.role = new_role

    if new_password:
        target_user.set_password(new_password)

    db.session.commit()

    # Update session if current user edited their own profile
    if target_user.id == session.get('user_id'):
        session['username'] = target_user.username
        session['role'] = target_user.role

    flash(f"Account '{new_username}' updated successfully.", "success")
    return redirect(url_for('auth.accounts'))

@auth_bp.route('/accounts/<int:user_id>/reset_password', methods=['POST'])
@chief_librarian_required
def reset_password(user_id):
    target_user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()

    if not new_password:
        flash("New password cannot be empty.", "danger")
        return redirect(url_for('auth.accounts'))

    target_user.set_password(new_password)
    db.session.commit()
    flash(f"Password for '{target_user.username}' reset successfully.", "success")
    return redirect(url_for('auth.accounts'))

@auth_bp.route('/accounts/<int:user_id>/delete', methods=['POST'])
@chief_librarian_required
def delete_account(user_id):
    target_user = User.query.get_or_404(user_id)

    if target_user.id == session.get('user_id'):
        flash("You cannot delete your own logged-in account.", "danger")
        return redirect(url_for('auth.accounts'))

    username = target_user.username
    db.session.delete(target_user)
    db.session.commit()
    flash(f"Account '{username}' deleted successfully.", "info")
    return redirect(url_for('auth.accounts'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not user or not user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('auth.change_password'))

        if new_username and new_username != user.username:
            existing = User.query.filter(User.username == new_username, User.id != user.id).first()
            if existing:
                flash(f"Username '{new_username}' is already taken.", "danger")
                return redirect(url_for('auth.change_password'))
            user.username = new_username
            session['username'] = new_username

        if new_password:
            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for('auth.change_password'))
            user.set_password(new_password)

        db.session.commit()
        flash("Account settings updated successfully.", "success")
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html', user=user)
