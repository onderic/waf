from django.urls import path, include
from . import views
from .views import PaymentView

urlpatterns = [
    path('', views.index, name='home'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-math-problem/', views.manage_math_problem, name='add_math_problem'),
    path('analytics/', views.view_analytics, name='view_analytics'),
    path('edit/<int:pk>/', views.manage_math_problem, name='edit_math_problem'),
    path('delete/<int:pk>/', views.delete_math_problem, name='delete_math_problem'),
    path('math/problem/<int:pk>/', views.detail_view, name='math_problem_detail'),
    
    path('problem/<slug:slug>/', views.math_problem_detail, name='math_problem_detail'),
    path('submit-score/', views.submit_score, name='submit_score'),
    path('problems/', views.problems, name='problems'),
    path('records/', views.student_scores, name='records'),
    path('pricing/', views.pricing, name='pricing'),
    path('payment/<str:plan>/<int:amount>/', PaymentView.as_view(), name='payment_page'),
    path('daraja', views.payment_page, name='daraja'),
    path('mpesa_callback/', views.mpesa_callback, name='mpesa_callback'),
    path('check_payment_status/', views.check_payment_status, name='check_payment_status'),
]