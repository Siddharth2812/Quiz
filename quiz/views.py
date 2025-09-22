import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Teacher, Student, Quiz, QuizQuestion, StudentQuiz, Result

@login_required
def create_quiz(request):
    if request.method == 'POST':
        quiz_name = request.POST['quiz_name']
        subject = request.POST['subject']
        topic = request.POST['topic']
        
        try:
            # Get teacher record based on current user
            teacher = Teacher.objects.get(teacher_email=request.user.email)
            
            # Create quiz with a shorter, readable code
            quiz_code = str(uuid.uuid4())[:8].upper()
            quiz = Quiz.objects.create(
                quiz_name=quiz_name,
                quiz_code=quiz_code,
                subject=subject,
                topic=topic,
                teacher=teacher
            )
            messages.success(request, f'Quiz "{quiz_name}" created successfully! Quiz code: {quiz_code}')
            return redirect('teacher_dashboard')
            
        except Teacher.DoesNotExist:
            messages.error(request, 'Teacher profile not found. Please contact admin.')
            return redirect('teacher_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating quiz: {str(e)}')
            return redirect('teacher_dashboard')
    
    return render(request, 'quiz/create_quiz.html')

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, quiz_id=quiz_id)
    
    # Check if the current user is the teacher who owns this quiz
    try:
        teacher = Teacher.objects.get(teacher_email=request.user.email)
        if quiz.teacher != teacher:
            messages.error(request, 'You can only add questions to your own quizzes.')
            return redirect('teacher_dashboard')
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        question = request.POST['question']
        question_type = request.POST['question_type']
        score = request.POST['score']
        
        # Handle different question types
        choices = {}
        correct_answers = ""
        
        if question_type == 'multiple_choice':
            # Build choices list from form data
            choices_list = []
            for choice_key in ['choice_a', 'choice_b', 'choice_c', 'choice_d']:
                choice_value = request.POST.get(choice_key, '').strip()
                if choice_value:
                    choices_list.append(choice_value)
            
            choices = {"options": choices_list}
            correct_answers = request.POST.get('correct_choice', '')
            
        elif question_type == 'true_false':
            choices = {"options": ["True", "False"]}
            correct_answers = request.POST.get('tf_answer', '')
            
        elif question_type == 'short_answer':
            choices = {}
            correct_answers = request.POST.get('correct_answer', '')
        
        try:
            QuizQuestion.objects.create(
                question=question,
                question_type=question_type,
                choices=choices,
                correct_answers=correct_answers,
                score=float(score),
                quiz=quiz
            )
            messages.success(request, 'Question added successfully!')
            return redirect('teacher_dashboard')
        except Exception as e:
            messages.error(request, f'Error adding question: {str(e)}')
    
    return render(request, 'quiz/add_question.html', {'quiz_id': quiz_id, 'quiz': quiz})

@login_required
def join_quiz(request):
    # Check if code is provided in URL parameters (for direct links)
    code_from_url = request.GET.get('code', '').upper().strip()
    
    if request.method == 'POST':
        code = request.POST['code'].upper().strip()
    elif code_from_url:
        # Auto-join if code is in URL
        code = code_from_url
    else:
        # Show the form
        return render(request, 'quiz/join_quiz.html')
    
    try:
        # Find quiz by code
        quiz = Quiz.objects.get(quiz_code=code)
        
        # Get student record based on current user
        student = Student.objects.get(student_email=request.user.email)
        
        # Check if student is already enrolled
        existing_enrollment = StudentQuiz.objects.filter(
            student=student, 
            quiz=quiz
        ).exists()
        
        if existing_enrollment:
            messages.warning(request, f'You are already enrolled in "{quiz.quiz_name}".')
        else:
            StudentQuiz.objects.create(student=student, quiz=quiz)
            messages.success(request, f'Successfully joined "{quiz.quiz_name}"!')
            
        return redirect('student_dashboard')
        
    except Quiz.DoesNotExist:
        messages.error(request, 'Invalid quiz code. Please check the code and try again.')
        return render(request, 'quiz/join_quiz.html')
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact admin.')
        return redirect('student_dashboard')
    except Exception as e:
        messages.error(request, f'Error joining quiz: {str(e)}')
        return render(request, 'quiz/join_quiz.html')

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, quiz_id=quiz_id)
    
    try:
        # Verify student is enrolled in this quiz
        student = Student.objects.get(student_email=request.user.email)
        enrollment = StudentQuiz.objects.get(student=student, quiz=quiz)
        
        # Check if student has already completed this quiz
        existing_result = Result.objects.filter(student=student, quiz=quiz).first()
        if existing_result:
            messages.warning(request, f'You have already completed "{quiz.quiz_name}". Your score: {existing_result.score}')
            return redirect('student_dashboard')
        
        # Get all questions for this quiz
        questions = QuizQuestion.objects.filter(quiz=quiz).order_by('question_id')
        
        if not questions.exists():
            messages.error(request, 'This quiz has no questions yet. Please contact your teacher.')
            return redirect('student_dashboard')
        
        return render(request, 'quiz/take_quiz.html', {
            'quiz': quiz,
            'questions': questions,
        })
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    except StudentQuiz.DoesNotExist:
        messages.error(request, 'You are not enrolled in this quiz.')
        return redirect('student_dashboard')

