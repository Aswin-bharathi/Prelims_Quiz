import io
import pandas as pd
from docx import Document
from app.database import get_db
from app.utils.formatting import format_duration


class ResultService:

    @staticmethod
    def _announcement_key(prefix, quiz_type_id=None):
        if quiz_type_id is not None:
            return f'{prefix}:{quiz_type_id}'
        return prefix

    @staticmethod
    def set_announcement_state(is_released, top_n=None, quiz_type_id=None):
        with get_db() as (_, c):
            released_key = ResultService._announcement_key('results_announced', quiz_type_id)
            c.execute(
                '''INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)''',
                (released_key, '1' if is_released else '0'),
            )
            if top_n is not None:
                top_n_key = ResultService._announcement_key('results_top_n', quiz_type_id)
                c.execute(
                    '''INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)
                       ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)''',
                    (top_n_key, str(top_n)),
                )

    @staticmethod
    def get_announcement_state(quiz_type_id=None):
        with get_db() as (_, c):
            key = ResultService._announcement_key('results_announced', quiz_type_id)
            c.execute('SELECT setting_value FROM settings WHERE setting_key = %s', (key,))
            row = c.fetchone()
            if row and row['setting_value'] is not None:
                return row['setting_value'] == '1'
            fallback_key = ResultService._announcement_key('results_announced', None)
            c.execute('SELECT setting_value FROM settings WHERE setting_key = %s', (fallback_key,))
            row = c.fetchone()
            return bool(row and row['setting_value'] == '1')

    @staticmethod
    def get_announcement_top_n(quiz_type_id=None):
        with get_db() as (_, c):
            key = ResultService._announcement_key('results_top_n', quiz_type_id)
            c.execute('SELECT setting_value FROM settings WHERE setting_key = %s', (key,))
            row = c.fetchone()
            if row and row['setting_value'] is not None:
                try:
                    return int(row['setting_value'])
                except (TypeError, ValueError):
                    pass
            fallback_key = ResultService._announcement_key('results_top_n', None)
            c.execute('SELECT setting_value FROM settings WHERE setting_key = %s', (fallback_key,))
            row = c.fetchone()
            if row and row['setting_value'] is not None:
                try:
                    return int(row['setting_value'])
                except (TypeError, ValueError):
                    pass
            return 5

    @staticmethod
    def is_team_selected(lotname, quiz_type_id=None, top_n=None):
        if not lotname:
            return False
        resolved_top_n = top_n if top_n is not None else ResultService.get_announcement_top_n(quiz_type_id)
        leaderboard = ResultService.get_leaderboard(quiz_type_id, resolved_top_n)
        return any(team['lotname'] == lotname for team in leaderboard)

    @staticmethod
    def get_results(page=1, per_page=10, search='', quiz_type_id=None):
        offset = (page - 1) * per_page
        with get_db() as (_, c):
            base = '''
                FROM results r
                JOIN students s ON s.id = r.student_id
                JOIN quiz_types qt ON qt.id = r.quiz_type_id
                WHERE 1=1
            '''
            params = []
            if quiz_type_id:
                base += ' AND r.quiz_type_id = %s'
                params.append(quiz_type_id)
            if search:
                base += ' AND r.lotname LIKE %s'
                params.append(f'%{search}%')

            c.execute(f'SELECT COUNT(*) AS cnt {base}', params)
            total = c.fetchone()['cnt']

            c.execute(
                f'''SELECT r.*, qt.name AS quiz_type_name, s.lotname
                    {base}
                    ORDER BY r.score DESC, r.duration ASC, r.lotname ASC
                    LIMIT %s OFFSET %s''',
                params + [per_page, offset],
            )
            results = c.fetchall()

            for r in results:
                r['duration_formatted'] = format_duration(r['duration'])

            total_pages = max(1, (total + per_page - 1) // per_page)
            return results, total, total_pages

    @staticmethod
    def get_leaderboard(quiz_type_id=None, limit=5):
        with get_db() as (_, c):
            query = '''
                SELECT r.lotname, r.score, r.duration, qt.name AS quiz_type_name,
                       r.quiz_type_id, r.total_questions
                FROM results r
                JOIN quiz_types qt ON qt.id = r.quiz_type_id
            '''
            params = []
            if quiz_type_id:
                query += ' WHERE r.quiz_type_id = %s'
                params.append(quiz_type_id)
            query += ' ORDER BY r.score DESC, r.duration ASC, r.lotname ASC LIMIT %s'
            params.append(limit)
            c.execute(query, params)
            rows = c.fetchall()
            for i, row in enumerate(rows):
                if i > 0 and row['score'] == rows[i-1]['score'] and row['duration'] == rows[i-1]['duration']:
                    row['rank'] = rows[i-1]['rank']
                else:
                    row['rank'] = i + 1
                row['duration_formatted'] = format_duration(row['duration'])
            return rows

    @staticmethod
    def get_ranked_results(page=1, per_page=10, search='', quiz_type_id=None):
        results, total, total_pages = ResultService.get_results(page, per_page, search, quiz_type_id)
        for i, r in enumerate(results):
            if i > 0 and r['score'] == results[i-1]['score'] and r['duration'] == results[i-1]['duration']:
                r['rank'] = results[i-1]['rank']
            else:
                r['rank'] = i + 1
        return results, total, total_pages

    @staticmethod
    def export_word(quiz_type_id=None, top_n=5):
        top = ResultService.get_leaderboard(quiz_type_id, top_n)
        doc = Document()
        title = f'Top {top_n} Teams - All Quizzes' if not quiz_type_id else f'Top {top_n} Teams - {top[0]["quiz_type_name"] if top else "Quiz"}'
        doc.add_heading(title, 0)
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        headers = ['Rank', 'Team Name', 'Quiz Type', 'Score', 'Time Taken']
        for i, h in enumerate(headers):
            table.rows[0].cells[i].text = h
        for row in top:
            cells = table.add_row().cells
            cells[0].text = str(row['rank'])
            cells[1].text = row['lotname']
            cells[2].text = row['quiz_type_name']
            cells[3].text = str(row['score'])
            cells[4].text = row['duration_formatted']
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output

    @staticmethod
    def export_excel(quiz_type_id=None, search=''):
        results, _, _ = ResultService.get_results(page=1, per_page=100000, search=search, quiz_type_id=quiz_type_id)
        df = pd.DataFrame([
            {
                'Rank': i + 1,
                'Team': r['lotname'],
                'Quiz Type': r['quiz_type_name'],
                'Score': r['score'],
                'Total Questions': r['total_questions'],
                'Duration': r['duration_formatted'],
            }
            for i, r in enumerate(results)
        ])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Results')
        output.seek(0)
        return output
