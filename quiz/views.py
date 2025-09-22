import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
# Models are no longer needed since we use raw SQL

@login_required
def create_quiz(request):
    if request.method == 'POST':
        quiz_name = request.POST['quiz_name']
        subject = request.POST['subject']
        topic = request.POST['topic']
        
        with connection.cursor() as cursor:
            try:
                # Get teacher record using raw SQL
                cursor.execute(
                    "SELECT teacher_id FROM quiz_teacher WHERE teacher_email = %s",
                    [request.user.email]
                )
                teacher_result = cursor.fetchone()
                
                if not teacher_result:
                    messages.error(request, 'Teacher profile not found. Please contact admin.')
                    return redirect('teacher_dashboard')
                
                teacher_id = teacher_result[0]
                
                # Generate quiz code and create quiz using raw SQL (let database auto-generate quiz_id)
                quiz_code = str(uuid.uuid4())[:8].upper()
                
                cursor.execute(
                    """INSERT INTO quiz_quiz (quiz_name, quiz_code, subject, topic, teacher_id, top_score, score_avg) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    [quiz_name, quiz_code, subject, topic, teacher_id, 0, 0]
                )
                
                messages.success(request, f'Quiz "{quiz_name}" created successfully! Quiz code: {quiz_code}')
                return redirect('teacher_dashboard')
                
            except Exception as e:
                messages.error(request, f'Error creating quiz: {str(e)}')
                return redirect('teacher_dashboard')
    
    return render(request, 'quiz/create_quiz.html')

@login_required
def add_question(request, quiz_id):
    with connection.cursor() as cursor:
        # Verify quiz exists and get quiz details using raw SQL
        cursor.execute(
            "SELECT quiz_id, quiz_name, teacher_id FROM quiz_quiz WHERE quiz_id = %s",
            [quiz_id]
        )
        quiz_result = cursor.fetchone()
        
        if not quiz_result:
            messages.error(request, 'Quiz not found.')
            return redirect('teacher_dashboard')
        
        quiz_data = {
            'quiz_id': quiz_result[0],
            'quiz_name': quiz_result[1],
            'teacher_id': quiz_result[2]
        }
        
        # Check if the current user is the teacher who owns this quiz
        cursor.execute(
            "SELECT teacher_id FROM quiz_teacher WHERE teacher_email = %s",
            [request.user.email]
        )
        teacher_result = cursor.fetchone()
        
        if not teacher_result or teacher_result[0] != quiz_data['teacher_id']:
            messages.error(request, 'You can only add questions to your own quizzes.')
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
                # Insert question using raw SQL (let database auto-generate question_id)
                import json
                choices_json = json.dumps(choices) if choices else '{}'
                # correct_answers also needs to be JSON format for JSONB field
                correct_answers_json = json.dumps({"answer": correct_answers})
                
                cursor.execute(
                    """INSERT INTO quiz_quizquestion (question, question_type, choices, correct_answers, score, quiz_id) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    [question, question_type, choices_json, correct_answers_json, float(score), quiz_id]
                )
                
                messages.success(request, 'Question added successfully!')
                return redirect('teacher_dashboard')
            except Exception as e:
                messages.error(request, f'Error adding question: {str(e)}')
        
        return render(request, 'quiz/add_question.html', {'quiz_id': quiz_id, 'quiz': quiz_data})

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
    
    with connection.cursor() as cursor:
        try:
            # Find quiz by code using raw SQL
            cursor.execute(
                "SELECT quiz_id, quiz_name FROM quiz_quiz WHERE quiz_code = %s",
                [code]
            )
            quiz_result = cursor.fetchone()
            
            if not quiz_result:
                messages.error(request, 'Invalid quiz code. Please check the code and try again.')
                return render(request, 'quiz/join_quiz.html')
            
            quiz_id, quiz_name = quiz_result
            
            # Get student record using raw SQL
            cursor.execute(
                "SELECT student_id FROM quiz_student WHERE student_email = %s",
                [request.user.email]
            )
            student_result = cursor.fetchone()
            
            if not student_result:
                messages.error(request, 'Student profile not found. Please contact admin.')
                return redirect('student_dashboard')
            
            student_id = student_result[0]
            
            # Check if student is already enrolled using raw SQL
            cursor.execute(
                "SELECT COUNT(*) FROM quiz_studentquiz WHERE student_id = %s AND quiz_id = %s",
                [student_id, quiz_id]
            )
            enrollment_count = cursor.fetchone()[0]
            
            if enrollment_count > 0:
                messages.warning(request, f'You are already enrolled in "{quiz_name}".')
            else:
                # Enroll student using raw SQL
                cursor.execute(
                    "INSERT INTO quiz_studentquiz (student_id, quiz_id) VALUES (%s, %s)",
                    [student_id, quiz_id]
                )
                messages.success(request, f'Successfully joined "{quiz_name}"!')
                
            return redirect('student_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error joining quiz: {str(e)}')
            return render(request, 'quiz/join_quiz.html')

