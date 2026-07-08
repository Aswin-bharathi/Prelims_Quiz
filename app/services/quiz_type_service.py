from app.database import get_db
from app.utils.formatting import slugify
from app.utils.validation import validate_quiz_type_form


class QuizTypeService:

    @staticmethod
    def get_all(active_only=False):
        with get_db() as (_, c):
            query = 'SELECT * FROM quiz_types'
            if active_only:
                query += " WHERE status = 'active'"
            query += ' ORDER BY name ASC'
            c.execute(query)
            return c.fetchall()

    @staticmethod
    def get_by_id(quiz_type_id):
        with get_db() as (_, c):
            c.execute('SELECT * FROM quiz_types WHERE id = %s', (quiz_type_id,))
            return c.fetchone()

    @staticmethod
    def get_by_entry_code(entry_code):
        with get_db() as (_, c):
            c.execute(
                'SELECT * FROM quiz_types WHERE entry_code = %s',
                (entry_code.strip(),),
            )
            return c.fetchone()

    @staticmethod
    def create(data):
        valid, msg = validate_quiz_type_form(
            data['name'], data['question_count'], data['duration_minutes'], data['entry_code']
        )
        if not valid:
            return False, msg
        slug = slugify(data['name'])
        with get_db() as (_, c):
            c.execute('SELECT id FROM quiz_types WHERE slug = %s OR entry_code = %s', (slug, data['entry_code'].strip()))
            if c.fetchone():
                return False, 'Quiz type with this name or entry code already exists.'
            c.execute(
                '''INSERT INTO quiz_types
                   (name, slug, description, question_count, duration_minutes, entry_code, status, allow_reattempt)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (
                    data['name'].strip(),
                    slug,
                    (data.get('description') or '').strip() or None,
                    int(data['question_count']),
                    int(data['duration_minutes']),
                    data['entry_code'].strip().upper(),
                    data.get('status', 'inactive'),
                    bool(data.get('allow_reattempt')),
                ),
            )
            return True, c.lastrowid

    @staticmethod
    def update(quiz_type_id, data):
        valid, msg = validate_quiz_type_form(
            data['name'], data['question_count'], data['duration_minutes'], data['entry_code']
        )
        if not valid:
            return False, msg
        slug = slugify(data['name'])
        with get_db() as (_, c):
            c.execute(
                'SELECT id FROM quiz_types WHERE (slug = %s OR entry_code = %s) AND id != %s',
                (slug, data['entry_code'].strip(), quiz_type_id),
            )
            if c.fetchone():
                return False, 'Another quiz type uses this name or entry code.'
            c.execute(
                '''UPDATE quiz_types SET name=%s, slug=%s, description=%s, question_count=%s,
                   duration_minutes=%s, entry_code=%s, status=%s, allow_reattempt=%s WHERE id=%s''',
                (
                    data['name'].strip(),
                    slug,
                    (data.get('description') or '').strip() or None,
                    int(data['question_count']),
                    int(data['duration_minutes']),
                    data['entry_code'].strip().upper(),
                    data.get('status', 'inactive'),
                    bool(data.get('allow_reattempt')),
                    quiz_type_id,
                ),
            )
            return True, None

    @staticmethod
    def delete(quiz_type_id):
        with get_db() as (_, c):
            c.execute('DELETE FROM quiz_types WHERE id = %s', (quiz_type_id,))
            return True

    @staticmethod
    def toggle_status(quiz_type_id):
        with get_db() as (_, c):
            c.execute('SELECT status FROM quiz_types WHERE id = %s', (quiz_type_id,))
            row = c.fetchone()
            if not row:
                return False, 'Quiz type not found.'
            new_status = 'inactive' if row['status'] == 'active' else 'active'
            c.execute('UPDATE quiz_types SET status = %s WHERE id = %s', (new_status, quiz_type_id))
            return True, new_status

    @staticmethod
    def set_quiz_status(quiz_type_id, quiz_status):
        with get_db() as (_, c):
            c.execute('UPDATE quiz_types SET quiz_status = %s WHERE id = %s', (quiz_status, quiz_type_id))
            return True

    @staticmethod
    def get_dashboard_stats():
        with get_db() as (_, c):
            c.execute('SELECT COUNT(*) AS cnt FROM quiz_types')
            quiz_types = c.fetchone()['cnt']
            c.execute('SELECT COUNT(*) AS cnt FROM students')
            teams = c.fetchone()['cnt']
            c.execute('SELECT COUNT(*) AS cnt FROM questions')
            questions = c.fetchone()['cnt']
            c.execute('SELECT COUNT(*) AS cnt FROM results')
            results = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) AS cnt FROM quiz_types WHERE status = 'active'")
            active_quizzes = c.fetchone()['cnt']
            return {
                'quiz_types': quiz_types,
                'teams': teams,
                'questions': questions,
                'results': results,
                'active_quizzes': active_quizzes,
            }
