from flask import render_template, request, redirect, url_for, flash
from app.config import Config
from app.decorators import admin_login_required
from app.routes.admin import admin_bp
from app.services.team_service import TeamService
from app.services.quiz_type_service import QuizTypeService


@admin_bp.route('/teams')
@admin_login_required
def show_teams():
    search = request.args.get('search', '')
    quiz_type_id = request.args.get('quiz_type_id', type=int)
    status_filter = request.args.get('status', '')
    # Query with huge per_page to return all matching rows for inner scrolling container
    teams, total, total_pages = TeamService.get_teams(
        page=1, per_page=1000000, search=search,
        quiz_type_id=quiz_type_id, status_filter=status_filter or None,
    )
    quiz_types = QuizTypeService.get_all()
    return render_template(
        'admin/teams/list.html',
        teams=teams, page=1, total_pages=1,
        search=search, quiz_types=quiz_types,
        quiz_type_id=quiz_type_id, status_filter=status_filter, total=total,
    )


@admin_bp.route('/teams/add', methods=['GET', 'POST'])
@admin_login_required
def add_team():
    quiz_types = QuizTypeService.get_all()
    if request.method == 'POST':
        all_quizzes = request.form.get('assignment') == 'all'
        quiz_type_ids = request.form.getlist('quiz_type_ids')
        ok, msg, _ = TeamService.create_team(
            request.form['lotname'], all_quizzes=all_quizzes, quiz_type_ids=quiz_type_ids,
        )
        flash(msg, 'success' if ok else 'error')
        if ok:
            return redirect(url_for('admin.show_teams'))
    return render_template('admin/teams/add.html', quiz_types=quiz_types)


@admin_bp.route('/teams/upload', methods=['GET', 'POST'])
@admin_login_required
def upload_teams():
    quiz_types = QuizTypeService.get_all()
    if request.method == 'POST':
        if 'file' not in request.files or not request.files['file'].filename:
            flash('Please select a file to upload.', 'error')
            return redirect(url_for('admin.upload_teams'))
        assignment = request.form.get('assignment', 'specific')
        assign_all = assignment == 'all'
        quiz_type_id = request.form.get('quiz_type_id', type=int) if not assign_all else None
        if not assign_all and not quiz_type_id:
            flash('Please select a quiz type or choose All Quiz Types.', 'error')
            return redirect(url_for('admin.upload_teams'))
        ok, result, errors = TeamService.upload_from_excel(
            request.files['file'], quiz_type_id=quiz_type_id, assign_all=assign_all,
        )
        if ok:
            flash(f"Uploaded {result['added']} teams. Skipped {result['skipped']} duplicates/errors.", 'success')
        else:
            flash('Upload failed.', 'error')
        for err in errors[:10]:
            flash(err, 'error')
        if len(errors) > 10:
            flash(f'...and {len(errors) - 10} more errors.', 'error')
        return redirect(url_for('admin.show_teams'))
    return render_template('admin/teams/upload.html', quiz_types=quiz_types)


@admin_bp.route('/teams/<int:team_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def update_team(team_id):
    team = TeamService.get_by_id(team_id)
    quiz_types = QuizTypeService.get_all()
    if not team:
        flash('Team not found.', 'error')
        return redirect(url_for('admin.show_teams'))
    if request.method == 'POST':
        all_quizzes = request.form.get('assignment') == 'all'
        quiz_type_ids = request.form.getlist('quiz_type_ids')
        ok, msg = TeamService.update_team(
            team_id, request.form['lotname'], all_quizzes=all_quizzes, quiz_type_ids=quiz_type_ids,
        )
        flash(msg, 'success' if ok else 'error')
        if ok:
            return redirect(url_for('admin.show_teams'))
    return render_template('admin/teams/edit.html', team=team, quiz_types=quiz_types)


@admin_bp.route('/teams/<int:team_id>/delete', methods=['POST'])
@admin_login_required
def delete_team(team_id):
    TeamService.delete_team(team_id)
    flash('Team deleted successfully!', 'success')
    return redirect(url_for('admin.show_teams'))


@admin_bp.route('/teams/sync', methods=['GET', 'POST'])
@admin_login_required
def sync_teams():
    if request.method == 'POST':
        ok, err, added, skipped = TeamService.sync_from_api()
        if ok:
            flash(f'Successfully added {added} teams, skipped {skipped}.', 'success')
        else:
            flash(f'Error: {err}', 'error')
        return redirect(url_for('admin.show_teams'))
    return render_template('admin/teams/sync.html')

# teams.py — merge into the existing file, don't duplicate imports

@admin_bp.route('/teams/<int:team_id>/quiz-status/<int:quiz_type_id>/toggle', methods=['POST'])
@admin_login_required
def toggle_quiz_status(team_id, quiz_type_id):
    ok, msg = TeamService.toggle_quiz_status(team_id, quiz_type_id)
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('admin.show_teams', **request.args))


@admin_bp.route('/teams/delete-all', methods=['POST'])
@admin_login_required
def delete_all_teams():
    ok, msg = TeamService.delete_all_teams()
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('admin.show_teams'))