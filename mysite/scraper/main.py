from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
import requests
from .models import New
import re
from datetime import datetime


ISJ_URL = "https://www.idahostatejournal.com/"
EIN_URL = "https://www.eastidahonews.com/"
YAHOO_URL = "https://news.yahoo.com/"
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
}


def update_idaho_state_journal_db():
    res = requests.get(ISJ_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    urls = soup.find_all("h5", class_="tnt-headline")
    urls = [f"https://www.idahostatejournal.com{url.a.get('href')}" for url in urls]
    for url in urls:
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        try:
            new_img = soup.find("img", class_="full").get("src")[:166]
        except:
            new_img = "https://bloximages.chicago2.vip.townnews.com/idahostatejournal.com/content/tncms/custom/image/4c53f1e8-74be-11ec-9071-fbe2e18eb898.png"
        if new_img == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAQAAAAe/WZNAAAAEElEQVR42mM8U88ABowYDABAxQPltt5zqAAAAABJRU5ErkJggg==":
            new_img = "https://bloximages.chicago2.vip.townnews.com/idahostatejournal.com/content/tncms/custom/image/4c53f1e8-74be-11ec-9071-fbe2e18eb898.png"
        new_title = soup.find("h1", class_="headline")
        new_title_formatted = " ".join(new_title.get_text().split())
        data = soup.find("div", class_="subscriber-premium")
        body_formatted = re.sub('[^p\.m\.|^\s\.|a-z]*\.', '. ', data.get_text(), flags=re.M)
        body_formatted = re.sub('^\s*[a-zA-Z\d]*\.[a-z\s]*$', "", body_formatted, flags=re.M)
        body_formatted = " ".join(body_formatted.split())
        try:
            if New.objects.get(title=new_title_formatted):
                print(f"[DATABASE] - {new_title_formatted} in database")
        except ObjectDoesNotExist:
            news = New(title=new_title_formatted,
                       body=body_formatted,
                       img=new_img,
                       url=url,
                       site="IdahoStateJournal",
                       date=datetime.now()
                       )
            news.save()
            print(f"{new_title_formatted} has been saved successfully.")


def update_east_idaho_news_db():
    res = requests.get(EIN_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    main_new_url = soup.find("a", id="featuredStoryLink")
    news = soup.find_all("figure", class_="subfeaturedPic")
    urls = [url.a.get('href') for url in news]
    urls.insert(0, main_new_url.get("href"))

    for url in urls:
        try:
            res = requests.get(url, headers=header)
            site_html = res.text
            soup = BeautifulSoup(site_html, "html.parser")
            title = soup.find("h1").get_text()
            try:
                img = soup.find("figure", class_="featured-image").img.get("src")
            except AttributeError:
                img = "https://s3-assets.eastidahonews.com/wp-content/uploads/2017/09/25103716/EINLogo_1024x1024.jpg"
            body = soup.find("div", id="articleText").get_text()
            time = datetime.strptime(soup.find("time").get_text(), "%I:%M %p, %B %d, %Y")
            try:
                if New.objects.get(title=title):
                    print(f"[DATABASE] - {title} in database")
            except ObjectDoesNotExist:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time,
                           site="EastIdahoNews"
                           )
                news.save()
                print(f"{title} has been saved successfully.")
        except Exception as e:
            print(e)


def update_yahoo_news_db():
    res = requests.get(YAHOO_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    ul = soup.find("ul", attrs={"class": "Pstart(0)"})
    ul_urls = [url.a.get('href') for url in ul]
    main_new = soup.find("a", attrs={"class": "js-content-viewer"}).get("href")
    all_news = soup.find_all("a", attrs={"class": "js-content-viewer"})
    ul_urls.insert(0, main_new)
    urls = ul_urls + [url.get('href') for url in all_news]
    urls = list(dict.fromkeys([f"https://news.yahoo.com{url}" for url in urls if not url.startswith("https")]))

    for url in urls:
        try:
            res = requests.get(url, headers=header)
            site_html = res.text
            soup = BeautifulSoup(site_html, "html.parser")
            title = soup.find("h1").get_text()
            body = soup.find("div", attrs={"class": "caas-body"}).get_text()
            time_published = datetime.strptime(soup.find("time").get_text(), "%B %d, %Y, %I:%M %p")
            img = soup.find("div", attrs={"class": "caas-img-container"}).img.get("src")
            if img is None:
                img = "https://s.yimg.com/os/creatr-uploaded-images/2021-02/3b8ac110-7263-11eb-affd-ceae64845733"
            try:
                if New.objects.get(title=title):
                    print(f"[DATABASE] - {title} in database")
            except ObjectDoesNotExist:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time_published,
                           site="YahooNews"
                           )
                news.save()
                print(f"{title} has been saved successfully.")
        except AttributeError:
            img = "https://s.yimg.com/os/creatr-uploaded-images/2021-02/3b8ac110-7263-11eb-affd-ceae64845733"
