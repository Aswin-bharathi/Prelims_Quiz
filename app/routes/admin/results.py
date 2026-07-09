from flask import render_template, request, redirect, url_for, flash, make_response
from app.config import Config
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.result_service import ResultService
from app.services.quiz_type_service import QuizTypeService


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
        output = ResultService.export_excel(quiz_type_id, search)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=results.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response

    results, total, total_pages = ResultService.get_ranked_results(
        page=1, per_page=1000000, search=search, quiz_type_id=quiz_type_id,
    )
    top_teams = ResultService.get_leaderboard(quiz_type_id, top_n)
    quiz_types = QuizTypeService.get_all()
    results_released = ResultService.get_announcement_state(quiz_type_id)

    return render_template(
        'admin/results.html',
        results=results, top_teams=top_teams,
        page=1, total_pages=1, search=search,
        quiz_type_id=quiz_type_id, quiz_types=quiz_types, total=total, top_n=top_n,
        results_released=results_released,
    )


@admin_bp.route('/results/release', methods=['POST'])
@admin_login_required
def release_results():
    quiz_type_id = request.form.get('quiz_type_id', type=int)
    top_n = request.form.get('top_n', 5, type=int)
    ResultService.set_announcement_state(True, top_n, quiz_type_id)
    flash('Results have been released to students.', 'success')
    return redirect(url_for('admin.view_results', quiz_type_id=quiz_type_id, top_n=top_n))
