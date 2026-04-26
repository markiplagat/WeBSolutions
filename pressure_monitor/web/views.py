from django.shortcuts import render

# Home page view - simple landing page for the application.
# This is the default route and can be accessed by anyone. 

def home(request):
    return render(request, "web/home.html")
