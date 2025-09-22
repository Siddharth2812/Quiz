from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/add_question/', views.add_question, name='add_question'),
    path('join/', views.join_quiz, name='join_quiz'),
    path('<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('<int:quiz_id>/results/', views.view_quiz_results, name='view_quiz_results'),
    path('<int:quiz_id>/student-results/', views.student_quiz_result, name='student_quiz_result'),
]
