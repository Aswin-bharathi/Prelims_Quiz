from flask import render_template, request, redirect, url_for, flash
from app.decorators import admin_login_required
from app.database import get_db
from app.routes.admin import admin_bp


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_login_required
def settings():
    if request.method == 'POST':
        with get_db() as (_, c):
            settings_to_save = {
                'app_name': request.form.get('app_name', 'Intercollege Quiz Platform'),
                'tab_switch_limit': request.form.get('tab_switch_limit', '1'),
                'prevent_copy': '1' if 'prevent_copy' in request.form else '0'
            }
            for key, val in settings_to_save.items():
                c.execute(
                    '''INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)
                       ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)''',
                    (key, val),
                )
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin.settings'))

    with get_db() as (_, c):
        c.execute('SELECT setting_key, setting_value FROM settings')
        rows = c.fetchall()
    settings_map = {r['setting_key']: r['setting_value'] for r in rows}
    return render_template('admin/settings.html', settings=settings_map)
