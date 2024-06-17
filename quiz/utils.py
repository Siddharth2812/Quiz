# quiz/utils.py
from django.db import connection

def create_teacher_account(teacher_name, teacher_email, dept, subject):
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO quiz_teacher (teacher_name, teacher_email, dept, subject)
            VALUES (%s, %s, %s, %s)
        """, [teacher_name, teacher_email, dept, subject])

def add_student_to_quiz(student_id, quiz_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO quiz_studentquiz (student_id, quiz_id)
            VALUES (%s, %s)
        """, [student_id, quiz_id])
