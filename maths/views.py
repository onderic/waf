
from django.shortcuts import render, redirect,get_object_or_404

from maths.models import MathProblem, QuizScore
from .forms import MathProblemForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required

# Create your views here.


def index(request):
    return render(request, 'index.html',)

@login_required
def problems(request):
    problems = MathProblem.objects.all()
    return render(request, 'tasks.html',{'problems': problems})

def math_problem_detail(request, slug):
    problem = get_object_or_404(MathProblem, slug=slug)
    template_mapping = {
        'number-sense': 'number_sense.html',
        'basic-operations': 'basic_operations.html',
        'basic-fractions': 'basic_fractions.html',
        'measurements': 'measurements.html',
        'time': 'time.html',
    }

    template_name = template_mapping.get(slug, 'index.html')
    return render(request, template_name, {'problem': problem})

def detail_view(request):
    return render()

@csrf_exempt
def submit_score(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        score = data.get('score')
        total_questions = data.get('totalQuestions')
        
        # Save the score to the database
        QuizScore.objects.create(score=score, total_questions=total_questions)

        return JsonResponse({'status': 'success'}, status=201)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def admin_dashboard(request):
    total_users = User.objects.count()  
    active_users = User.objects.filter(is_active=True).count() 
    total_problems_solved = QuizScore.objects.count() 


    average_score = QuizScore.objects.aggregate(Avg('score'))['score__avg'] or 0

    today = timezone.now()
    start_of_week = today - timedelta(days=today.weekday())
    last_seven_days = start_of_week - timedelta(days=6) 

    user_activity = (
        QuizScore.objects
        .filter(submitted_at__gte=last_seven_days)
        .annotate(day=TruncDate('submitted_at')) 
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    chart_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    counts = [0] * 7 
    for entry in user_activity:
        day_of_week = entry['day'].weekday() 
        counts[day_of_week] = entry['count']

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_problems_solved': total_problems_solved,
        'average_score': round(average_score, 2), 
        'chart_labels': chart_labels,
        'chart_data': counts,
    }

    return render(request, 'Admin/dashboard.html', context)


def manage_math_problem(request, pk=None):
    # Fetch existing math problems
    problems = MathProblem.objects.all()
    
    if pk:
        # Edit existing math problem
        problem = get_object_or_404(MathProblem, pk=pk)
        if request.method == 'POST':
            form = MathProblemForm(request.POST, instance=problem)
            if form.is_valid():
                form.save()
                return redirect('add_math_problem') 
        else:
            form = MathProblemForm(instance=problem)
        return render(request, 'mathproblems/edit.html', {'form': form, 'problem': problem, 'problems': problems})

    # Add new math problem
    if request.method == 'POST':
        form = MathProblemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_math_problem') 
    else:
        form = MathProblemForm()
    
    return render(request, 'Admin/add.html', {'form': form, 'problems': problems})

# View to delete a math problem
def delete_math_problem(request, pk):
    problem = get_object_or_404(MathProblem, pk=pk)
    if request.method == 'POST':
        problem.delete()
        return redirect('add_math_problem')
    return render(request, 'mathproblems/delete_confirm.html', {'problem': problem})


def view_analytics(request):
    # Display analytics, like the number of problems added, topics covered, etc.
    return render(request, 'view_analytics.html')