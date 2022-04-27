from django.shortcuts import render
from .models import New
from django.core.paginator import Paginator

# Create your views here.


def index(request):
    news = New.objects.all().order_by("-date")
    ap = [new for new in news.order_by("-date") if new.site == "AssociatedPress"][:10]
    wp = [new for new in news.order_by("-date") if new.site == "WashingtonPost"][:10]
    sky = [new for new in news.order_by("-date") if new.site == "SkyNews"][:10]
    cnn = [new for new in news.order_by("-date") if new.site == "CNN"][:10]
    nyt = [new for new in news.order_by("-date") if new.site == "NewYorkTimes"][:10]
    yh = [new for new in news.order_by("-date") if new.site == "YahooNews"][:10]
    ein = [new for new in news.order_by("-date") if new.site == "EastIdahoNews"][:10]
    isj = [new for new in news.order_by("-date") if new.site == "IdahoStateJournal"][:10]
    # for new in New.objects.values_list('title', flat=True).distinct():
    #     New.objects.filter(pk__in=New.objects.filter(title=new).values_list('id', flat=True)[1:]).delete()

    # ap_paginator = Paginator([new for new in news if new.site == "AssociatedPress"][:10], 10)
    # page_number = request.GET.get('page')
    # ap = ap_paginator.get_page(page_number)
    #
    # wp_paginator = Paginator([new for new in news if new.site == "WashingtonPost"], 10)
    # wp = wp_paginator.get_page(page_number)
    #
    # sky_paginator = Paginator([new for new in news if new.site == "SkyNews"], 10)
    # sky = sky_paginator.get_page(page_number)
    #
    # cnn_paginator = Paginator([new for new in news if new.site == "CNN"], 10)
    # cnn = cnn_paginator.get_page(page_number)
    #
    # nyt_paginator = Paginator([new for new in news if new.site == "NewYorkTimes"], 10)
    # nyt = nyt_paginator.get_page(page_number)
    #
    # yh_paginator = Paginator([new for new in news if new.site == "YahooNews"], 10)
    # yh = yh_paginator.get_page(page_number)
    #
    # ein_paginator = Paginator([new for new in news if new.site == "EastIdahoNews"], 10)
    # ein = ein_paginator.get_page(page_number)
    #
    # isj_paginator = Paginator([new for new in news if new.site == "IdahoStateJournal"], 10)
    # isj = isj_paginator.get_page(page_number)

    return render(request, "scraper/home.html", {"ap": ap,
                                                 "wp": wp,
                                                 "sky": sky,
                                                 "cnn": cnn,
                                                 "nyt": nyt,
                                                 "yh": yh,
                                                 "ein": ein,
                                                 "isj": isj
                                                 })
