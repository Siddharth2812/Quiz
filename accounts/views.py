import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from quiz.models import Quiz, StudentQuiz, Teacher, Student

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

            # Assuming Teacher model exists
            Teacher.objects.create(
                teacher_name=teacher_name,
                teacher_email=teacher_email,
                dept=dept,
                subject=subject
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

            # Assuming Student model exists
            Student.objects.create(
                student_name=student_name,
                student_email=student_email,
                roll_no=roll_no,
                student_class=student_class
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
                if hasattr(user, 'teacher'):
                    return redirect('teacher_dashboard')
                elif hasattr(user, 'student'):
                    return redirect('student_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def teacher_dashboard(request):
    teacher = Teacher.objects.get(teacher_email=request.user.email)
    quizzes = Quiz.objects.filter(teacher=teacher)
    return render(request, 'accounts/teacher_dashboard.html', {'quizzes': quizzes})

@login_required
def student_dashboard(request):
    try:
        student = Student.objects.get(student_email=request.user.email)
        student_quizzes = StudentQuiz.objects.filter(student=student)
        quizzes = [sq.quiz for sq in student_quizzes]
        return render(request, 'accounts/student_dashboard.html', {'quizzes': quizzes})
    except Student.DoesNotExist:
        return redirect('login')
