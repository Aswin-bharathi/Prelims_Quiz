# Database Setup Guide

## Prerequisites
- MySQL Server installed and running
- MySQL command-line client or GUI tool (like MySQL Workbench)

## Setup Instructions

### Option 1: Using MySQL Command Line

1. **Open MySQL terminal:**
   ```bash
   mysql -u root -p
   ```
   (Leave password empty if you don't have one set)

2. **Run the SQL schema file:**
   ```bash
   mysql -u root < quiz_db_schema.sql
   ```

3. **Verify database creation:**
   ```bash
   mysql -u root -e "USE quiz_db; SHOW TABLES;"
   ```

### Option 2: Using MySQL GUI
1. Open MySQL Workbench or your preferred MySQL GUI
2. Open the file `quiz_db_schema.sql`
3. Execute the script

### Option 3: Programmatically
Run the Python setup script (after creating `setup_db.py`):
```bash
python setup_db.py
```

## Database Schema

The database includes 5 tables:

1. **students** - Team/Student login credentials
   - lotname (unique identifier)
   - password
   - quiz_status_tech
   - quiz_status_software

2. **questions** - Quiz questions
   - quiz_type (Tech/Software)
   - question, option1-4, answer

3. **quiz_entries** - Entry codes for quizzes
   - entry_code
   - quiz_type

4. **results** - Quiz results
   - lotname, score, duration, quiz_type

5. **admins** - Admin credentials
   - username, password

## Verify Setup
After setup, run your Flask app:
```bash
source env/bin/activate
python app.py
```

You should see database initialization without errors.
