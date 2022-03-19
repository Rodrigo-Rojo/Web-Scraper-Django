from django.shortcuts import render
from .models import New
# Create your views here.


def index(request):
    news = New.objects.all()
    return render(request, "scraper/home.html", {"news": news})
