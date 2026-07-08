import mysql.connector
from contextlib import contextmanager
from app.config import Config


@contextmanager
def get_db():
    conn = mysql.connector.connect(**Config.db_config())
    cursor = conn.cursor(dictionary=True)
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_connection():
    return mysql.connector.connect(**Config.db_config())
