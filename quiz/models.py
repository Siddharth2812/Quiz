import uuid
from django.db import models

class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    student_name = models.CharField(max_length=255)
    student_email = models.EmailField(unique=True)
    roll_no = models.CharField(max_length=50)
    student_class = models.CharField(max_length=50)  # Renamed from 'class' to avoid conflict with Python keyword

class Teacher(models.Model):
    teacher_id = models.AutoField(primary_key=True)
    teacher_name = models.CharField(max_length=255)
    teacher_email = models.EmailField(unique=True)
    dept = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)

class Quiz(models.Model):
    quiz_id = models.AutoField(primary_key=True)
    quiz_name = models.CharField(max_length=255)
    quiz_code = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    top_score = models.FloatField(default=0)
    score_avg = models.FloatField(default=0)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

class QuizQuestion(models.Model):
    question_id = models.AutoField(primary_key=True)
    question = models.TextField()
    question_type = models.CharField(max_length=50)
    choices = models.JSONField()  # Assumes choices are stored as JSON
    correct_answers = models.JSONField()  # Assumes correct answers are stored as JSON
    score = models.FloatField(default=0)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

class Result(models.Model):
    result_id = models.AutoField(primary_key=True)
    score = models.FloatField()
    top_score = models.FloatField()
    score_avg = models.FloatField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

class StudentQuiz(models.Model):
    student_quiz_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
