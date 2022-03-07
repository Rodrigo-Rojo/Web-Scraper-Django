from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import requests
from .models import New
import re
from time import sleep
from datetime import datetime
from requests_html import HTMLSession

ISJ_URL = "https://www.idahostatejournal.com/"
EIN_URL = "https://www.eastidahonews.com/"
YAHOO_URL = "https://news.yahoo.com/"
NYT_URL = "https://www.nytimes.com/"
AP_URL = "https://apnews.com/"
CNN_URL = "https://www.cnn.com"
header = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Accept-Language": "en-US,en;q=0.5"
}
year = datetime.now().year


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
                       date=timezone.now()
                       )
            news.save()
            print(f"{new_title_formatted} has been saved successfully.")


def update_east_idaho_news_db():
    res = requests.get(EIN_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a if url.get("href") is not None and str(year) in url.get("href")]
    urls = list(dict.fromkeys(urls))
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
            time = timezone.datetime.strptime(soup.find("time").get_text(), "%I:%M %p, %B %d, %Y")
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
    a = soup.find_all("a")
    urls = [url.get("href") for url in a if
            url.get("href").endswith(".html") and not url.get("href").startswith("https://legal")]
    urls = [f"https://news.yahoo.com{url}" for url in urls if not url.startswith("https")]
    for url in urls:
        try:
            res = requests.get(url, headers=header)
            site_html = res.text
            soup = BeautifulSoup(site_html, "html.parser")
            title = soup.find("h1").get_text()
            body = soup.find("div", attrs={"class": "caas-body"}).get_text()
            time = timezone.datetime.strptime(soup.find("time").get_text(), "%B %d, %Y, %I:%M %p")
            try:
                img = soup.find("div", attrs={"class": "caas-img-container"}).img.get("src")
            except AttributeError:
                img = "https://s.yimg.com/os/creatr-uploaded-images/2021-02/3b8ac110-7263-11eb-affd-ceae64845733"
            try:
                if New.objects.get(title=title):
                    print(f"[DATABASE] - {title} in database")
            except ObjectDoesNotExist:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time,
                           site="YahooNews"
                           )
                news.save()
                print(f"{title} has been saved successfully.")
        except Exception as e:
            print(e)
            break


def update_new_york_times_db():
    res = requests.get(NYT_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a if str(year) in url.get("href") and "live" not in url.get("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        try:
            title = soup.find("h1").get_text()
        except AttributeError:
            continue
        body = soup.find_all("p")
        body = " ".join([i.get_text() for i in body])
        try:
            time = datetime.strptime(soup.find("time").get("datetime")[:-5], "%Y-%m-%dT%H:%M:%S")
        except TypeError:
            time = datetime.now()
        except ValueError:
            time = datetime.now()
        try:
            img = soup.find_all("img")[1].get("src")
        except IndexError:
            img = "https://m.media-amazon.com/images/I/31B-jyc2D5L._SY445_SX342_.jpg"
        except AttributeError:
            img = "https://m.media-amazon.com/images/I/31B-jyc2D5L._SY445_SX342_.jpg"
        try:
            if New.objects.get(title=title):
                print(f"[DATABASE] - {title} in database")
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="NewYorkTimes"
                       )
            news.save()
            print(f"{title} has been saved successfully.")
        sleep(1)


def update_associated_press_db():
    res = requests.get(AP_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a if url.get("href").startswith("/article/")]
    urls = list(dict.fromkeys(urls))
    urls = [f"https://apnews.com{url}" for url in urls if not url.startswith("https")]
    for url in urls:
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        title = soup.find("h1").get_text()
        try:
            body = soup.find("div", attrs={"class": "Article"}).get_text()
        except AttributeError:
            continue
        time = timezone.datetime.strptime(soup.find("span", attrs={"class": "Timestamp"}).get("data-source")[:-1], "%Y-%m-%dT%H:%M:%S")
        img = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Associated_Press_logo_2012.svg/1200px-Associated_Press_logo_2012.svg.png"
        try:
            if New.objects.get(title=title):
                print(f"[DATABASE] - {title} in database")
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="AssociatedPress"
                       )
            news.save()
            print(f"{title} has been saved successfully.")


def update_cnn_db():
    session = HTMLSession()
    res = session.get(CNN_URL)
    res = [a for a in res if "2022" in a]
    print(res)
    return
    res = requests.get(CNN_URL+ "/us", headers=header)
    soup = BeautifulSoup(res.text, "html5lib")
    a = soup.find_all("div", attrs={"class": "column zn__column--idx-1"})
    urls = [url.get("href") for url in a]
    print(urls)
    return
    urls = list(dict.fromkeys(urls))
    urls = [f"https://apnews.com{url}" for url in urls if not url.startswith("https")]
    for url in urls:
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        title = soup.find("h1").get_text()
        try:
            body = soup.find("div", attrs={"class": "Article"}).get_text()
        except AttributeError:
            continue
        time = timezone.datetime.strptime(soup.find("span", attrs={"class": "Timestamp"}).get("data-source")[:-1], "%Y-%m-%dT%H:%M:%S")
        img = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Associated_Press_logo_2012.svg/1200px-Associated_Press_logo_2012.svg.png"
        try:
            if New.objects.get(title=title):
                print(f"[DATABASE] - {title} in database")
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="AssociatedPress"
                       )
            news.save()
            print(f"{title} has been saved successfully.")