from django.utils import timezone
from django.db import models
from django.utils.text import slugify
import uuid
from accounts.models import User
from datetime import timedelta


class MathProblem(models.Model):
    topic = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)  

    def save(self, *args, **kwargs):
        if not self.slug: 
            self.slug = slugify(self.topic)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.topic

class QuizScore(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    math_problem = models.CharField(max_length=200)  
    submitted_at = models.DateTimeField(auto_now_add=True)



class Subscription(models.Model):
    PLAN_DURATIONS = {
        'monthly': timedelta(days=30),
        'quarterly': timedelta(days=90),
        'yearly': timedelta(days=365),
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=255, blank=True, null=True)  
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) 
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True) 
    is_active = models.BooleanField(default=False) 

    def activate_subscription(self):
        self.is_active = True
        self.start_date = timezone.now()
        plan_duration = self.PLAN_DURATIONS.get(self.plan.lower(), timedelta(days=30)) 
        self.end_date = self.start_date + plan_duration
        self.save()

    def __str__(self):
        return f"{self.user.email} - {self.plan} - {'Active' if self.is_active else 'Inactive'}"
    


class Mpesa(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    result_code = models.IntegerField(null=True, blank=True)
    result_description = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    is_processed = models.BooleanField(default=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"M-Pesa Transaction - {self.checkout_request_id}"
        