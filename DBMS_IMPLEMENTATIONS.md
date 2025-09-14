# DBMS Implementations - Database CRUD Operations

This document outlines all database operations implemented in the Django Quiz System, showing where and how CRUD (Create, Read, Update, Delete) operations are performed across different files.

## Database Approach Overview

The project uses **two different approaches** for database operations:
1. **Django ORM** - Object-Relational Mapping (in `accounts/views.py`)
2. **Raw SQL Queries** - Direct SQL execution (in `quiz/views.py` and `quiz/utils.py`)

---

## 1. Django ORM Operations

### File: `accounts/views.py`

#### CREATE Operations

**Function: `register_teacher()` (Line 9-35)**
```python
# Create CustomUser
user = form.save(commit=False)
user.is_staff = True
user.save()  # Line 15

# Create Teacher record
Teacher.objects.create(  # Line 23
    teacher_name=teacher_name,
    teacher_email=teacher_email,
    dept=dept,
    subject=subject
)
```

**Function: `register_student()` (Line 37-63)**
```python
# Create CustomUser
user = form.save(commit=False)
user.is_staff = False
user.save()  # Line 43

# Create Student record
Student.objects.create(  # Line 51
    student_name=student_name,
    student_email=student_email,
    roll_no=roll_no,
    student_class=student_class
)
```

#### READ Operations

**Function: `teacher_dashboard()` (Line 82-86)**
```python
# Get teacher by email
teacher = Teacher.objects.get(teacher_email=request.user.email)  # Line 84

# Get all quizzes for this teacher
quizzes = Quiz.objects.filter(teacher=teacher)  # Line 85
```

**Function: `student_dashboard()` (Line 88-96)**
```python
# Get student by email
student = Student.objects.get(student_email=request.user.email)  # Line 91

# Get all quiz enrollments for this student
student_quizzes = StudentQuiz.objects.filter(student=student)  # Line 92
```

---

## 2. Raw SQL Operations

### File: `quiz/views.py`

#### SQL Execution Helper Function
**Function: `execute_query()` (Line 8-17)**
```python
def execute_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        return None
```

#### READ Operations

**Function: `teacher_dashboard()` (Line 19-32)**
```sql
-- Get teacher information
SELECT * FROM teacher 
WHERE teacher_id = (SELECT id FROM auth_user WHERE id = %s)
```
```sql
-- Get all quizzes for teacher
SELECT * FROM quiz WHERE teacher_id = %s
```

**Function: `student_dashboard()` (Line 81-93)**
```sql
-- Get student information
SELECT * FROM student 
WHERE student_id = (SELECT id FROM auth_user WHERE id = %s)
```
```sql
-- Get quizzes joined by student
SELECT quiz.* FROM quiz 
JOIN student_quiz ON quiz.quiz_id = student_quiz.quiz_id 
WHERE student_quiz.student_id = %s
```

**Function: `join_quiz()` (Line 65-78)**
```sql
-- Find quiz by code
SELECT * FROM quiz WHERE quiz_code = %s
```

#### CREATE Operations

**Function: `create_quiz()` (Line 35-47)**
```sql
-- Insert new quiz
INSERT INTO quiz (quiz_name, quiz_code, subject, topic, teacher_id) 
VALUES (%s, %s, %s, %s, %s)
```

**Function: `add_question()` (Line 49-62)**
```sql
-- Insert new question
INSERT INTO quiz_question (question, question_type, choices, correct_answers, score, quiz_id) 
VALUES (%s, %s, %s, %s, %s, %s)
```

**Function: `join_quiz()` (Line 73-75)**
```sql
-- Enroll student in quiz
INSERT INTO student_quiz (student_id, quiz_id) 
VALUES (%s, %s)
```

### File: `quiz/utils.py`

#### CREATE Operations

**Function: `create_teacher_account()` (Line 4-9)**
```sql
-- Insert teacher record
INSERT INTO quiz_teacher (teacher_name, teacher_email, dept, subject)
VALUES (%s, %s, %s, %s)
```

