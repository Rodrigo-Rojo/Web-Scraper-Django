from django.shortcuts import render
from .models import New
from .main import update_idaho_state_journal_db, update_east_idaho_news_db, update_yahoo_news_db, update_new_york_times_db, update_associated_press_db, update_cnn_db
# Create your views here.


def index(request):
    # update_idaho_state_journal_db()
    # update_yahoo_news_db()
    # update_east_idaho_news_db()
    # update_new_york_times_db()
    update_cnn_db()
    news = New.objects.all()
    return render(request, "scraper/home.html", {"news": news})
