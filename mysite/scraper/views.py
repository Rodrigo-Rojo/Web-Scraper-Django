from django.shortcuts import render
from .models import New
from django.core.paginator import Paginator

# Create your views here.


def index(request):
    news = New.objects.all().order_by("-date")
    for new in New.objects.values_list('title', flat=True).distinct():
        New.objects.filter(pk__in=New.objects.filter(title=new).values_list('id', flat=True)[1:]).delete()
    ap = [new for new in news.order_by("-date") if new.site == "Associated Press"][:10]
    wp = [new for new in news.order_by("-date") if new.site == "Washington Post"][:10]
    sky = [new for new in news.order_by("-date") if new.site == "Sky News"][:10]
    cnn = [new for new in news.order_by("-date") if new.site == "CNN"][:10]
    nyt = [new for new in news.order_by("-date") if new.site == "New York Times"][:10]
    yh = [new for new in news.order_by("-date") if new.site == "Yahoo News"][:10]
    ein = [new for new in news.order_by("-date") if new.site == "East Idaho News"][:10]
    isj = [new for new in news.order_by("-date") if new.site == "Idaho State Journal"][:10]
    return render(request, "scraper/home.html", {"ap": ap,
                                                 "wp": wp,
                                                 "sky": sky,
                                                 "cnn": cnn,
                                                 "nyt": nyt,
                                                 "yh": yh,
                                                 "ein": ein,
                                                 "isj": isj
                                                 })


def news_site(request, site):
    news = New.objects.all().order_by("-date")
    news_name = site
    site = [new for new in news.order_by("-date") if new.site == site]
    ap_paginator = Paginator(site, 25)
    page_number = request.GET.get('page')
    site = ap_paginator.get_page(page_number)
    return render(request, "scraper/news_site.html", {"site": site, "news_name": news_name})
