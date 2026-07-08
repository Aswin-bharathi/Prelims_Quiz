from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request


def admin_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('admin'):
            flash('Please login as admin first!', 'error')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return wrap


def quiz_session_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        team = session.get('team')
        if not team or not team.get('quiz_type_id'):
            flash('Please login first!', 'error')
            return redirect(url_for('quiz.quiz_login'))
        return f(*args, **kwargs)
    return wrap


def quiz_active_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        team = session.get('team')
        if not team:
            if request.is_json or request.path.startswith('/quiz/api'):
                return jsonify({'error': 'Not authenticated'}), 403
            flash('Please login first!', 'error')
            return redirect(url_for('quiz.quiz_login'))
        if not session.get('quiz_active'):
            flash('Quiz session is not active.', 'error')
            return redirect(url_for('quiz.quiz_login'))
        return f(*args, **kwargs)
    return wrap
