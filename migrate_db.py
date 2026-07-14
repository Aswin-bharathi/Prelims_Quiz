"""Initialize or update the modular MySQL database schema.

This project now uses the schema declared in app/db_init.py. Run this script
from the Prelims_Quiz/Prelims directory after configuring DB_* settings.
"""

from app.db_init import init_db

def migrate_db():
    init_db()
    print('MySQL database schema is up to date.')

if __name__ == '__main__':
    migrate_db()
