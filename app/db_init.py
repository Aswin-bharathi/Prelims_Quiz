import logging
import re
from werkzeug.security import generate_password_hash
from app.config import Config
from app.database import get_connection

logger = logging.getLogger(__name__)

SCHEMA_SQL = [
    '''CREATE TABLE IF NOT EXISTS quiz_types (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        question_count INT NOT NULL DEFAULT 15,
        duration_minutes INT NOT NULL DEFAULT 15,
        entry_code VARCHAR(100) NOT NULL UNIQUE,
        status ENUM('active', 'inactive') DEFAULT 'inactive',
        allow_reattempt BOOLEAN DEFAULT FALSE,
        quiz_status ENUM('scheduled', 'running', 'ended') DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        lotname VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        all_quizzes BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS team_quiz_assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        quiz_type_id INT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_type_id) REFERENCES quiz_types(id) ON DELETE CASCADE,
        UNIQUE KEY unique_assignment (student_id, quiz_type_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS team_quiz_status (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        quiz_type_id INT NOT NULL,
        status ENUM('not_attempted', 'in_progress', 'completed') DEFAULT 'not_attempted',
        session_token VARCHAR(255),
        current_question INT DEFAULT 0,
        started_at TIMESTAMP NULL,
        completed_at TIMESTAMP NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_type_id) REFERENCES quiz_types(id) ON DELETE CASCADE,
        UNIQUE KEY unique_status (student_id, quiz_type_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS questions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        quiz_type_id INT NOT NULL,
        question TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        answer TEXT NOT NULL,
        FOREIGN KEY (quiz_type_id) REFERENCES quiz_types(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        lotname VARCHAR(255) NOT NULL,
        quiz_type_id INT NOT NULL,
        score INT NOT NULL,
        duration INT NOT NULL,
        total_questions INT NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_type_id) REFERENCES quiz_types(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS settings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        setting_key VARCHAR(100) NOT NULL UNIQUE,
        setting_value TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',

    '''CREATE TABLE IF NOT EXISTS admins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
]


def init_db():
    conn = None
    try:
        conn = get_connection()
        c = conn.cursor(dictionary=True)

        for sql in SCHEMA_SQL:
            c.execute(sql)

        def _column_names(table_name):
            c.execute(
                'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s',
                (Config.DB_NAME, table_name),
            )
            return {row['COLUMN_NAME'] for row in c.fetchall()}

        def _add_column(table_name, column_name, definition_sql):
            if column_name in _column_names(table_name):
                return
            c.execute(f'ALTER TABLE {table_name} ADD COLUMN {definition_sql}')
            logger.info('Added column %s.%s', table_name, column_name)

        _add_column('students', 'all_quizzes', 'all_quizzes BOOLEAN DEFAULT FALSE')
        _add_column('students', 'quiz_status_tech', "quiz_status_tech VARCHAR(50) DEFAULT 'not_attempted'")
        _add_column('students', 'quiz_status_software', "quiz_status_software VARCHAR(50) DEFAULT 'not_attempted'")
        _add_column('students', 'created_at', 'created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP')
        _add_column('questions', 'quiz_type_id', 'quiz_type_id INT NULL')
        _add_column('results', 'student_id', 'student_id INT NULL')
        _add_column('results', 'quiz_type_id', 'quiz_type_id INT NULL')
        _add_column('results', 'total_questions', 'total_questions INT NOT NULL DEFAULT 0')
        _add_column('results', 'completed_at', 'completed_at TIMESTAMP NULL')

        c.execute('SELECT COUNT(*) AS cnt FROM admins')
        if c.fetchone()['cnt'] == 0:
            default_password = generate_password_hash(Config.DEFAULT_ADMIN_PASS)
            c.execute(
                'INSERT IGNORE INTO admins (username, password) VALUES (%s, %s)',
                (Config.DEFAULT_ADMIN_USER, default_password),
            )

        c.execute('SELECT COUNT(*) AS cnt FROM quiz_types')
        if c.fetchone()['cnt'] == 0:
            defaults = []
            for name, slug, desc, qc, dm, code in defaults:
                c.execute(
                    '''INSERT INTO quiz_types
                       (name, slug, description, question_count, duration_minutes, entry_code, status)
                       VALUES (%s, %s, %s, %s, %s, %s, 'inactive')''',
                    (name, slug, desc, qc, dm, code),
                )

        c.execute('SELECT id, name FROM quiz_types')
        quiz_types = c.fetchall()

        def _resolve_quiz_type_id(raw_name):
            if not quiz_types:
                return None
            normalized = re.sub(r'[^a-z0-9]+', ' ', str(raw_name or '')).strip().lower()
            if not normalized:
                return quiz_types[0]['id']
            for quiz_type in quiz_types:
                name = re.sub(r'[^a-z0-9]+', ' ', quiz_type['name']).strip().lower()
                if 'technical' in normalized and 'technical' in name:
                    return quiz_type['id']
                if 'aptitude' in normalized and 'aptitude' in name:
                    return quiz_type['id']
                if ('general' in normalized or 'knowledge' in normalized or 'gk' in normalized) and ('general' in name or 'knowledge' in name):
                    return quiz_type['id']
            return quiz_types[0]['id']

        question_columns = _column_names('questions')
        if 'quiz_type' in question_columns:
            c.execute('SELECT id, quiz_type FROM questions WHERE quiz_type_id IS NULL')
            for question in c.fetchall():
                quiz_type_id = _resolve_quiz_type_id(question['quiz_type'])
                if quiz_type_id is not None:
                    c.execute('UPDATE questions SET quiz_type_id = %s WHERE id = %s', (quiz_type_id, question['id']))

        c.execute('SELECT id, lotname FROM students')
        student_id_map = {row['lotname']: row['id'] for row in c.fetchall()}

        result_columns = _column_names('results')
        if 'quiz_type' in result_columns:
            c.execute('SELECT id, lotname, quiz_type FROM results WHERE student_id IS NULL OR quiz_type_id IS NULL')
            for result in c.fetchall():
                quiz_type_id = _resolve_quiz_type_id(result['quiz_type'])
                student_id = student_id_map.get(result['lotname'])
                c.execute(
                    'UPDATE results SET student_id = %s, quiz_type_id = %s WHERE id = %s',
                    (student_id, quiz_type_id, result['id']),
                )

        c.execute('SELECT id FROM students')
        student_ids = [row['id'] for row in c.fetchall()]
        c.execute('SELECT id FROM quiz_types')
        quiz_type_ids = [row['id'] for row in c.fetchall()]
        for student_id in student_ids:
            for quiz_type_id in quiz_type_ids:
                c.execute(
                    'INSERT IGNORE INTO team_quiz_status (student_id, quiz_type_id, status) VALUES (%s, %s, %s)',
                    (student_id, quiz_type_id, 'not_attempted'),
                )

        c.execute('''
            INSERT IGNORE INTO settings (setting_key, setting_value) VALUES
            ('app_name', 'Intercollege Quiz Platform'),
            ('tab_switch_limit', '1'),
            ('prevent_copy', '1')
        ''')

        conn.commit()
        logger.info('Database initialized successfully.')
    except Exception as e:
        logger.error(f'Database init error: {e}')
        raise
    finally:
        if conn and conn.is_connected():
            c.close()
            conn.close()
