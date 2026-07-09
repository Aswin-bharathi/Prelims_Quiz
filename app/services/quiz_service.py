import secrets
import time
from app.database import get_db
from app.services.question_service import QuestionService
from app.services.team_service import TeamService
from app.services.quiz_type_service import QuizTypeService


class QuizService:

    @staticmethod
    def authenticate(lotname, password, entry_code):
        quiz_type = QuizTypeService.get_by_entry_code(entry_code)
        if not quiz_type:
            return False, 'Invalid Entry Code!', None

        if quiz_type['status'] != 'active':
            return False, 'Quiz type is not active.', None

        if quiz_type['quiz_status'] == 'scheduled':
            return False, 'Quiz has not started yet.', None

        with get_db() as (_, c):
            c.execute(
                '''SELECT * FROM students
                   WHERE LOWER(REPLACE(TRIM(lotname), ' ', '')) = %s
                     AND LOWER(REPLACE(TRIM(password), ' ', '')) = %s''',
                (lotname, password),
            )
            team = c.fetchone()
            if not team:
                return False, 'Incorrect team name or password.', None

            eligible, eligibility_msg = TeamService.is_eligible(team['id'], quiz_type['id'])
            if not eligible:
                return False, eligibility_msg, None

            TeamService.ensure_quiz_status(team['id'], quiz_type['id'])

            if quiz_type['quiz_status'] == 'ended':
                return False, 'Quiz has already ended.', None

            return True, None, {
                'id': team['id'],
                'lotname': team['lotname'],
                'quiz_type_id': quiz_type['id'],
                'quiz_type_name': quiz_type['name'],
                'question_count': quiz_type['question_count'],
                'duration_minutes': quiz_type['duration_minutes'],
                'description': quiz_type.get('description'),
            }

    @staticmethod
    def initialize_session(team_data):
        quiz_type_id = team_data['quiz_type_id']
        question_count = team_data['question_count']
        available = QuestionService.count_for_quiz(quiz_type_id)
        if available < question_count:
            return False, f'Not enough questions. Need {question_count}, have {available}.', None

        questions = QuestionService.get_for_quiz(quiz_type_id, question_count)
        session_token = secrets.token_hex(32)
        start_time = time.time()

        with get_db() as (_, c):
            c.execute(
                '''INSERT INTO team_quiz_status
                   (student_id, quiz_type_id, status, session_token, current_question, started_at)
                   VALUES (%s, %s, 'in_progress', %s, 1, NOW())
                   ON DUPLICATE KEY UPDATE status='in_progress', session_token=VALUES(session_token),
                   current_question=1, started_at=NOW(), completed_at=NULL''',
                (team_data['id'], quiz_type_id, session_token),
            )
            QuizTypeService.set_quiz_status(quiz_type_id, 'running')

        return True, None, {
            'questions': questions,
            'session_token': session_token,
            'start_time': start_time,
            'duration_seconds': team_data['duration_minutes'] * 60,
            'total_questions': len(questions),
        }

    @staticmethod
    def verify_session(team_session, session_token):
        if not team_session or not session_token:
            return False
        if team_session.get('session_token') != session_token:
            return False
        with get_db() as (_, c):
            c.execute(
                '''SELECT status, session_token FROM team_quiz_status
                   WHERE student_id=%s AND quiz_type_id=%s''',
                (team_session['id'], team_session['quiz_type_id']),
            )
            row = c.fetchone()
            return row and row['status'] == 'in_progress' and row['session_token'] == session_token

    @staticmethod
    def submit_quiz(team_session, answers, questions, start_time):
        score = 0
        for index, q in enumerate(questions, 1):
            q_id = f'q{index}'
            if answers.get(q_id) == q['answer']:
                score += 1

        duration = int(time.time() - start_time)
        quiz_type_id = team_session['quiz_type_id']

        with get_db() as (_, c):
            c.execute(
                '''INSERT INTO results
                   (student_id, lotname, quiz_type_id, score, duration, total_questions)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (
                    team_session['id'],
                    team_session['lotname'],
                    quiz_type_id,
                    score,
                    duration,
                    len(questions),
                ),
            )
            c.execute(
                '''UPDATE team_quiz_status SET status='completed', session_token=NULL,
                   completed_at=NOW(), current_question=%s
                   WHERE student_id=%s AND quiz_type_id=%s''',
                (len(questions), team_session['id'], quiz_type_id),
            )

        return score, duration

    @staticmethod
    def update_progress(team_session, current_question):
        with get_db() as (_, c):
            c.execute(
                '''UPDATE team_quiz_status SET current_question=%s
                   WHERE student_id=%s AND quiz_type_id=%s AND status='in_progress' ''',
                (current_question, team_session['id'], team_session['quiz_type_id']),
            )

    @staticmethod
    def invalidate_session(team_session):
        with get_db() as (_, c):
            c.execute(
                '''UPDATE team_quiz_status SET session_token=NULL, status='not_attempted',
                   current_question=0, started_at=NULL
                   WHERE student_id=%s AND quiz_type_id=%s''',
                (team_session['id'], team_session['quiz_type_id']),
            )