**Function: `add_student_to_quiz()` (Line 11-16)**
```sql
-- Enroll student in quiz
INSERT INTO quiz_studentquiz (student_id, quiz_id)
VALUES (%s, %s)
```

---

## 3. Database Models (Schema Definitions)

### File: `accounts/models.py`

**CustomUser Model (Line 5-7)**
```python
class CustomUser(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
```

### File: `quiz/models.py`

**All Model Definitions (Line 4-49)**
- `Student` - Student information storage
- `Teacher` - Teacher information storage  
- `Quiz` - Quiz metadata with UUID codes
- `QuizQuestion` - Questions with JSON choices/answers
- `Result` - Quiz results and scoring
- `StudentQuiz` - Many-to-many relationship

---

## 4. CRUD Operations Summary by Entity

### User Management
| Operation | Method | File | Function | Line |
|-----------|---------|------|----------|------|
| CREATE | ORM | accounts/views.py | register_teacher() | 15, 23 |
| CREATE | ORM | accounts/views.py | register_student() | 43, 51 |
| READ | ORM | accounts/views.py | teacher_dashboard() | 84 |
| READ | ORM | accounts/views.py | student_dashboard() | 91 |

### Quiz Management
| Operation | Method | File | Function | Line |
|-----------|---------|------|----------|------|
| CREATE | SQL | quiz/views.py | create_quiz() | 42-44 |
| READ | SQL | quiz/views.py | teacher_dashboard() | 27-29 |
| READ | SQL | quiz/views.py | join_quiz() | 68-70 |

### Question Management
| Operation | Method | File | Function | Line |
|-----------|---------|------|----------|------|
| CREATE | SQL | quiz/views.py | add_question() | 57-60 |

### Student-Quiz Relationships
| Operation | Method | File | Function | Line |
|-----------|---------|------|----------|------|
| CREATE | SQL | quiz/views.py | join_quiz() | 73-75 |
| CREATE | SQL | quiz/utils.py | add_student_to_quiz() | 13-15 |
| READ | ORM | accounts/views.py | student_dashboard() | 92 |
| READ | SQL | quiz/views.py | student_dashboard() | 88-90 |

---

## 5. Key Database Design Patterns

### 1. Mixed ORM and SQL Approach
- **ORM Usage**: User authentication and simple CRUD operations
- **Raw SQL**: Complex joins and custom queries for better performance

### 2. Foreign Key Relationships
- `Quiz.teacher` → `Teacher` (One-to-Many)
- `QuizQuestion.quiz` → `Quiz` (One-to-Many)
- `Result.student` → `Student` (One-to-Many)
- `Result.quiz` → `Quiz` (One-to-Many)
- `StudentQuiz` → Many-to-Many between `Student` and `Quiz`

### 3. JSON Field Usage
- `QuizQuestion.choices` - Stores multiple choice options as JSON
- `QuizQuestion.correct_answers` - Stores correct answers as JSON

### 4. UUID Implementation
- `Quiz.quiz_code` - Uses UUID for unique quiz access codes

---

## 6. Database Security Considerations

### Parameterized Queries
All SQL queries use parameter binding to prevent SQL injection:
```python
cursor.execute(query, [param1, param2, param3])
```

### Django ORM Benefits
- Automatic SQL injection protection
- Built-in validation
- Transaction management

---

## 7. Performance Considerations

### Efficient Queries
- Direct SQL for complex joins (student dashboard quiz retrieval)
- Single queries instead of multiple database hits
- Proper use of foreign key relationships

### Areas for Optimization
1. Add database indexes for frequently queried fields
2. Consider caching for quiz data
3. Optimize JSON field queries for large question sets

---

## 8. Missing CRUD Operations

The following operations are not yet implemented but would be valuable additions:

### UPDATE Operations Needed
- Update quiz details
- Modify questions
- Edit user profiles

### DELETE Operations Needed  
- Delete quizzes
- Remove questions
- Unenroll students from quizzes

### Advanced READ Operations
- Quiz result analytics
- Student performance tracking
- Teacher statistics

---

This document provides a comprehensive overview of all database operations in the Django Quiz System, helping developers understand where and how data persistence is handled throughout the application.