@login_required
def take_quiz(request, quiz_id):
    with connection.cursor() as cursor:
        try:
            # Get quiz details using raw SQL
            cursor.execute(
                "SELECT quiz_id, quiz_name, subject, topic FROM quiz_quiz WHERE quiz_id = %s",
                [quiz_id]
            )
            quiz_result = cursor.fetchone()
            
            if not quiz_result:
                messages.error(request, 'Quiz not found.')
                return redirect('student_dashboard')
            
            quiz_data = {
                'quiz_id': quiz_result[0],
                'quiz_name': quiz_result[1],
                'subject': quiz_result[2],
                'topic': quiz_result[3]
            }
            
            # Get student record using raw SQL
            cursor.execute(
                "SELECT student_id FROM quiz_student WHERE student_email = %s",
                [request.user.email]
            )
            student_result = cursor.fetchone()
            
            if not student_result:
                messages.error(request, 'Student profile not found.')
                return redirect('student_dashboard')
            
            student_id = student_result[0]
            
            # Verify student is enrolled using raw SQL
            cursor.execute(
                "SELECT COUNT(*) FROM quiz_studentquiz WHERE student_id = %s AND quiz_id = %s",
                [student_id, quiz_id]
            )
            enrollment_count = cursor.fetchone()[0]
            
            if enrollment_count == 0:
                messages.error(request, 'You are not enrolled in this quiz.')
                return redirect('student_dashboard')
            
            # Check if student has already completed this quiz using raw SQL
            cursor.execute(
                "SELECT score FROM quiz_result WHERE student_id = %s AND quiz_id = %s",
                [student_id, quiz_id]
            )
            existing_result = cursor.fetchone()
            
            if existing_result:
                messages.warning(request, f'You have already completed "{quiz_data["quiz_name"]}". Your score: {existing_result[0]}')
                return redirect('student_dashboard')
            
            # Get all questions for this quiz using raw SQL
            cursor.execute(
                "SELECT question_id, question, question_type, choices, correct_answers, score FROM quiz_quizquestion WHERE quiz_id = %s ORDER BY question_id",
                [quiz_id]
            )
            questions_data = cursor.fetchall()
            
            if not questions_data:
                messages.error(request, 'This quiz has no questions yet. Please contact your teacher.')
                return redirect('student_dashboard')
            
            # Format questions for template
            questions = []
            import json
            for q in questions_data:
                question = {
                    'question_id': q[0],
                    'question': q[1],
                    'question_type': q[2],
                    'choices': json.loads(q[3]) if q[3] else {},
                    'correct_answers': q[4],  # Keep as JSON for template (not needed in display)
                    'score': q[5]
                }
                questions.append(question)
            
            return render(request, 'quiz/take_quiz.html', {
                'quiz': quiz_data,
                'questions': questions,
            })
            
        except Exception as e:
            messages.error(request, f'Error loading quiz: {str(e)}')
            return redirect('student_dashboard')

