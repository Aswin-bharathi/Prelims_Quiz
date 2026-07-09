from flask import render_template, request, redirect, url_for, session, flash
from app.routes.quiz import quiz_bp
from app.services.quiz_service import QuizService


@quiz_bp.route('/login', methods=['GET', 'POST'])
def quiz_login():
    if request.method == 'POST':
        lotname = request.form['lotname'].replace(' ', '').strip().lower()
        password = request.form['password'].replace(' ', '').strip().lower()
        entry_code = request.form['entry_code'].replace(' ', '').strip().upper()

        ok, msg, team_data = QuizService.authenticate(lotname, password, entry_code)
        if ok:
            admin_val = session.get('admin')
            session.clear()
            if admin_val:
                session['admin'] = admin_val
            session['team'] = team_data
            session['authenticated'] = True
            return redirect(url_for('quiz.quiz_instructions'))
        flash(msg, 'error')

    return render_template('quiz/login.html')
