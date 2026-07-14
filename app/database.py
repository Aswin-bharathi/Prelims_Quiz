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
    try:
        conn = mysql.connector.connect(**Config.db_config())
        print("✅ Connected Successfully")
        return conn
    except mysql.connector.Error as e:
        print("ERROR NO :", e.errno)
        print("ERROR MSG:", e.msg)
        raise
