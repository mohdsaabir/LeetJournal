from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        # Create user and log in
        user = User.objects.create_user(username=username, email=email, password=password1)
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')
        
         # Redirect after successful signup

    return render(request, 'signup.html')  # GET request or errors

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')  # Redirect after successful POST
        else:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')  # Message persists through next render

            # Still render login page if login failed (no redirect)
            # because user needs to retry form with message visible

    return render(request, 'login.html')  # GET or failed POST

def logout_view(request):
    logout(request)
    return redirect('login')
