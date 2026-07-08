from pathlib import Path
from flask import Flask, redirect, url_for
from app.config import Config
from app.db_init import init_db


def create_app():
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / 'templates'),
        static_folder=str(project_root / 'static'),
    )
    app.config.from_object(Config)

    init_db()

    from app.routes.admin import admin_bp
    from app.routes.quiz import quiz_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(quiz_bp)

    @app.route('/')
    def index():
        return redirect(url_for('quiz.quiz_login'))

    @app.route('/admin_login')
    def legacy_admin_login():
        return redirect(url_for('admin.admin_login'))

    @app.route('/quiz_login')
    def legacy_quiz_login():
        return redirect(url_for('quiz.quiz_login'))

    @app.route('/logout')
    def legacy_logout():
        return redirect(url_for('admin.admin_logout'))

    return app
