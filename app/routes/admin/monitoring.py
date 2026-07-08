from flask import render_template, jsonify
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.monitoring_service import MonitoringService
from app.services.quiz_type_service import QuizTypeService


@admin_bp.route('/monitoring')
@admin_login_required
def monitoring():
    quiz_types = QuizTypeService.get_all()
    return render_template('admin/monitoring.html', quiz_types=quiz_types)


@admin_bp.route('/api/monitoring')
@admin_login_required
def monitoring_api():
    return jsonify({'quizzes': MonitoringService.get_live_data()})


@admin_bp.route('/api/monitoring/sessions')
@admin_login_required
def monitoring_sessions_api():
    quiz_type_id = __import__('flask').request.args.get('quiz_type_id', type=int)
    sessions = MonitoringService.get_active_sessions(quiz_type_id)
    return jsonify({'sessions': sessions})
