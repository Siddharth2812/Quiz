from django.urls import path
from . import views

urlpatterns = [
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('quiz/create/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/add_question/', views.add_question, name='add_question'),
    path('quiz/join/', views.join_quiz, name='join_quiz'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]
