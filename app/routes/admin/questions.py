from flask import render_template, request, redirect, url_for, flash
from app.config import Config
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.question_service import QuestionService
from app.services.quiz_type_service import QuizTypeService
from app.database import get_db


@admin_bp.route('/questions')
@admin_login_required
def show_questions():
    search = request.args.get('search', '')
    quiz_type_id = request.args.get('quiz_type_id', type=int)
    # Set per_page=1000000 to return all matching questions for inner scrolling
    questions, total, total_pages = QuestionService.get_questions(
        quiz_type_id=quiz_type_id, page=1, per_page=1000000, search=search,
    )
    quiz_types = QuizTypeService.get_all()
    return render_template(
        'admin/questions/list.html',
        questions=questions, page=1, total_pages=1,
        search=search, quiz_types=quiz_types, quiz_type_id=quiz_type_id, total=total,
    )


@admin_bp.route('/questions/add', methods=['GET', 'POST'])
@admin_login_required
def add_question():
    quiz_types = QuizTypeService.get_all()
    if request.method == 'POST':
        ok, result = QuestionService.create({
            'quiz_type_id': request.form['quiz_type_id'],
            'question': request.form['question'],
            'option1': request.form['option1'],
            'option2': request.form['option2'],
            'option3': request.form['option3'],
            'option4': request.form['option4'],
            'answer': request.form['answer'],
        })
        if ok:
            flash('Question added successfully!', 'success')
            return redirect(url_for('admin.show_questions', quiz_type_id=request.form['quiz_type_id']))
        flash(result, 'error')
    return render_template('admin/questions/add.html', quiz_types=quiz_types)


@admin_bp.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def edit_question(question_id):
    question = QuestionService.get_by_id(question_id)
    if not question:
        flash('Question not found.', 'error')
        return redirect(url_for('admin.show_questions'))
    quiz_types = QuizTypeService.get_all()
    if request.method == 'POST':
        ok, msg = QuestionService.update(question_id, {
            'quiz_type_id': request.form['quiz_type_id'],
            'question': request.form['question'],
            'option1': request.form['option1'],
            'option2': request.form['option2'],
            'option3': request.form['option3'],
            'option4': request.form['option4'],
            'answer': request.form['answer'],
        })
        if ok:
            flash(msg, 'success')
            return redirect(url_for('admin.show_questions', quiz_type_id=request.form['quiz_type_id']))
        flash(msg, 'error')
    return render_template('admin/questions/edit.html', question=question, quiz_types=quiz_types)


@admin_bp.route('/questions/upload', methods=['GET', 'POST'])
@admin_login_required
def upload_questions():
    quiz_types = QuizTypeService.get_all()
    if request.method == 'POST':
        quiz_type_id = request.form.get('quiz_type_id', type=int)
        if not quiz_type_id:
            flash('Please select a quiz type.', 'error')
            return redirect(url_for('admin.upload_questions'))
        if 'file' not in request.files or not request.files['file'].filename:
            flash('No file selected!', 'error')
            return redirect(url_for('admin.upload_questions'))
        ok, inserted, errors = QuestionService.upload_from_excel(request.files['file'], quiz_type_id)
        failed = len(errors)
        if inserted:
            flash(f'Upload complete: {inserted} successful row(s), {failed} failed row(s).', 'success')
        else:
            flash(f'No questions were uploaded. {failed} failed row(s).', 'error')
        for err in errors[:10]:
            flash(err, 'error')
        if failed > 10:
            flash(f'...and {failed - 10} more failed row(s).', 'error')
        return redirect(url_for('admin.show_questions', quiz_type_id=quiz_type_id))
    return render_template('admin/questions/upload.html', quiz_types=quiz_types)


@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@admin_login_required
def delete_question(question_id):
    QuestionService.delete(question_id)
    flash('Question deleted successfully!', 'success')
    # Try to redirect to the previous quiz type if available in referer/args
    quiz_type_id = request.args.get('quiz_type_id')
    return redirect(url_for('admin.show_questions', quiz_type_id=quiz_type_id))


@admin_bp.route('/questions/bulk-delete', methods=['POST'])
@admin_login_required
def bulk_delete_questions():
    quiz_type_id = request.form.get('quiz_type_id', type=int)
    if not quiz_type_id:
        flash('Please select a quiz type to bulk delete questions.', 'error')
        return redirect(url_for('admin.show_questions'))
    quiz_type = QuizTypeService.get_by_id(quiz_type_id)
    if not quiz_type:
        flash('Quiz type not found.', 'error')
        return redirect(url_for('admin.show_questions'))
    
    with get_db() as (_, c):
        c.execute('DELETE FROM questions WHERE quiz_type_id = %s', (quiz_type_id,))
    
    flash(f'All questions for "{quiz_type["name"]}" have been deleted successfully.', 'success')
    return redirect(url_for('admin.show_questions', quiz_type_id=quiz_type_id))
