# pyrefly: ignore [missing-import]
from flask import request, jsonify
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.question_service import QuestionService
from app.services.team_service import TeamService
from app.services.quiz_type_service import QuizTypeService
from app.services.result_service import ResultService
from app.services.monitoring_service import MonitoringService
from app.database import get_db

# Helper for standard JSON response
def json_response(status='success', message='', data=None):
    return jsonify({'status': status, 'message': message, 'data': data})

# Helper to get request data whether JSON or Form
def get_request_data():
    if request.is_json:
        return request.get_json() or {}
    # Convert MultiDict to standard dict, extracting lists for multi-select
    data = {}
    for key in request.form:
        list_val = request.form.getlist(key)
        if len(list_val) > 1:
            data[key] = list_val
        else:
            data[key] = request.form.get(key)
    return data

# ------------------- Questions -------------------
@admin_bp.route('/api/questions', methods=['GET'])
@admin_login_required
def api_get_questions():
    search = request.args.get('search', '')
    quiz_type_id = request.args.get('quiz_type_id', type=int)
    questions, total, _ = QuestionService.get_questions(page=1, per_page=1000000, search=search, quiz_type_id=quiz_type_id)
    return json_response(data={'questions': questions, 'total': total})

@admin_bp.route('/api/questions', methods=['POST'])
@admin_login_required
def api_create_question():
    data = get_request_data()
    ok, result = QuestionService.create(data)
    if ok:
        return json_response(message='Question created.', data={'id': result})
    return json_response(status='error', message=result), 400

@admin_bp.route('/api/questions/<int:question_id>', methods=['PUT', 'POST'])
@admin_login_required
def api_update_question(question_id):
    data = get_request_data()
    ok, result = QuestionService.update(question_id, data)
    if ok:
        return json_response(message=result or 'Question updated.')
    return json_response(status='error', message=result), 400

@admin_bp.route('/api/questions/<int:question_id>/delete', methods=['POST', 'DELETE'])
@admin_login_required
def api_delete_question(question_id):
    # delete question
    ok, result = QuestionService.delete(question_id)
    if ok:
        return json_response(message='Question deleted successfully.')
    return json_response(status='error', message=result), 400

@admin_bp.route('/api/questions/bulk-delete', methods=['POST'])
@admin_login_required
def api_bulk_delete_questions():
    data = get_request_data()
    quiz_type_id = data.get('quiz_type_id')
    if not quiz_type_id:
        return json_response(status='error', message='quiz_type_id required'), 400
    
    quiz_type = QuizTypeService.get_by_id(quiz_type_id)
    if not quiz_type:
        return json_response(status='error', message='Quiz type not found.'), 404
        
    with get_db() as (_, c):
        c.execute('DELETE FROM questions WHERE quiz_type_id = %s', (quiz_type_id,))
    
    return json_response(message=f'All questions for "{quiz_type["name"]}" deleted successfully.')

# ------------------- Teams -------------------
@admin_bp.route('/api/teams', methods=['GET'])
@admin_login_required
def api_get_teams():
    search = request.args.get('search', '')
    quiz_type_id = request.args.get('quiz_type_id', type=int)
    status_filter = request.args.get('status', '')
    teams, total, _ = TeamService.get_teams(page=1, per_page=1000000, search=search, quiz_type_id=quiz_type_id, status_filter=status_filter or None)
    return json_response(data={'teams': teams, 'total': total})

@admin_bp.route('/api/teams', methods=['POST'])
@admin_login_required
def api_create_team():
    data = get_request_data()
    all_quizzes = data.get('assignment') == 'all' or data.get('all_quizzes') == '1' or data.get('all_quizzes') is True
    # Get list of quiz type ids
    quiz_type_ids = data.get('quiz_type_ids', [])
    if isinstance(quiz_type_ids, str):
        quiz_type_ids = [quiz_type_ids]
    
    ok, msg, student_id = TeamService.create_team(
        data.get('lotname', ''), all_quizzes=all_quizzes, quiz_type_ids=quiz_type_ids
    )
    if ok:
        return json_response(message=msg, data={'id': student_id})
    return json_response(status='error', message=msg), 400

@admin_bp.route('/api/teams/<int:team_id>', methods=['PUT', 'POST'])
@admin_login_required
def api_update_team(team_id):
    data = get_request_data()
    all_quizzes = data.get('assignment') == 'all' or data.get('all_quizzes') == '1' or data.get('all_quizzes') is True
    quiz_type_ids = data.get('quiz_type_ids', [])
    if isinstance(quiz_type_ids, str):
        quiz_type_ids = [quiz_type_ids]

    ok, msg = TeamService.update_team(
        team_id, data.get('lotname', ''), all_quizzes=all_quizzes, quiz_type_ids=quiz_type_ids
    )
    if ok:
        return json_response(message=msg)
    return json_response(status='error', message=msg), 400

@admin_bp.route('/api/teams/<int:team_id>/delete', methods=['POST', 'DELETE'])
@admin_login_required
def api_delete_team(team_id):
    TeamService.delete_team(team_id)
    return json_response(message='Team deleted successfully.')

@admin_bp.route('/api/teams/sync', methods=['POST'])
@admin_login_required
def api_sync_teams():
    ok, err, added, skipped = TeamService.sync_from_api()
    if ok:
        return json_response(message=f'Successfully added {added} teams, skipped {skipped}.')
    return json_response(status='error', message=err), 400

