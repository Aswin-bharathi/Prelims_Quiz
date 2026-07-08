# Intercollege Quiz Platform

A modern, high-performance, and responsive web application built with Flask and MySQL for hosting and managing intercollegiate quiz competitions. The administration panel features a premium AJAX-driven SPA architecture, real-time live monitoring, and auto-refreshing leaderboards.

---

## 🚀 Key Features

*   **Premium AJAX Dashboard:** Fully asynchronous Single Page Application (SPA) administration interface. Navigation, CRUD actions, search filters, and updates happen instantly without page reloads.
*   **Persistent Interface State:** AJAX navigation automatically preserves search input cursor positions, focus states, and the scroll offsets of data tables.
*   **Real-time Live Monitoring:** Auto-refreshing view (every 3 seconds) displaying active teams, current question progress, and remaining time.
*   **Shared Rank Leaderboards:** Standard leaderboard ranking (e.g., Rank 1, 2, 2, 4) calculated by highest score first, then least time taken. Supports Top N filtering and auto-refreshes every 3 seconds.
*   **Interactive Management:** Add, edit, delete, enable/disable, and start/stop quiz types, questions, and teams dynamically.
*   **Excel Imports:** Upload team registrations and question banks in batch formats from Excel files.
*   **Light/Dark Theme Toggle:** Full dark and light mode coverage across all widgets, tables, and settings, persisting across navigation.
*   **Student Quiz View:** Clean, interactive interface for student team attempts with tab-switch warnings and time tracking.

---

## 🛠️ Prerequisites

*   **Python 3.8+** installed on your system.
*   **MySQL Server** running locally or accessible via network.
*   **Microsoft Excel / LibreOffice Calc** (for preparing team and question sheets).

---

## ⚙️ Installation & Setup

Follow these steps to set up the project on a new machine:

### 1. Clone the Repository
```bash
git clone https://github.com/Aswin-bharathi/Prelims_Quiz.git
cd Prelims_Quiz/Prelims
```

### 2. Configure Python Virtual Environment
Create a Python virtual environment and activate it:

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
Install all package requirements:
```bash
pip install -r requirements.txt
```

### 4. Configure Database
Ensure MySQL Server is running. Create the database schema.

**Option A (Using MySQL Terminal):**
```bash
mysql -u root -p
# Enter your password, then run:
CREATE DATABASE IF NOT EXISTS quiz_db;
```
Once the database is created, import the schema:
```bash
mysql -u root -p quiz_db < quiz_db_schema.sql
```

**Option B (Using Python Script):**
Create the database and run:
```bash
python setup_db.py
```

---

## 🔒 Configuration

You can customize the application's configuration by setting environment variables. If not set, the platform falls back to the defaults defined in `app/config.py`:

| Variable Name | Description | Default Value |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session encrypting key | `intercollege_event_2025` |
| `DB_HOST` | MySQL Server host | `localhost` |
| `DB_USER` | MySQL Username | `root` |
| `DB_PASSWORD` | MySQL Password | `aswin2772` |
| `DB_NAME` | MySQL Database Name | `quiz_db` |
| `ADMIN_USER` | Admin dashboard username | `admin` |
| `ADMIN_PASS` | Admin dashboard password | `admin@123#` |
| `PASSWORD_SUFFIX` | Suffix appended to team passwords | `@2k26` |
| `PER_PAGE` | Pagination count (where applicable) | `10` |
| `MONITORING_POLL_MS` | Real-time polling rate (milliseconds) | `3000` |

To set them on Linux/macOS, use:
```bash
export DB_PASSWORD="your_new_password"
export ADMIN_PASS="your_admin_password"
```

---

## 🏃 Running the Application

Start the Flask development server:
```bash
python app.py
```

By default, the server runs on:
*   **Admin Dashboard Login:** [http://localhost:5000/admin/login](http://localhost:5000/admin/login)
*   **Student Quiz Portal:** [http://localhost:5000/quiz_login](http://localhost:5000/quiz_login)

### Default Admin Credentials
*   **Username:** `admin`
*   **Password:** `admin@123#`

---

## 📝 Running Tests
Verify database compatibility and endpoint route functionality:
```bash
venv/bin/python3 -m unittest tests/test_db_migration.py
```
