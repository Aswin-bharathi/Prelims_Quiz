import time
from app.database import get_db


class MonitoringService:

    @staticmethod
    def get_live_data():
        with get_db() as (_, c):
            c.execute("SELECT * FROM quiz_types ORDER BY name ASC")
            quiz_types = c.fetchall()
            monitoring = []

            for qt in quiz_types:
                quiz_type_id = qt['id']

                c.execute(
                    '''SELECT COUNT(DISTINCT s.id) AS cnt FROM students s
                       LEFT JOIN team_quiz_assignments tqa ON tqa.student_id = s.id
                       WHERE s.all_quizzes = 1 OR tqa.quiz_type_id = %s''',
                    (quiz_type_id,),
                )
                registered = c.fetchone()['cnt']

                c.execute(
                    '''SELECT COUNT(*) AS cnt FROM team_quiz_status
                       WHERE quiz_type_id = %s AND status = 'in_progress' ''',
                    (quiz_type_id,),
                )
                active = c.fetchone()['cnt']

                c.execute(
                    '''SELECT COUNT(*) AS cnt FROM team_quiz_status
                       WHERE quiz_type_id = %s AND status = 'completed' ''',
                    (quiz_type_id,),
                )
                completed = c.fetchone()['cnt']

                remaining = max(0, registered - completed - active)

                c.execute(
                    '''SELECT AVG(current_question) AS avg_q, MAX(current_question) AS max_q
                       FROM team_quiz_status
                       WHERE quiz_type_id = %s AND status = 'in_progress' ''',
                    (quiz_type_id,),
                )
                progress = c.fetchone()
                current_question = int(progress['max_q'] or 0)

                c.execute(
                    '''SELECT MIN(started_at) AS earliest FROM team_quiz_status
                       WHERE quiz_type_id = %s AND status = 'in_progress' AND started_at IS NOT NULL''',
                    (quiz_type_id,),
                )
                earliest = c.fetchone()['earliest']
                remaining_seconds = qt['duration_minutes'] * 60
                if earliest:
                    elapsed = time.time() - earliest.timestamp() if hasattr(earliest, 'timestamp') else 0
                    remaining_seconds = max(0, qt['duration_minutes'] * 60 - int(elapsed))

                monitoring.append({
                    'id': quiz_type_id,
                    'name': qt['name'],
                    'entry_code': qt['entry_code'],
                    'status': qt['status'],
                    'quiz_status': qt['quiz_status'],
                    'question_count': qt['question_count'],
                    'duration_minutes': qt['duration_minutes'],
                    'registered_teams': registered,
                    'active_teams': active,
                    'completed_teams': completed,
                    'remaining_teams': remaining,
                    'current_question': current_question,
                    'remaining_seconds': remaining_seconds,
                })

            return monitoring

    @staticmethod
    def get_active_sessions(quiz_type_id=None):
        with get_db() as (_, c):
            query = '''
                SELECT s.lotname, qt.name AS quiz_name, tqs.current_question,
                       tqs.started_at, tqs.status, qt.duration_minutes
                FROM team_quiz_status tqs
                JOIN students s ON s.id = tqs.student_id
                JOIN quiz_types qt ON qt.id = tqs.quiz_type_id
                WHERE tqs.status = 'in_progress'
            '''
            params = []
            if quiz_type_id:
                query += ' AND tqs.quiz_type_id = %s'
                params.append(quiz_type_id)
            query += ' ORDER BY tqs.started_at DESC'
            c.execute(query, params)
            return c.fetchall()