@login_required
def submit_quiz(request, quiz_id):
    if request.method != 'POST':
        return redirect('student_dashboard')
    
    with connection.cursor() as cursor:
        try:
            # Get student record using raw SQL
            cursor.execute(
                "SELECT student_id FROM quiz_student WHERE student_email = %s",
                [request.user.email]
            )
            student_result = cursor.fetchone()
            
            if not student_result:
                messages.error(request, 'Student profile not found.')
                return redirect('student_dashboard')
            
            student_id = student_result[0]
            
            # Check if already submitted using raw SQL
            cursor.execute(
                "SELECT COUNT(*) FROM quiz_result WHERE student_id = %s AND quiz_id = %s",
                [student_id, quiz_id]
            )
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                messages.warning(request, 'You have already submitted this quiz.')
                return redirect('student_dashboard')
            
            # Get all questions and calculate score using raw SQL
            cursor.execute(
                "SELECT question_id, question_type, correct_answers, score FROM quiz_quizquestion WHERE quiz_id = %s",
                [quiz_id]
            )
            questions_data = cursor.fetchall()
            
            total_score = 0
            max_score = 0
            
            import json
            for question in questions_data:
                question_id, question_type, correct_answer_json, score = question
                max_score += score
                student_answer = request.POST.get(f'question_{question_id}', '').strip()
                
                # Parse correct answer from JSON
                try:
                    correct_answer_data = json.loads(correct_answer_json)
                    correct_answer = correct_answer_data.get('answer', '').strip()
                except:
                    correct_answer = str(correct_answer_json).strip()
                
                # Check if answer is correct (case-insensitive for text answers)
                if question_type == 'short_answer':
                    if student_answer.lower() == correct_answer.lower():
                        total_score += score
                else:
                    if student_answer == correct_answer:
                        total_score += score
            
            # Calculate percentage
            percentage = (total_score / max_score * 100) if max_score > 0 else 0
            
            # Get current quiz statistics using raw SQL
            cursor.execute(
                "SELECT score FROM quiz_result WHERE quiz_id = %s",
                [quiz_id]
            )
            existing_scores = [row[0] for row in cursor.fetchall()]
            
            # Calculate new statistics
            all_scores = existing_scores + [total_score]
            top_score = max(all_scores)
            score_avg = sum(all_scores) / len(all_scores)
            
            # Update quiz statistics using raw SQL
            cursor.execute(
                "UPDATE quiz_quiz SET top_score = %s, score_avg = %s WHERE quiz_id = %s",
                [top_score, score_avg, quiz_id]
            )
            
            # Save student result using raw SQL (let database auto-generate result_id)
            cursor.execute(
                "INSERT INTO quiz_result (score, top_score, score_avg, student_id, quiz_id) VALUES (%s, %s, %s, %s, %s)",
                [total_score, top_score, score_avg, student_id, quiz_id]
            )
            
            messages.success(request, f'Quiz submitted successfully! Your score: {total_score}/{max_score} ({percentage:.1f}%)')
            return redirect('student_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting quiz: {str(e)}')
            return redirect('student_dashboard')

@login_required
def student_quiz_result(request, quiz_id):
    """View for students to see their individual quiz result"""
    with connection.cursor() as cursor:
        try:
            # Get quiz details using raw SQL
            cursor.execute(
                "SELECT quiz_id, quiz_name, subject, topic FROM quiz_quiz WHERE quiz_id = %s",
                [quiz_id]
            )
            quiz_result = cursor.fetchone()
            
            if not quiz_result:
                messages.error(request, 'Quiz not found.')
                return redirect('student_dashboard')
            
            quiz_data = {
                'quiz_id': quiz_result[0],
                'quiz_name': quiz_result[1],
                'subject': quiz_result[2],
                'topic': quiz_result[3]
            }
            
            # Get student record using raw SQL
            cursor.execute(
                "SELECT student_id FROM quiz_student WHERE student_email = %s",
                [request.user.email]
            )
            student_result = cursor.fetchone()
            
            if not student_result:
                messages.error(request, 'Student profile not found.')
                return redirect('student_dashboard')
            
            student_id = student_result[0]
            
            # Check if student is enrolled using raw SQL
            cursor.execute(
                "SELECT COUNT(*) FROM quiz_studentquiz WHERE student_id = %s AND quiz_id = %s",
                [student_id, quiz_id]
            )
            enrollment_count = cursor.fetchone()[0]
            
            if enrollment_count == 0:
                messages.error(request, 'You are not enrolled in this quiz.')
                return redirect('student_dashboard')
            
            # Get the student's result using raw SQL
            cursor.execute(
                "SELECT result_id, score, top_score, score_avg FROM quiz_result WHERE student_id = %s AND quiz_id = %s",
                [student_id, quiz_id]
            )
            result_data = cursor.fetchone()
            
            if not result_data:
                messages.error(request, 'You have not completed this quiz yet.')
                return redirect('student_dashboard')
            
            result = {
                'result_id': result_data[0],
                'score': result_data[1],
                'top_score': result_data[2],
                'score_avg': result_data[3]
            }
            
            # Get all questions to show detailed results using raw SQL
            cursor.execute(
                "SELECT question_id, question, question_type, choices, correct_answers, score FROM quiz_quizquestion WHERE quiz_id = %s ORDER BY question_id",
                [quiz_id]
            )
            questions_data = cursor.fetchall()
            
            questions = []
            total_possible_score = 0
            import json
            
            for q in questions_data:
                # Parse correct answer from JSON for display
                try:
                    correct_answer_data = json.loads(q[4]) if q[4] else {}
                    correct_answer_display = correct_answer_data.get('answer', 'N/A')
                except:
                    correct_answer_display = str(q[4]) if q[4] else 'N/A'
                
                question = {
                    'question_id': q[0],
                    'question': q[1],
                    'question_type': q[2],
                    'choices': json.loads(q[3]) if q[3] else {},
                    'score': q[5],
                    'correct_answers': correct_answer_display  # Parsed for display
                }
                questions.append(question)
                total_possible_score += q[5]
            
            percentage = (result['score'] / total_possible_score * 100) if total_possible_score > 0 else 0
            
            return render(request, 'quiz/student_result.html', {
                'quiz': quiz_data,
                'result': result,
                'questions': questions,
                'total_possible_score': total_possible_score,
                'percentage': percentage,
            })
            
        except Exception as e:
            messages.error(request, f'Error loading results: {str(e)}')
            return redirect('student_dashboard')

