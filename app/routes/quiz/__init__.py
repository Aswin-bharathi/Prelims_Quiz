from flask import Blueprint

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

from app.routes.quiz import auth, quiz_flow  # noqa: E402, F401
