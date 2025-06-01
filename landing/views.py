from django.shortcuts import render,redirect


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('/')  # Update this to your actual home/dashboard route name
    return render(request, 'landing.html')
