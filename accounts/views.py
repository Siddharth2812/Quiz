import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import connection
from .forms import CustomUserCreationForm
# Models are no longer needed since we use raw SQL

def register_teacher(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            
            teacher_name = form.cleaned_data['username']
            teacher_email = form.cleaned_data['email']
            dept = request.POST.get('dept')
            subject = request.POST.get('subject')

            # Create teacher record using raw SQL
            with connection.cursor() as cursor:
                teacher_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO quiz_teacher (teacher_id, teacher_name, teacher_email, dept, subject) VALUES (%s, %s, %s, %s, %s)",
                    [teacher_id, teacher_name, teacher_email, dept, subject]
                )
            
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            return redirect('teacher_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register_teacher.html', {'form': form})

def register_student(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.save()
            
            student_name = form.cleaned_data['username']
            student_email = form.cleaned_data['email']
            roll_no = request.POST.get('roll_no')
            student_class = request.POST.get('student_class')

            # Create student record using raw SQL
            with connection.cursor() as cursor:
                student_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO quiz_student (student_id, student_name, student_email, roll_no, student_class) VALUES (%s, %s, %s, %s, %s)",
                    [student_id, student_name, student_email, roll_no, student_class]
                )
            
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            return redirect('student_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register_student.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check user type using raw SQL
                with connection.cursor() as cursor:
                    # Check if user is a teacher
                    cursor.execute(
                        "SELECT COUNT(*) FROM quiz_teacher WHERE teacher_email = %s",
                        [user.email]
                    )
                    is_teacher = cursor.fetchone()[0] > 0
                    
                    if is_teacher:
                        return redirect('teacher_dashboard')
                    else:
                        return redirect('student_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def teacher_dashboard(request):
    with connection.cursor() as cursor:
        # Get teacher record using raw SQL
        cursor.execute(
            "SELECT teacher_id, teacher_name FROM quiz_teacher WHERE teacher_email = %s",
            [request.user.email]
        )
        teacher_result = cursor.fetchone()
        
        if not teacher_result:
            return redirect('login')
        
        teacher_id = teacher_result[0]
        
        # Get teacher's quizzes using raw SQL
        cursor.execute(
            "SELECT quiz_id, quiz_name, quiz_code, subject, topic FROM quiz_quiz WHERE teacher_id = %s ORDER BY quiz_name",
            [teacher_id]
        )
        quiz_results = cursor.fetchall()
        
        # Format quizzes for template
        quizzes = []
        for q in quiz_results:
            quiz = {
                'quiz_id': q[0],
                'quiz_name': q[1],
                'quiz_code': q[2],
                'subject': q[3],
                'topic': q[4]
            }
            quizzes.append(quiz)
        
        return render(request, 'accounts/teacher_dashboard.html', {'quizzes': quizzes})

@login_required
def student_dashboard(request):
    with connection.cursor() as cursor:
        # Get student record using raw SQL
        cursor.execute(
            "SELECT student_id, student_name FROM quiz_student WHERE student_email = %s",
            [request.user.email]
        )
        student_result = cursor.fetchone()
        
        if not student_result:
            return redirect('login')
        
        student_id = student_result[0]
        
        # Get student's enrolled quizzes using raw SQL with JOIN
        cursor.execute(
            """SELECT q.quiz_id, q.quiz_name, q.quiz_code, q.subject, q.topic,
                      CASE WHEN r.result_id IS NOT NULL THEN 1 ELSE 0 END as completed
               FROM quiz_quiz q 
               JOIN quiz_studentquiz sq ON q.quiz_id = sq.quiz_id 
               LEFT JOIN quiz_result r ON q.quiz_id = r.quiz_id AND r.student_id = %s
               WHERE sq.student_id = %s 
               ORDER BY q.quiz_name""",
            [student_id, student_id]
        )
        quiz_results = cursor.fetchall()
        
        # Format quizzes for template
        quizzes = []
        for q in quiz_results:
            quiz = {
                'quiz_id': q[0],
                'quiz_name': q[1],
                'quiz_code': q[2],
                'subject': q[3],
                'topic': q[4],
                'completed': bool(q[5])
            }
            quizzes.append(quiz)
        
        return render(request, 'accounts/student_dashboard.html', {'quizzes': quizzes})
