
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout


def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("search_flights")

        else:
            messages.error(request, "Invalid username or password!")
            return redirect("login")

    return render(request, "accounts/login.html")

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect("search_flights")

def register(request):
    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("register")

        User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        messages.success(
            request,
            "Account created successfully!"
        )

        return redirect("search_flights")

    return render(request, "accounts/register.html")
