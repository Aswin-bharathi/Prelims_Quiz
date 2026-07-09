import time
from flask import render_template, request, redirect, url_for, session, flash, jsonify, make_response
from app.decorators import quiz_session_required, quiz_active_required
from app.routes.quiz import quiz_bp
from app.services.quiz_service import QuizService
from app.services.result_service import ResultService
from app.utils.formatting import format_duration


def _verify_quiz_access():
    team = session.get('team')
    if not team:
        return False, 'Please login first!'
    token = session.get('session_token')
    if session.get('quiz_active') and not QuizService.verify_session(team, token):
        session.clear()
        return False, 'Session expired or invalid.'
    return True, None


def _complete_quiz(answers):
    questions = session.get('questions', [])
    team = session['team']
    start_time = session.get('start_time', time.time())

    score, duration = QuizService.submit_quiz(team, answers, questions, start_time)

    admin_val = session.get('admin')
    session.clear()
    if admin_val:
        session['admin'] = admin_val
    session['quiz_completed'] = True
    session['result'] = {
        'score': score,
        'total': len(questions),
        'duration': duration,
        'duration_formatted': format_duration(duration),
        'quiz_type_name': team.get('quiz_type_name', 'Quiz'),
        'quiz_type_id': team.get('quiz_type_id'),
        'lotname': team['lotname'],
    }


@quiz_bp.route('/instructions')
@quiz_session_required
def quiz_instructions():
    team = session['team']
    return render_template('quiz/instructions.html', team=team)


@quiz_bp.route('/start', methods=['GET'])
@quiz_session_required
def quiz_start():
    if session.get('quiz_active'):
        return redirect(url_for('quiz.quiz_questions'))

    team = session['team']
    ok, msg, quiz_data = QuizService.initialize_session(team)
    if not ok:
        flash(msg, 'error')
        return redirect(url_for('quiz.quiz_login'))

    session['questions'] = quiz_data['questions']
    session['session_token'] = quiz_data['session_token']
    session['start_time'] = quiz_data['start_time']
    session['duration_seconds'] = quiz_data['duration_seconds']
    session['total_questions'] = quiz_data['total_questions']
    session['quiz_active'] = True
    session['tab_switches'] = 0
    team['session_token'] = quiz_data['session_token']
    session['team'] = team

    return render_template('quiz/start.html', team=team, total_questions=quiz_data['total_questions'],
                           duration_minutes=team['duration_minutes'])


@quiz_bp.route('/questions')
@quiz_session_required
@quiz_active_required
def quiz_questions():
    ok, msg = _verify_quiz_access()
    if not ok:
        flash(msg, 'error')
        return redirect(url_for('quiz.quiz_login'))

    team = session['team']
    questions = session.get('questions', [])
    if not questions:
        flash('No active quiz session.', 'error')
        return redirect(url_for('quiz.quiz_login'))

    elapsed = int(time.time() - session['start_time'])
    remaining = max(0, session['duration_seconds'] - elapsed)
    if remaining <= 0:
        _complete_quiz({})
        flash('Time is up! Your quiz was submitted automatically.', 'error')
        return redirect(url_for('quiz.quiz_result'))

    from app.database import get_db
    with get_db() as (_, c):
        c.execute('SELECT setting_key, setting_value FROM settings')
        rows = c.fetchall()
    settings_map = {r['setting_key']: r['setting_value'] for r in rows}

    return render_template(
        'quiz/questions.html',
        team=team,
        questions=questions,
        remaining_seconds=remaining,
        total_questions=len(questions),
        settings=settings_map,
    )


@quiz_bp.route('/submit', methods=['POST'])
@quiz_session_required
def quiz_submit():
    ok, msg = _verify_quiz_access()
    if not ok:
        flash(msg, 'error')
        return redirect(url_for('quiz.quiz_login'))

    if not session.get('quiz_active'):
        flash('Quiz session is not active.', 'error')
        return redirect(url_for('quiz.quiz_login'))

    _complete_quiz(request.form.to_dict())

    return redirect(url_for('quiz.quiz_completion'))


@quiz_bp.route('/completion')
def quiz_completion():
    if not session.get('quiz_completed'):
        flash('Please complete the quiz first!', 'error')
        return redirect(url_for('quiz.quiz_login'))

    result = session.get('result', {})
    quiz_type_id = result.get('quiz_type_id') or session.get('team', {}).get('quiz_type_id')
    announcement_released = ResultService.get_announcement_state(quiz_type_id)
    announcement_top_n = ResultService.get_announcement_top_n(quiz_type_id)
    selected = ResultService.is_team_selected(result.get('lotname'), quiz_type_id, announcement_top_n) if announcement_released else False

    return render_template(
        'quiz/completion.html',
        result=result,
        announcement={'released': announcement_released, 'top_n': announcement_top_n, 'selected': selected},
    )


@quiz_bp.route('/result')
def quiz_result():
    if not session.get('quiz_completed'):
        flash('Please complete the quiz first!', 'error')
        return redirect(url_for('quiz.quiz_login'))

    result = session.get('result', {})
    quiz_type_id = result.get('quiz_type_id') or session.get('team', {}).get('quiz_type_id')
    announcement_released = ResultService.get_announcement_state(quiz_type_id)
    announcement_top_n = ResultService.get_announcement_top_n(quiz_type_id)
    selected = ResultService.is_team_selected(result.get('lotname'), quiz_type_id, announcement_top_n) if announcement_released else False

    response = make_response(render_template(
        'quiz/result.html',
        result=result,
        announcement={'released': announcement_released, 'top_n': announcement_top_n, 'selected': selected},
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


@quiz_bp.route('/api/results-state')
def results_state():
    if not session.get('quiz_completed'):
        return jsonify({'ok': False, 'message': 'Quiz not completed'}), 403

    result = session.get('result', {})
    quiz_type_id = result.get('quiz_type_id') or session.get('team', {}).get('quiz_type_id')
    announcement_released = ResultService.get_announcement_state(quiz_type_id)
    announcement_top_n = ResultService.get_announcement_top_n(quiz_type_id)
    selected = ResultService.is_team_selected(result.get('lotname'), quiz_type_id, announcement_top_n) if announcement_released else False

    return jsonify({
        'ok': True,
        'announcement': {
            'released': announcement_released,
            'selected': selected,
        },
    })


@quiz_bp.route('/track_tab_switch', methods=['POST'])
@quiz_active_required
def track_tab_switch():
    ok, _ = _verify_quiz_access()
    if not ok:
        return jsonify({'auto_submit': True})

    limit = 1
    from app.database import get_db
    with get_db() as (_, c):
        c.execute("SELECT setting_value FROM settings WHERE setting_key = 'tab_switch_limit'")
        row = c.fetchone()
        if row:
            try:
                limit = int(row['setting_value'])
            except ValueError:
                pass

    session['tab_switches'] = session.get('tab_switches', 0) + 1
    if session['tab_switches'] >= limit:
        return jsonify({'auto_submit': True})
    return jsonify({'auto_submit': False})


@quiz_bp.route('/api/progress', methods=['POST'])
@quiz_active_required
def update_progress():
    ok, _ = _verify_quiz_access()
    if not ok:
        return jsonify({'error': 'Unauthorized'}), 403
    current = request.json.get('current_question', 1) if request.is_json else 1
    QuizService.update_progress(session['team'], current)
    return jsonify({'ok': True})