@login_required
def submit_quiz(request, quiz_id):
    if request.method != 'POST':
        return redirect('student_dashboard')
    
    quiz = get_object_or_404(Quiz, quiz_id=quiz_id)
    
    try:
        student = Student.objects.get(student_email=request.user.email)
        
        # Check if already submitted
        existing_result = Result.objects.filter(student=student, quiz=quiz).first()
        if existing_result:
            messages.warning(request, 'You have already submitted this quiz.')
            return redirect('student_dashboard')
        
        # Get all questions and calculate score
        questions = QuizQuestion.objects.filter(quiz=quiz)
        total_score = 0
        max_score = 0
        
        for question in questions:
            max_score += question.score
            student_answer = request.POST.get(f'question_{question.question_id}', '').strip()
            correct_answer = str(question.correct_answers).strip()
            
            # Check if answer is correct (case-insensitive for text answers)
            if question.question_type == 'short_answer':
                if student_answer.lower() == correct_answer.lower():
                    total_score += question.score
            else:
                if student_answer == correct_answer:
                    total_score += question.score
        
        # Calculate percentage and statistics
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Update quiz statistics
        quiz_results = Result.objects.filter(quiz=quiz)
        if quiz_results.exists():
            scores = [r.score for r in quiz_results] + [total_score]
            quiz.top_score = max(scores)
            quiz.score_avg = sum(scores) / len(scores)
        else:
            quiz.top_score = total_score
            quiz.score_avg = total_score
        quiz.save()
        
        # Save student result
        Result.objects.create(
            score=total_score,
            top_score=quiz.top_score,
            score_avg=quiz.score_avg,
            student=student,
            quiz=quiz
        )
        
        messages.success(request, f'Quiz submitted successfully! Your score: {total_score}/{max_score} ({percentage:.1f}%)')
        return redirect('student_dashboard')
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    except Exception as e:
        messages.error(request, f'Error submitting quiz: {str(e)}')
        return redirect('student_dashboard')

@login_required
def student_quiz_result(request, quiz_id):
    """View for students to see their individual quiz result"""
    quiz = get_object_or_404(Quiz, quiz_id=quiz_id)
    
    try:
        student = Student.objects.get(student_email=request.user.email)
        
        # Check if student is enrolled in this quiz
        enrollment = StudentQuiz.objects.get(student=student, quiz=quiz)
        
        # Get the student's result
        result = Result.objects.filter(student=student, quiz=quiz).first()
        
        if not result:
            messages.error(request, 'You have not completed this quiz yet.')
            return redirect('student_dashboard')
        
        # Get all questions to show detailed results
        questions = QuizQuestion.objects.filter(quiz=quiz).order_by('question_id')
        total_possible_score = sum(q.score for q in questions)
        percentage = (result.score / total_possible_score * 100) if total_possible_score > 0 else 0
        
        return render(request, 'quiz/student_result.html', {
            'quiz': quiz,
            'result': result,
            'questions': questions,
            'total_possible_score': total_possible_score,
            'percentage': percentage,
        })
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    except StudentQuiz.DoesNotExist:
        messages.error(request, 'You are not enrolled in this quiz.')
        return redirect('student_dashboard')

@login_required
def view_quiz_results(request, quiz_id):
    """View for teachers to see all student results for their quiz"""
    quiz = get_object_or_404(Quiz, quiz_id=quiz_id)
    
    try:
        teacher = Teacher.objects.get(teacher_email=request.user.email)
        
        # Check if this is the teacher's quiz
        if quiz.teacher != teacher:
            messages.error(request, 'You can only view results for your own quizzes.')
            return redirect('teacher_dashboard')
        
        # Get quiz statistics first
        questions = QuizQuestion.objects.filter(quiz=quiz)
        total_possible_score = sum(q.score for q in questions)
        
        # Get all results for this quiz
        results = Result.objects.filter(quiz=quiz).select_related('student').order_by('-score')
        
        # Calculate percentage for each result
        for result in results:
            result.percentage = (result.score / total_possible_score * 100) if total_possible_score > 0 else 0
        
        # Calculate additional statistics
        if results.exists():
            scores = [r.score for r in results]
            stats = {
                'total_students': results.count(),
                'highest_score': max(scores),
                'lowest_score': min(scores),
                'average_score': sum(scores) / len(scores),
                'total_possible': total_possible_score,
                'average_percentage': (sum(scores) / len(scores) / total_possible_score * 100) if total_possible_score > 0 else 0,
            }
        else:
            stats = {
                'total_students': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'average_score': 0,
                'total_possible': total_possible_score,
                'average_percentage': 0,
            }
        
        return render(request, 'quiz/teacher_results.html', {
            'quiz': quiz,
            'results': results,
            'stats': stats,
            'total_questions': questions.count(),
        })
        
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_dashboard')

