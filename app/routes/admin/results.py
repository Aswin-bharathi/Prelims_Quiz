from flask import render_template, request, redirect, url_for, flash, make_response
from app.config import Config
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.result_service import ResultService
from app.services.quiz_type_service import QuizTypeService


# result.py - only change the view_results route

@admin_bp.route('/results')
@admin_login_required
def view_results():
    search = request.args.get('search', '')
    quiz_type_id = request.args.get('quiz_type_id', type=int)
    fmt = request.args.get('format')
    top_n = request.args.get('top_n', 5, type=int)

    if fmt == 'word':
        output = ResultService.export_word(quiz_type_id, top_n)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=top_teams.docx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        return response

    if fmt == 'excel':
        output = ResultService.export_excel(quiz_type_id, search, top_n=top_n)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=results.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response

    # When a specific quiz is selected, limit table rows to top_n
    # When no quiz selected (all quizzes), show everything
    table_limit = top_n if quiz_type_id else 1000000

    results, total, total_pages = ResultService.get_ranked_results(
        page=1, per_page=table_limit, search=search, quiz_type_id=quiz_type_id,top_n=top_n if quiz_type_id else None, 
    )
    top_teams = ResultService.get_leaderboard(quiz_type_id, top_n)
    quiz_types = QuizTypeService.get_all()
    results_released = ResultService.get_announcement_state(quiz_type_id)
    release_states = ResultService.get_all_announcement_states()

    return render_template(
        'admin/results.html',
        results=results, top_teams=top_teams,
        page=1, total_pages=1, search=search,
        quiz_type_id=quiz_type_id, quiz_types=quiz_types, total=total, top_n=top_n,
        results_released=results_released,
        release_states=release_states,
    )


@admin_bp.route('/results/release', methods=['POST'])
@admin_login_required
def release_results():
    quiz_type_id = request.form.get('quiz_type_id', type=int)
    top_n = request.form.get('top_n', 5, type=int)

    if not quiz_type_id:
        flash('Please select a quiz before releasing results.', 'danger')
        return redirect(url_for('admin.view_results'))

    if top_n < 1:
        top_n = 5

    ResultService.set_announcement_state(True, top_n, quiz_type_id)
    flash(f'Results released for the selected quiz (top {top_n} teams).', 'success')
    return redirect(url_for('admin.view_results', quiz_type_id=quiz_type_id, top_n=top_n))


# NEW ROUTE
@admin_bp.route('/results/unrelease', methods=['POST'])
@admin_login_required
def unrelease_results():
    quiz_type_id = request.form.get('quiz_type_id', type=int)

    if not quiz_type_id:
        flash('Please select a quiz to cancel release for.', 'danger')
        return redirect(url_for('admin.view_results'))

    ResultService.unset_announcement_state(quiz_type_id)
    flash('Results release has been cancelled for the selected quiz.', 'success')
    return redirect(url_for('admin.view_results', quiz_type_id=quiz_type_id))