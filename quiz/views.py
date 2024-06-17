import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

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

@login_required
def teacher_dashboard(request):
    user_id = request.user.id
    teacher = execute_query(
        "SELECT * FROM teacher WHERE teacher_id = (SELECT id FROM auth_user WHERE id = %s)",
        [user_id]
    )
    if teacher:
        quizzes = execute_query(
            "SELECT * FROM quiz WHERE teacher_id = %s",
            [teacher[0]['teacher_id']]
        )
        return render(request, 'teacher_dashboard.html', {'quizzes': quizzes})
    return redirect('login')

@login_required
def create_quiz(request):
    if request.method == 'POST':
        quiz_name = request.POST['quiz_name']
        subject = request.POST['subject']
        topic = request.POST['topic']
        teacher_id = request.user.id
        quiz_code = uuid.uuid4()
        execute_query(
            "INSERT INTO quiz (quiz_name, quiz_code, subject, topic, teacher_id) VALUES (%s, %s, %s, %s, %s)",
            [quiz_name, quiz_code, subject, topic, teacher_id]
        )
        return redirect('teacher_dashboard')
    return render(request, 'create_quiz.html')

@login_required
def add_question(request, quiz_id):
    if request.method == 'POST':
        question = request.POST['question']
        question_type = request.POST['question_type']
        choices = request.POST['choices']  # Assuming choices are in JSON format
        correct_answers = request.POST['correct_answers']  # Assuming correct_answers are in JSON format
        score = request.POST['score']
        execute_query(
            "INSERT INTO quiz_question (question, question_type, choices, correct_answers, score, quiz_id) VALUES (%s, %s, %s, %s, %s, %s)",
            [question, question_type, choices, correct_answers, score, quiz_id]
        )
        return redirect('teacher_dashboard')
    return render(request, 'add_question.html', {'quiz_id': quiz_id})

@login_required
def join_quiz(request):
    if request.method == 'POST':
        code = request.POST['code']
        quiz = execute_query(
            "SELECT * FROM quiz WHERE quiz_code = %s",
            [code]
        )
        if quiz:
            execute_query(
                "INSERT INTO student_quiz (student_id, quiz_id) VALUES (%s, %s)",
                [request.user.id, quiz[0]['quiz_id']]
            )
            return redirect('student_dashboard')
    return render(request, 'join_quiz.html')

@login_required
def student_dashboard(request):
    user_id = request.user.id
    student = execute_query(
        "SELECT * FROM student WHERE student_id = (SELECT id FROM auth_user WHERE id = %s)",
        [user_id]
    )
    if student:
        quizzes = execute_query(
            "SELECT quiz.* FROM quiz JOIN student_quiz ON quiz.quiz_id = student_quiz.quiz_id WHERE student_quiz.student_id = %s",
            [student[0]['student_id']]
        )
        return render(request, 'student_dashboard.html', {'quizzes': quizzes})
    return redirect('login')
