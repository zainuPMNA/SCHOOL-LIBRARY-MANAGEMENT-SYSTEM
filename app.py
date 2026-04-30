from flask import Flask, render_template
from config import Config
from models import db
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
    from routes.dashboard import dashboard_bp
    from routes.students import students_bp
    from routes.books import books_bp
    from routes.circulation import circulation_bp
    from routes.backup import backup_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(circulation_bp, url_prefix='/circulation')
    app.register_blueprint(backup_bp, url_prefix='/backup')

    # Create tables
    with app.app_context():
        db.create_all()

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
