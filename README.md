# Django Quiz System

A comprehensive Django-based quiz management system that allows teachers to create quizzes and students to participate in them. The system features user authentication, role-based dashboards, quiz creation, question management, and scoring.

## Features

- **User Management**: Separate registration and authentication for teachers and students
- **Quiz Creation**: Teachers can create quizzes with unique codes for student access
- **Question Management**: Support for multiple choice questions with JSON-stored options
- **Student Participation**: Students can join quizzes using unique codes
- **Scoring System**: Automatic scoring with statistics tracking
- **Role-based Dashboards**: Different interfaces for teachers and students

## Prerequisites

Before setting up the project, ensure you have the following installed:

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pgAdmin (optional, for database management)
- pip (Python package manager)

## Project Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Quiz
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv quiz_env

# Activate virtual environment
# On Windows:
quiz_env\Scripts\activate
# On macOS/Linux:
source quiz_env/bin/activate
```

### 3. Install Dependencies

```bash
pip install django psycopg2-binary
```

## Database Setup

### 1. Start PostgreSQL Service

Make sure PostgreSQL is running on your system:

**On Windows:**
- Start PostgreSQL service from Services panel or command line
- Or use pgAdmin to start the server

**On macOS:**
```bash
brew services start postgresql
```

**On Linux:**
```bash
sudo systemctl start postgresql
```

### 2. Create Database using pgAdmin

1. **Open pgAdmin**
   - Launch pgAdmin from your applications

2. **Connect to PostgreSQL Server**
   - Expand "Servers" in the left panel
   - Right-click on your PostgreSQL server and select "Connect Server"
   - Enter your PostgreSQL password

3. **Create New Database**
   - Right-click on "Databases"
   - Select "Create" > "Database..."
   - Enter database name: `quiz_system`
   - Click "Save"

### 3. Alternative: Create Database via Command Line

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE quiz_system;

# Exit PostgreSQL
\q
```

### 4. Update Database Configuration

The project is already configured to use the following database settings in `quiz_system/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'quiz_system',
        'USER': 'postgres',
        'PASSWORD': 'Sonu@2812',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**Important**: Update the `PASSWORD` field with your actual PostgreSQL password.

## Django Setup and Migration

### 1. Apply Database Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

### 2. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user for accessing Django admin panel.

### 3. Start Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Accessing the Application

1. **Home Page**: `http://127.0.0.1:8000/`
2. **Admin Panel**: `http://127.0.0.1:8000/admin/` (if superuser created)

### User Registration

**For Teachers:**
- Visit: `http://127.0.0.1:8000/accounts/register/teacher/`
- Fill in: Username, Password, Email, Department, Subject
- After registration, you'll be redirected to the teacher dashboard

**For Students:**
- Visit: `http://127.0.0.1:8000/accounts/register/student/`
- Fill in: Username, Password, Email, Roll Number, Class
- After registration, you'll be redirected to the student dashboard

### Teacher Workflow

1. **Login**: `http://127.0.0.1:8000/accounts/login/`
2. **Dashboard**: View and manage your quizzes
3. **Create Quiz**: Use the create quiz functionality to add new quizzes
4. **Add Questions**: Add questions to your quizzes with multiple choice options
5. **Share Quiz Code**: Provide the unique quiz code to students

### Student Workflow

1. **Login**: `http://127.0.0.1:8000/accounts/login/`
2. **Dashboard**: View enrolled quizzes
3. **Join Quiz**: Use quiz codes provided by teachers to join quizzes
4. **Take Quizzes**: Participate in available quizzes

## URL Structure

- `/` - Home page
- `/accounts/register/teacher/` - Teacher registration
- `/accounts/register/student/` - Student registration
- `/accounts/login/` - Login page
- `/accounts/teacher/dashboard/` - Teacher dashboard
- `/accounts/student/dashboard/` - Student dashboard
- `/quiz/quiz/create/` - Create new quiz
- `/quiz/quiz/<quiz_id>/add_question/` - Add questions to quiz
- `/quiz/quiz/join/` - Join quiz with code

## Troubleshooting

### Database Connection Issues

1. **Check PostgreSQL Service**: Ensure PostgreSQL is running
2. **Verify Database Exists**: Confirm `quiz_system` database was created
3. **Check Credentials**: Verify username/password in `settings.py`
4. **Port Issues**: Ensure PostgreSQL is running on port 5432

### Migration Issues

```bash
# Reset migrations if needed
python manage.py migrate --fake-initial

# Or reset specific app migrations
python manage.py migrate accounts zero
python manage.py migrate quiz zero
python manage.py migrate
```

### Common Commands

```bash
# Check migration status
python manage.py showmigrations

# Create new migrations after model changes
python manage.py makemigrations

# Run development server on specific port
python manage.py runserver 8080
```

## Project Structure

```
Quiz/
├── accounts/           # User authentication and management
│   ├── models.py      # CustomUser model
│   ├── views.py       # Registration and dashboard views
│   └── templates/     # Authentication templates
├── quiz/              # Quiz management
│   ├── models.py      # Quiz, Question, Result models
│   ├── views.py       # Quiz creation and participation views
│   └── templates/     # Quiz templates
├── quiz_system/       # Main project settings
│   ├── settings.py    # Database and app configuration
│   └── urls.py        # URL routing
└── manage.py          # Django management script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes.