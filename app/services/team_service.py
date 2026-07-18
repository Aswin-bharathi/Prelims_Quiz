import pandas as pd
from app.config import Config
from app.database import get_db


class TeamService:

    @staticmethod
    def default_password(lotname):
        return f"{lotname.strip()}{Config.PASSWORD_SUFFIX}"

    @staticmethod
    def get_teams(page=1, per_page=10, search='', quiz_type_id=None, status_filter=None):
        offset = (page - 1) * per_page
        with get_db() as (_, c):
            base = 'FROM students s WHERE 1=1'
            params = []

            if search:
                base += ' AND s.lotname LIKE %s'
                params.append(f'%{search}%')

            if quiz_type_id:
                base += '''
                    AND (s.all_quizzes = 1 OR EXISTS (
                        SELECT 1 FROM team_quiz_assignments tqa
                        WHERE tqa.student_id = s.id AND tqa.quiz_type_id = %s
                    ))
                '''
                params.append(quiz_type_id)

            if status_filter and quiz_type_id:
                if status_filter == 'incomplete':
                    base += '''
                        AND NOT EXISTS (
                            SELECT 1 FROM team_quiz_status tqs
                            WHERE tqs.student_id = s.id AND tqs.quiz_type_id = %s AND tqs.status = 'completed'
                        )
                    '''
                    params.append(quiz_type_id)
                else:
                    base += '''
                        AND EXISTS (
                            SELECT 1 FROM team_quiz_status tqs
                            WHERE tqs.student_id = s.id AND tqs.quiz_type_id = %s AND tqs.status = %s
                        )
                    '''
                    params.append(quiz_type_id)
                    params.append(status_filter)

            c.execute(f'SELECT COUNT(*) AS cnt {base}', params)
            total = c.fetchone()['cnt']

            c.execute(
                f'''SELECT s.id, s.lotname, s.password, s.all_quizzes, s.created_at
                    {base} ORDER BY s.lotname ASC LIMIT %s OFFSET %s''',
                params + [per_page, offset],
            )
            teams = c.fetchall()

            for team in teams:
                if team['all_quizzes']:
                    query = '''SELECT qt.id, qt.name, COALESCE(tqs.status, 'not_attempted') AS status
                            FROM quiz_types qt
                            LEFT JOIN team_quiz_status tqs
                                ON tqs.student_id = %s AND tqs.quiz_type_id = qt.id
                            WHERE 1=1'''
                    qparams = [team['id']]
                else:
                    query = '''SELECT qt.id, qt.name, COALESCE(tqs.status, 'not_attempted') AS status
                            FROM team_quiz_assignments tqa
                            JOIN quiz_types qt ON qt.id = tqa.quiz_type_id
                            LEFT JOIN team_quiz_status tqs
                                ON tqs.student_id = tqa.student_id AND tqs.quiz_type_id = qt.id
                            WHERE tqa.student_id = %s'''
                    qparams = [team['id']]
                if quiz_type_id:
                    query += ' AND qt.id = %s'
                    qparams.append(quiz_type_id)
                query += ' ORDER BY qt.name'
                c.execute(query, qparams)
                team['quiz_statuses'] = c.fetchall()

            total_pages = max(1, (total + per_page - 1) // per_page)
            return teams, total, total_pages
    @staticmethod
    def get_by_id(student_id):
        with get_db() as (_, c):
            c.execute('SELECT * FROM students WHERE id = %s', (student_id,))
            team = c.fetchone()
            if team:
                c.execute(
                    'SELECT quiz_type_id FROM team_quiz_assignments WHERE student_id = %s',
                    (student_id,),
                )
                team['assigned_quiz_ids'] = [r['quiz_type_id'] for r in c.fetchall()]
            return team

    @staticmethod
    def create_team(lotname, all_quizzes=False, quiz_type_ids=None):
        lotname = lotname.strip()
        if not lotname:
            return False, 'Team name is required.', 0
        password = TeamService.default_password(lotname)
        with get_db() as (_, c):
            c.execute('SELECT id FROM students WHERE lotname = %s', (lotname,))
            if c.fetchone():
                return False, 'Team already exists.', 0
            c.execute(
                'INSERT INTO students (lotname, password, all_quizzes) VALUES (%s, %s, %s)',
                (lotname, password, all_quizzes),
            )
            student_id = c.lastrowid
            TeamService._sync_assignments(c, student_id, all_quizzes, quiz_type_ids or [])
            return True, 'Team added successfully.', student_id

    @staticmethod
    def update_team(student_id, lotname, all_quizzes=False, quiz_type_ids=None):
        lotname = lotname.strip()
        if not lotname:
            return False, 'Team name is required.'
        password = TeamService.default_password(lotname)
        with get_db() as (_, c):
            c.execute(
                'SELECT id FROM students WHERE lotname = %s AND id != %s',
                (lotname, student_id),
            )
            if c.fetchone():
                return False, 'Team name already exists.'
            c.execute(
                'UPDATE students SET lotname=%s, password=%s, all_quizzes=%s WHERE id=%s',
                (lotname, password, all_quizzes, student_id),
            )
            TeamService._sync_assignments(c, student_id, all_quizzes, quiz_type_ids or [])
            return True, 'Team updated successfully.'

    @staticmethod
    def delete_team(student_id):
        with get_db() as (_, c):
            c.execute('DELETE FROM students WHERE id = %s', (student_id,))
            return True

    @staticmethod
    def _sync_assignments(cursor, student_id, all_quizzes, quiz_type_ids):
        cursor.execute('DELETE FROM team_quiz_assignments WHERE student_id = %s', (student_id,))
        if not all_quizzes and quiz_type_ids:
            for qid in quiz_type_ids:
                cursor.execute(
                    'INSERT IGNORE INTO team_quiz_assignments (student_id, quiz_type_id) VALUES (%s, %s)',
                    (student_id, int(qid)),
                )
        cursor.execute('SELECT id FROM quiz_types')
        for qt in cursor.fetchall():
            cursor.execute(
                '''INSERT IGNORE INTO team_quiz_status (student_id, quiz_type_id, status)
                   VALUES (%s, %s, 'not_attempted')''',
                (student_id, qt['id']),
            )

    @staticmethod
    def ensure_quiz_status(student_id, quiz_type_id):
        with get_db() as (_, c):
            c.execute(
                '''INSERT IGNORE INTO team_quiz_status (student_id, quiz_type_id, status)
                   VALUES (%s, %s, 'not_attempted')''',
                (student_id, quiz_type_id),
            )

        with get_db() as (_, c):
            c.execute(
                'SELECT all_quizzes FROM students WHERE id = %s',
                (student_id,),
            )
            team = c.fetchone()
            if not team:
                return False
            if team['all_quizzes']:
                return True
            c.execute(
                '''SELECT 1 FROM team_quiz_assignments
                   WHERE student_id = %s AND quiz_type_id = %s''',
                (student_id, quiz_type_id),
            )
            return c.fetchone() is not None

    @staticmethod
    def is_eligible(student_id, quiz_type_id):
        with get_db() as (_, c):
            c.execute(
                '''SELECT id, status, allow_reattempt
                   FROM quiz_types WHERE id = %s''',
                (quiz_type_id,),
            )
            quiz_type = c.fetchone()
            if not quiz_type:
                return False, 'Quiz type not found.'
            if quiz_type['status'] != 'active':
                return False, 'Quiz type is not active.'

            c.execute('SELECT id, all_quizzes FROM students WHERE id = %s', (student_id,))
            team = c.fetchone()
            if not team:
                return False, 'Team not found.'

            if not team['all_quizzes']:
                c.execute(
                    '''SELECT 1 FROM team_quiz_assignments
                       WHERE student_id = %s AND quiz_type_id = %s''',
                    (student_id, quiz_type_id),
                )
                if not c.fetchone():
                    return False, 'Team is not registered for this Quiz Type.'

            c.execute(
                '''SELECT status, session_token FROM team_quiz_status
                   WHERE student_id = %s AND quiz_type_id = %s''',
                (student_id, quiz_type_id),
            )
            status_row = c.fetchone()
            if status_row:
                if status_row['status'] == 'completed' and not quiz_type['allow_reattempt']:
                    return False, 'Quiz already completed.'
                if status_row['status'] == 'in_progress' and status_row.get('session_token'):
                    return False, 'An active session already exists for this quiz.'

            return True, None

    @staticmethod
    def get_quiz_status(student_id, quiz_type_id):
        with get_db() as (_, c):
            c.execute(
                '''SELECT status, session_token FROM team_quiz_status
                   WHERE student_id = %s AND quiz_type_id = %s''',
                (student_id, quiz_type_id),
            )
            return c.fetchone()

    @staticmethod
    def upload_from_excel(file, quiz_type_id=None, assign_all=False):
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return False, [], ['Please upload a valid .xlsx, .xls, or .csv file.']
        except Exception as e:
            return False, [], [f'Error reading file: {e}']

        df.columns = [str(c).strip().lower() for c in df.columns]
        col = None
        for candidate in ['lotname', 'team_name', 'team', 'lot name', 'team name']:
            if candidate in df.columns:
                col = candidate
                break
        if not col:
            return False, [], ['Missing required column: lotname (or team_name).']

        added, skipped, errors = 0, 0, []
        with get_db() as (_, c):
            c.execute('SELECT lotname FROM students')
            existing = {r['lotname'] for r in c.fetchall()}
            seen_in_file = set()

            for index, row in df.iterrows():
                lotname = str(row[col]).strip()
                if not lotname or lotname.lower() == 'nan':
                    errors.append(f'Row {index + 2}: Empty team name.')
                    skipped += 1
                    continue
                if lotname in existing or lotname in seen_in_file:
                    errors.append(f'Row {index + 2}: Duplicate team "{lotname}".')
                    skipped += 1
                    continue
                seen_in_file.add(lotname)
                password = TeamService.default_password(lotname)
                c.execute(
                    'INSERT INTO students (lotname, password, all_quizzes) VALUES (%s, %s, %s)',
                    (lotname, password, assign_all),
                )
                student_id = c.lastrowid
                if not assign_all and quiz_type_id:
                    c.execute(
                        'INSERT INTO team_quiz_assignments (student_id, quiz_type_id) VALUES (%s, %s)',
                        (student_id, quiz_type_id),
                    )
                c.execute('SELECT id FROM quiz_types')
                for qt in c.fetchall():
                    c.execute(
                        '''INSERT IGNORE INTO team_quiz_status (student_id, quiz_type_id, status)
                           VALUES (%s, %s, 'not_attempted')''',
                        (student_id, qt['id']),
                    )
                existing.add(lotname)
                added += 1

        return True, {'added': added, 'skipped': skipped}, errors

    @staticmethod
    def sync_from_api():
        import requests
        import logging
        try:
            response = requests.get('https://anjacstrata.in/mob/get_isused_lots.php', timeout=30)
            response.raise_for_status()
            teams_data = response.json()
        except Exception as e:
            return False, str(e), 0, 0

        teams_list = []
        if isinstance(teams_data, list):
            teams_list = teams_data
        elif isinstance(teams_data, dict):
            for key in ['data', 'teams', 'lots', 'records']:
                if key in teams_data and isinstance(teams_data[key], list):
                    teams_list = teams_data[key]
                    break

        added, skipped = 0, 0
        with get_db() as (_, c):
            c.execute('SELECT lotname FROM students')
            existing = {r['lotname'] for r in c.fetchall()}
            for team in teams_list:
                if not isinstance(team, dict) or 'lotname' not in team:
                    skipped += 1
                    continue
                lotname = str(team['lotname']).strip()
                if lotname in existing:
                    skipped += 1
                    continue
                password = TeamService.default_password(lotname)
                c.execute(
                    'INSERT INTO students (lotname, password, all_quizzes) VALUES (%s, %s, 1)',
                    (lotname, password),
                )
                student_id = c.lastrowid
                c.execute('SELECT id FROM quiz_types')
                for qt in c.fetchall():
                    c.execute(
                        '''INSERT IGNORE INTO team_quiz_status (student_id, quiz_type_id, status)
                           VALUES (%s, %s, 'not_attempted')''',
                        (student_id, qt['id']),
                    )
                existing.add(lotname)
                added += 1
        return True, None, added, skipped
    @staticmethod
    def toggle_quiz_status(student_id, quiz_type_id):
        with get_db() as (_, c):
            c.execute(
                'SELECT status FROM team_quiz_status WHERE student_id = %s AND quiz_type_id = %s',
                (student_id, quiz_type_id),
            )
            row = c.fetchone()
            if not row:
                return False, 'Status record not found.'
            new_status = 'not_attempted' if row['status'] == 'completed' else 'completed'
            c.execute(
                '''UPDATE team_quiz_status SET status = %s, session_token = NULL
                WHERE student_id = %s AND quiz_type_id = %s''',
                (new_status, student_id, quiz_type_id),
            )
            return True, f'Status updated to {new_status}.'

    @staticmethod
    def delete_all_teams():
        with get_db() as (_, c):
            c.execute('DELETE FROM students')
            return True, 'All teams deleted.'
