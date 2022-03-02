from django.shortcuts import render
from django.http import HttpResponse
from .models import WebScraper
from .main import update_db
# Create your views here.


def index(request):
    update_db()
    news = WebScraper.objects.all()
    return render(request, "scraper/home.html", {"news": news})
