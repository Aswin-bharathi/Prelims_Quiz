from flask import render_template, request, redirect, url_for, flash
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.quiz_type_service import QuizTypeService


@admin_bp.route('/quiz-types')
@admin_login_required
def quiz_types_list():
    quiz_types = QuizTypeService.get_all()
    return render_template('admin/quiz_types/list.html', quiz_types=quiz_types)


@admin_bp.route('/quiz-types/create', methods=['GET', 'POST'])
@admin_login_required
def quiz_types_create():
    if request.method == 'POST':
        ok, result = QuizTypeService.create({
            'name': request.form['name'],
            'description': request.form.get('description'),
            'question_count': request.form['question_count'],
            'duration_minutes': request.form['duration_minutes'],
            'entry_code': request.form['entry_code'],
            'status': request.form.get('status', 'inactive'),
            'allow_reattempt': request.form.get('allow_reattempt'),
        })
        if ok:
            flash('Quiz type created successfully!', 'success')
            return redirect(url_for('admin.quiz_types_list'))
        flash(result, 'error')
    return render_template('admin/quiz_types/form.html', quiz_type=None)


@admin_bp.route('/quiz-types/<int:quiz_type_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def quiz_types_edit(quiz_type_id):
    quiz_type = QuizTypeService.get_by_id(quiz_type_id)
    if not quiz_type:
        flash('Quiz type not found.', 'error')
        return redirect(url_for('admin.quiz_types_list'))
    if request.method == 'POST':
        ok, msg = QuizTypeService.update(quiz_type_id, {
            'name': request.form['name'],
            'description': request.form.get('description'),
            'question_count': request.form['question_count'],
            'duration_minutes': request.form['duration_minutes'],
            'entry_code': request.form['entry_code'],
            'status': request.form.get('status', 'inactive'),
            'allow_reattempt': request.form.get('allow_reattempt'),
        })
        if ok:
            flash('Quiz type updated successfully!', 'success')
            return redirect(url_for('admin.quiz_types_list'))
        flash(msg, 'error')
    return render_template('admin/quiz_types/form.html', quiz_type=quiz_type)


@admin_bp.route('/quiz-types/<int:quiz_type_id>/start', methods=['POST'])
@admin_login_required
def quiz_types_start(quiz_type_id):
    quiz_type = QuizTypeService.get_by_id(quiz_type_id)
    if not quiz_type:
        flash('Quiz type not found.', 'error')
        return redirect(url_for('admin.quiz_types_list'))
    QuizTypeService.set_quiz_status(quiz_type_id, 'running')
    flash(f'"{quiz_type["name"]}" is now open for teams.', 'success')
    return redirect(url_for('admin.quiz_types_list'))


@admin_bp.route('/quiz-types/<int:quiz_type_id>/end', methods=['POST'])
@admin_login_required
def quiz_types_end(quiz_type_id):
    quiz_type = QuizTypeService.get_by_id(quiz_type_id)
    if not quiz_type:
        flash('Quiz type not found.', 'error')
        return redirect(url_for('admin.quiz_types_list'))
    QuizTypeService.set_quiz_status(quiz_type_id, 'ended')
    flash(f'"{quiz_type["name"]}" has been closed.', 'success')
    return redirect(url_for('admin.quiz_types_list'))


@admin_bp.route('/quiz-types/<int:quiz_type_id>/delete', methods=['POST'])
@admin_login_required
def quiz_types_delete(quiz_type_id):
    QuizTypeService.delete(quiz_type_id)
    flash('Quiz type deleted.', 'success')
    return redirect(url_for('admin.quiz_types_list'))


@admin_bp.route('/quiz-types/<int:quiz_type_id>/toggle', methods=['POST'])
@admin_login_required
def quiz_types_toggle(quiz_type_id):
    ok, result = QuizTypeService.toggle_status(quiz_type_id)
    if ok:
        flash(f'Quiz type is now {result}.', 'success')
    else:
        flash(result, 'error')
    return redirect(url_for('admin.quiz_types_list'))
