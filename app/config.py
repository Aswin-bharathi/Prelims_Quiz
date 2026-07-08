import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'intercollege_event_2025')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '8305')
    DB_NAME = os.environ.get('DB_NAME', 'quiz_db')
    DEFAULT_ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
    DEFAULT_ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin@123#')
    PASSWORD_SUFFIX = os.environ.get('PASSWORD_SUFFIX', '@2k26')
    PER_PAGE = int(os.environ.get('PER_PAGE', 10))
    MONITORING_POLL_MS = int(os.environ.get('MONITORING_POLL_MS', 3000))

    @classmethod
    def db_config(cls):
        return {
            'host': cls.DB_HOST,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
        }