@login_required
def view_quiz_results(request, quiz_id):
    """View for teachers to see all student results for their quiz"""
    with connection.cursor() as cursor:
        try:
            # Get quiz details and verify ownership using raw SQL
            cursor.execute(
                "SELECT q.quiz_id, q.quiz_name, q.subject, q.topic, q.teacher_id FROM quiz_quiz q WHERE q.quiz_id = %s",
                [quiz_id]
            )
            quiz_result = cursor.fetchone()
            
            if not quiz_result:
                messages.error(request, 'Quiz not found.')
                return redirect('teacher_dashboard')
            
            quiz_data = {
                'quiz_id': quiz_result[0],
                'quiz_name': quiz_result[1],
                'subject': quiz_result[2],
                'topic': quiz_result[3],
                'teacher_id': quiz_result[4]
            }
            
            # Get teacher record using raw SQL
            cursor.execute(
                "SELECT teacher_id FROM quiz_teacher WHERE teacher_email = %s",
                [request.user.email]
            )
            teacher_result = cursor.fetchone()
            
            if not teacher_result or teacher_result[0] != quiz_data['teacher_id']:
                messages.error(request, 'You can only view results for your own quizzes.')
                return redirect('teacher_dashboard')
            
            # Get quiz statistics using raw SQL
            cursor.execute(
                "SELECT SUM(score) FROM quiz_quizquestion WHERE quiz_id = %s",
                [quiz_id]
            )
            total_possible_score = cursor.fetchone()[0] or 0
            
            cursor.execute(
                "SELECT COUNT(*) FROM quiz_quizquestion WHERE quiz_id = %s",
                [quiz_id]
            )
            total_questions = cursor.fetchone()[0]
            
            # Get all results for this quiz using raw SQL with JOIN
            cursor.execute(
                """SELECT r.result_id, r.score, r.top_score, r.score_avg, 
                         s.student_name, s.student_email, s.roll_no 
                   FROM quiz_result r 
                   JOIN quiz_student s ON r.student_id = s.student_id 
                   WHERE r.quiz_id = %s 
                   ORDER BY r.score DESC""",
                [quiz_id]
            )
            results_data = cursor.fetchall()
            
            # Format results for template
            results = []
            scores = []
            
            for r in results_data:
                percentage = (r[1] / total_possible_score * 100) if total_possible_score > 0 else 0
                result = {
                    'result_id': r[0],
                    'score': r[1],
                    'top_score': r[2],
                    'score_avg': r[3],
                    'percentage': percentage,
                    'student': {
                        'student_name': r[4],
                        'student_email': r[5],
                        'roll_no': r[6]
                    }
                }
                results.append(result)
                scores.append(r[1])
            
            # Calculate statistics
            if scores:
                stats = {
                    'total_students': len(scores),
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
                'quiz': quiz_data,
                'results': results,
                'stats': stats,
                'total_questions': total_questions,
            })
            
        except Exception as e:
            messages.error(request, f'Error loading results: {str(e)}')
            return redirect('teacher_dashboard')

