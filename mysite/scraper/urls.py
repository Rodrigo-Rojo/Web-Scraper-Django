from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('<str:site>', views.news_site, name='news_site')
]