# ------------------- Quiz Types -------------------
@admin_bp.route('/api/quiz-types', methods=['GET'])
@admin_login_required
def api_get_quiz_types():
    quiz_types = QuizTypeService.get_all()
    return json_response(data={'quiz_types': quiz_types})

@admin_bp.route('/api/quiz-types', methods=['POST'])
@admin_login_required
def api_create_quiz_type():
    data = get_request_data()
    ok, result = QuizTypeService.create({
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'question_count': data.get('question_count', 0),
        'duration_minutes': data.get('duration_minutes', 0),
        'entry_code': data.get('entry_code', ''),
        'status': data.get('status', 'inactive'),
        'allow_reattempt': data.get('allow_reattempt'),
    })
    if ok:
        return json_response(message='Quiz type created successfully.', data={'id': result})
    return json_response(status='error', message=result), 400

@admin_bp.route('/api/quiz-types/<int:qt_id>', methods=['PUT', 'POST'])
@admin_login_required
def api_update_quiz_type(qt_id):
    data = get_request_data()
    ok, result = QuizTypeService.update(qt_id, {
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'question_count': data.get('question_count', 0),
        'duration_minutes': data.get('duration_minutes', 0),
        'entry_code': data.get('entry_code', ''),
        'status': data.get('status', 'inactive'),
        'allow_reattempt': data.get('allow_reattempt'),
    })
    if ok:
        return json_response(message='Quiz type updated successfully.')
    return json_response(status='error', message=result), 400

@admin_bp.route('/api/quiz-types/<int:qt_id>/delete', methods=['POST', 'DELETE'])
@admin_login_required
def api_delete_quiz_type(qt_id):
    QuizTypeService.delete(qt_id)
    return json_response(message='Quiz type deleted successfully.')

@admin_bp.route('/api/quiz-types/<int:qt_id>/toggle', methods=['POST'])
@admin_login_required
def api_toggle_quiz_type(qt_id):
    ok, result = QuizTypeService.toggle_status(qt_id)
    if ok:
        return json_response(message=f'Quiz type status toggled to {result}.', data={'status': result})
    return json_response(status='error', message=result), 400

@admin_bp.route('/api/quiz-types/<int:qt_id>/start', methods=['POST'])
@admin_login_required
def api_start_quiz_type(qt_id):
    quiz_type = QuizTypeService.get_by_id(qt_id)
    if not quiz_type:
        return json_response(status='error', message='Quiz type not found.'), 404
    QuizTypeService.set_quiz_status(qt_id, 'running')
    return json_response(message=f'"{quiz_type["name"]}" is now open for teams.')

@admin_bp.route('/api/quiz-types/<int:qt_id>/end', methods=['POST'])
@admin_login_required
def api_end_quiz_type(qt_id):
    quiz_type = QuizTypeService.get_by_id(qt_id)
    if not quiz_type:
        return json_response(status='error', message='Quiz type not found.'), 404
    QuizTypeService.set_quiz_status(qt_id, 'ended')
    return json_response(message=f'"{quiz_type["name"]}" has been closed.')

# ------------------- Dashboard Live Stats -------------------
@admin_bp.route('/api/dashboard/stats', methods=['GET'])
@admin_login_required
def api_dashboard_stats():
    stats = QuizTypeService.get_dashboard_stats()
    monitoring = MonitoringService.get_live_data()[:3]
    return json_response(data={'stats': stats, 'monitoring_preview': monitoring})

# ------------------- Live Monitoring -------------------
@admin_bp.route('/api/monitoring/live', methods=['GET'])
@admin_login_required
def api_monitoring_live():
    data = MonitoringService.get_live_data()
    return json_response(data={'quizzes': data})

# ------------------- Results -------------------
@admin_bp.route('/api/results/data', methods=['GET'])
@admin_login_required
def api_results_data():
    search = request.args.get('search', '')
    quiz_type_id = request.args.get('quiz_type_id', type=int)
    top_n = request.args.get('top_n', default=5, type=int)
    results, total, _ = ResultService.get_ranked_results(page=1, per_page=1000000, search=search, quiz_type_id=quiz_type_id)
    top_teams = ResultService.get_leaderboard(quiz_type_id, top_n)
    return json_response(data={
        'results': results,
        'total': total,
        'top_teams': top_teams,
        'top_n': top_n
    })

# ------------------- Settings -------------------
@admin_bp.route('/api/settings', methods=['GET', 'POST'])
@admin_login_required
def api_settings():
    if request.method == 'GET':
        with get_db() as (_, c):
            c.execute('SELECT setting_key, setting_value FROM settings')
            rows = c.fetchall()
        settings_map = {r['setting_key']: r['setting_value'] for r in rows}
        return json_response(data={'settings': settings_map})
    else:
        data = get_request_data()
        settings_to_save = {
            'app_name': data.get('app_name', 'Intercollege Quiz Platform'),
            'tab_switch_limit': data.get('tab_switch_limit', '1'),
            'prevent_copy': '1' if data.get('prevent_copy') == '1' or data.get('prevent_copy') is True else '0'
        }
        with get_db() as (_, c):
            for key, val in settings_to_save.items():
                c.execute(
                    '''INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)
                       ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)''',
                    (key, val),
                )
        return json_response(message='Settings saved successfully.', data=settings_to_save)
