import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL connection config (without specifying database)
# UPDATE THE PASSWORD HERE IF YOUR MYSQL ROOT USER HAS A PASSWORD
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change '' to your MySQL root password if needed
}

def create_database():
    """Create the quiz_db database and all tables"""
    conn = None
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        logger.info("Connected to MySQL Server")
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS quiz_db")
        logger.info("Database 'quiz_db' created or already exists")
        
        # Use the database
        cursor.execute("USE quiz_db")
        
        # Create students table
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lotname VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            quiz_status_tech VARCHAR(50) DEFAULT 'not_attempted',
            quiz_status_software VARCHAR(50) DEFAULT 'not_attempted'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        logger.info("Table 'students' created")
        
        # Create questions table
        cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            quiz_type VARCHAR(50) NOT NULL,
            question TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            answer TEXT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        logger.info("Table 'questions' created")
        
        # Create quiz_entries table
        cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            entry_code VARCHAR(255) NOT NULL,
            quiz_type VARCHAR(50) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        logger.info("Table 'quiz_entries' created")
        
        # Create results table
        cursor.execute('''CREATE TABLE IF NOT EXISTS results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lotname VARCHAR(255) NOT NULL,
            score INT NOT NULL,
            duration INT NOT NULL,
            quiz_type VARCHAR(50) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        logger.info("Table 'results' created")
        
        # Create admins table
        cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        logger.info("Table 'admins' created")
        
        conn.commit()
        logger.info("✓ Database setup completed successfully!")
        
    except Error as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logger.info("MySQL connection closed")
    
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("Quiz Database Setup")
    print("=" * 50)
    if create_database():
        print("\n✓ Database initialized successfully!")
        print("You can now run: python app.py")
    else:
        print("\n✗ Database setup failed. Check the errors above.")
