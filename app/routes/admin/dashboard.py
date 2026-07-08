from flask import render_template
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.quiz_type_service import QuizTypeService
from app.services.monitoring_service import MonitoringService


@admin_bp.route('/dashboard')
@admin_login_required
def dashboard():
    stats = QuizTypeService.get_dashboard_stats()
    monitoring = MonitoringService.get_live_data()[:3]
    return render_template('admin/dashboard.html', stats=stats, monitoring_preview=monitoring)
