from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from app.routes.admin import auth, dashboard, quiz_types, teams, questions, monitoring, results, settings, api  # noqa: E402, F401
