from django.urls import path
from .views import register_teacher, register_student, login_view, teacher_dashboard, student_dashboard

urlpatterns = [
    path('register/teacher/', register_teacher, name='register_teacher'),
    path('register/student/', register_student, name='register_student'),
    path('login/', login_view, name='login'),
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
]
