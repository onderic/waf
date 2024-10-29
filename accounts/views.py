from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from .forms import LoginForm, SignUpForm
from .models import User
from django.contrib.auth import logout
from maths.models import Subscription
from django.db import transaction



def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            user_type = form.cleaned_data['user_type']
            password = form.cleaned_data['password']
            
            with transaction.atomic():
                # Create the user
                user = User.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=user_type,
                    password=password
                )

                Subscription.objects.create(
                    user=user,
                    plan='', 
                    amount=None, 
                    is_active=False 
                )
            
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful.')
                
                # Redirect based on user type
                if user.user_type == 'ADMIN':
                    return redirect('admin_dashboard')
                elif user.user_type == 'student':
                    return redirect('problems')
                else:
                    messages.error(request, 'Unknown user type.')
                    return redirect('login')
            else:
                messages.error(request, 'Invalid credentials. Please try again.')
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/') 


