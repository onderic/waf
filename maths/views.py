
from django.shortcuts import render, redirect,get_object_or_404

from maths.models import MathProblem, Mpesa, QuizScore,Subscription
from maths.mpesa import LipaNaMpesa
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
from django.views import View
from django.utils.decorators import method_decorator

# Create your views here.


def index(request):
    return render(request, 'index.html',)


def problems(request):
    problems = MathProblem.objects.all()
    return render(request, 'tasks.html',{'problems': problems})

@login_required
def math_problem_detail(request, slug):
    
    active_sub = Subscription.objects.filter(user=request.user, is_active=True).first()
    if not active_sub:
        return redirect("pricing")
    
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

@login_required
@csrf_exempt
def submit_score(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        score = data.get('score')
        total_questions = data.get('totalQuestions')
        math_problem_slug = data.get('slug')  
        
        try:
            math_problem = MathProblem.objects.get(slug=math_problem_slug)
        
            QuizScore.objects.create(
                student=request.user,
                score=score,
                total_questions=total_questions,
                math_problem=math_problem  
            )

            return JsonResponse({'status': 'success'}, status=201)

        except MathProblem.DoesNotExist:
            return JsonResponse({'error': 'Math problem not found'}, status=404)

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
        .subscription_by('day')
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
    
    return render(request, 'view_analytics.html')


@login_required
def student_scores(request):
    scores = QuizScore.objects.filter(student=request.user)

    # Get the current student's details
    student = request.user
    context = {
        'scores': scores,
        'student': student
    }
    return render(request, 'records.html', context)

def pricing(request):
    return render(request, 'pricing.html')


@method_decorator(login_required, name='dispatch') 
class PaymentView(View):
    def get(self, request, plan, amount):
        # Pass the plan and amount to the template context
        context = {
            'plan': plan,
            'amount': amount,
        }
        return render(request, 'payment.html', context)



@login_required
def payment_page(request):
    user = request.user
    subscription = get_object_or_404(Subscription, user=user) 
    
    if request.method == 'POST':
        data = json.loads(request.body) 
        phone_number = data.get('phone_number')
        amount = data.get('amount')  

        if not (len(phone_number) == 10 and (phone_number.startswith("07") or phone_number.startswith("01"))):
            return JsonResponse({'success': False, 'message': 'Invalid phone number. It must be 10 digits long and start with 07 or 01.'})

        # Format phone number to start with 254
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        
        lipa_na_mpesa = LipaNaMpesa()
    
        payload = {
            'amount': amount,
            'phone_number': phone_number,
            'subscription': str(subscription.id), 
        }
        response = lipa_na_mpesa.stk_push(payload)
        
        if response.get('ResponseCode') == '0': 
            checkout_request_id = response.get('CheckoutRequestID')
            Mpesa.objects.create(
                subscription=subscription,
                checkout_request_id=checkout_request_id,
                is_processed=False
            )
            
            request.session['subscription_id'] = str(subscription.id)
            request.session['checkout_request_id'] = checkout_request_id

            return JsonResponse({'success': True, 'checkout_request_id': checkout_request_id})
        else:
            return JsonResponse({'success': False, 'message': 'Payment initiation failed. Please try again.'})

    return render(request, 'payment.html', {'subscription': subscription})


@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print("callback", data)

        # Accessing nested data
        callback_data = data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = callback_data.get('CheckoutRequestID')
        result_code = callback_data.get('ResultCode')
        result_description = callback_data.get('ResultDesc')

        try:
            # Fetch the transaction using checkout_request_id
            transaction = Mpesa.objects.filter(checkout_request_id=checkout_request_id).first()
            transaction.result_code = result_code
            transaction.result_description = result_description
            transaction.is_processed = result_code == 0
            transaction.save()

         
            if transaction.is_processed:
                subscription = transaction.subscription
                subscription.activate_subscription()

            return JsonResponse({'status': 'success'})
        except Mpesa.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Transaction not found'})

    return JsonResponse({'status': 'failed', 'message': 'Invalid request'})


@csrf_exempt
def check_payment_status(request):
    checkout_request_id = request.GET.get('checkout_request_id')
    try:
        transaction = Mpesa.objects.filter(checkout_request_id=checkout_request_id).first()
        return JsonResponse({'is_processed': transaction.is_processed})
    except Mpesa.DoesNotExist:
        return JsonResponse({'is_processed': False, 'message': 'Transaction not found'})