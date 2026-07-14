from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Disable browser caching for all admin pages
@admin_bp.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Import routes after creating the blueprint
from app.routes.admin import (
    auth,
    dashboard,
    quiz_types,
    teams,
    questions,
    monitoring,
    results,
    settings,
    api,
)  # noqa: E402, F401