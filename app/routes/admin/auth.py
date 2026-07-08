from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app.database import get_db
from app.decorators import admin_login_required
from app.routes.admin import admin_bp


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as (_, c):
            c.execute('SELECT * FROM admins WHERE username = %s', (username,))
            admin = c.fetchone()
        if admin and check_password_hash(admin['password'], password):
            session.permanent = True
            session['admin'] = username
            flash('Welcome back!', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials!', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@admin_login_required
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin.admin_login'))
