from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import requests
from .models import New
import re
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from django.core.exceptions import ValidationError

ISJ_URL = "https://www.idahostatejournal.com/"
EIN_URL = "https://www.eastidahonews.com/"
YAHOO_URL = "https://news.yahoo.com/"
NYT_URL = "https://www.nytimes.com/"
AP_URL = "https://apnews.com/"
CNN_URL = "https://www.cnn.com"
SKY_URL = "https://news.sky.com/"
WP_URL = "https://www.washingtonpost.com/"
header = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Accept-Language": "en-US,en;q=0.5"
}
today = datetime.now()
year = str(datetime.now().year)


def update_idaho_state_journal_db():
    res = requests.get(ISJ_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    urls = soup.find_all("h5", class_="tnt-headline")
    urls = [f"https://www.idahostatejournal.com{url.a.get('href')}" for url in urls]
    for url in urls:
        print(url)
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")

        title = soup.find("h1").get_text()
        new_title_formatted = " ".join(title.split())

        body = soup.find("div", class_="subscriber-premium")
        body_formatted = re.sub('[^p\.m\.|^\s\.|a-z]*\.', '. ', body.get_text(), flags=re.M)
        body_formatted = re.sub('^\s*[a-zA-Z\d]*\.[a-z\s]*$', "", body_formatted, flags=re.M)

        all_images = soup.find_all("img")
        all_images = [img.get("src") for img in all_images if "content/tncms/assets/v3/editorial" in img.get("src")]
        img = all_images[0][:-17]

        time = soup.find("time").get("datetime")[:-6]
        time = timezone.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")

        body_formatted = " ".join(body_formatted.split())
        try:
            if New.objects.get(title=new_title_formatted):
                print(f"[DATABASE] - {new_title_formatted} in database")
        except ObjectDoesNotExist:
            news = New(title=new_title_formatted,
                       body=body_formatted,
                       img=img,
                       url=url,
                       site="IdahoStateJournal",
                       date=time
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
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        title = soup.find("h1").get_text()

        all_images = soup.find_all("img")
        all_images = [img.get("src") for img in all_images if year in img.get("src")]
        img = all_images[0]

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


def update_yahoo_news_db():
    res = requests.get(YAHOO_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a
            if url.get("href").endswith(".html")
            and not url.get("href").startswith("https://legal")
            and "live" not in url.get("href")]
    urls = [f"https://news.yahoo.com{url}" for url in urls if not url.startswith("https")]
    for url in urls:
        print(url)
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")

        title = soup.find("h1").get_text()

        body = soup.find("div", attrs={"class": "caas-body"}).get_text()

        time = timezone.datetime.strptime(soup.find("time").get_text(), "%B %d, %Y, %I:%M %p")

        try:
            all_images = soup.find_all("img")
            all_images = [img.get("src") for img in all_images
                          if img.get("src") is not None
                          and "media.zenfs.com" in img.get("src")]
            img = all_images[0]
        except IndexError:
            img = "https://s.yimg.com/os/creatr-uploaded-images/2021-02/e8658bb0-7883-11eb-8e1f-504e25bc297b"

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


def update_new_york_times_db():
    FALLBACK_FORMATS = ("Updated %A, %B %d, %I:%M %p", "%B %d, %YUpdated %I:%M %p",
                        "%B %d, %Y, %I:%M %p", "Updated %B %d, %Y, %I:%M %p")
    res = requests.get(NYT_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")

    a = soup.find_all("a")

    urls = [url.get("href") for url in a
            if str(year) in url.get("href")
            and "live" not in url.get("href")
            and "interactive" not in url.get("href")]
    urls = list(dict.fromkeys(urls))

    for url in urls:
        print(url)
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")

        try:
            title = soup.find("h1").get_text()
        except AttributeError:
            continue

        body = soup.find_all("p")
        body = " ".join([i.get_text() for i in body])

        time = soup.find("time").get_text()
        if "Updated" in time:
            time.replace("Updated", "")
        if "Published" in time:
            time = time[24:]
        if "p.m." in time:
            for form in FALLBACK_FORMATS:
                try:
                    time = datetime.strptime(f"{time[:-8]} PM", form)
                except ValueError:
                    pass
                else:
                    break
        elif "a.m." in time:
            for form in FALLBACK_FORMATS:
                try:
                    time = datetime.strptime(f"{time[:-8]} AM", form)
                except ValueError:
                    pass
                else:
                    break

        all_images = soup.find_all("img")
        all_images = [img.get("src") for img in all_images if img.get("src").startswith("https")]
        img = all_images[0]

        try:
            if New.objects.get(title=title):
                print(f"[DATABASE] - {title} in database")
        except ObjectDoesNotExist:
            try:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time,
                           site="NewYorkTimes"
                           )
                news.save()
                print(f"{title} has been saved successfully.")
            except ValidationError:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=today,
                           site="AssociatedPress"
                           )
                news.save()
                print(f"{title} has been saved successfully.")
        sleep(1)


def update_associated_press_db():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path="/home/rodrigo/Downloads/geckodriver-v0.30.0-linux64/geckodriver",
                               options=options)
    driver.get(AP_URL)
    a = driver.find_elements(By.TAG_NAME, "a")

    urls = [url.get_attribute("href") for url in a
            if "article" in url.get_attribute("href")
            and "mailto" not in url.get_attribute("href")
            and "twitter" not in url.get_attribute("href")
            and "facebook" not in url.get_attribute("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        print(url)
        driver.get(url)

        title = driver.title
        try:
            body = driver.find_element(by=By.CLASS_NAME, value="Article").text
        except NoSuchElementException:
            body = driver.find_element(by=By.CLASS_NAME, value="article-0-2-23").text

        time = driver.find_element(by=By.CLASS_NAME, value="Timestamp").get_attribute("data-source")
        time = datetime.strptime(time[:-1], "%Y-%m-%dT%H:%M:%S")

        try:
            all_images = driver.find_elements(by=By.TAG_NAME, value="img")
            all_images = [img.get_attribute("src") for img in all_images
                          if img.get_attribute("src") is not None
                          and "googleapis" in img.get_attribute("src")]
            img = all_images[0]
        except (StaleElementReferenceException, IndexError):
            img = "http://logok.org/wp-content/uploads/2014/04/Associated-Press-logo-2012-AP-880x660.png"

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
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path="/home/rodrigo/Downloads/geckodriver-v0.30.0-linux64/geckodriver",
                               options=options)
    driver.get(CNN_URL)
    a = driver.find_elements(By.TAG_NAME, "a")
    urls = [url.get_attribute("href") for url in a
            if url.get_attribute("href") is not None
            and year in url.get_attribute("href")
            and "election" not in url.get_attribute("href")
            and "videos" not in url.get_attribute("href")
            and "gallery" not in url.get_attribute("href")
            and "financebuzz" not in url.get_attribute("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        try:
            driver.get(url)
            title = driver.title
            body = driver.find_element(by=By.CLASS_NAME, value="l-container").text
            time = driver.find_element(by=By.CLASS_NAME, value="update-time").text
            if "Updated" in time:
                time = time[8:]
            time = timezone.datetime.strptime(time, "%I:%M %p ET, %a %B %d, %Y")
            img = [i.get_attribute("src") for i in driver.find_elements(by=By.TAG_NAME, value="img")
                   if "cnnnext/dam/assets/" in i.get_attribute("src")
                   and not "small" in i.get_attribute("src")][0]
            try:
                if New.objects.get(title=title):
                    print(f"[DATABASE] - {title} in database")
            except ObjectDoesNotExist:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time,
                           site="CNN"
                           )
                news.save()
                print(f"{title} has been saved successfully.")
        except WebDriverException:
            driver.quit()
            sleep(2)
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Firefox(
                executable_path="/home/rodrigo/Downloads/geckodriver-v0.30.0-linux64/geckodriver", options=options)
            continue


def update_sky_news_db():
    res = requests.get(SKY_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a
            if "story" in url.get("href")
            and "live-updates" not in url.get("href")
            and "a-question" not in url.get("href")]
    urls = [f"https://news.sky.com{url}" for url in urls if url.startswith("/story/")] + [url for url in urls if
                                                                                          url.startswith("https")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        title = soup.find("h1").get_text()
        try:
            p = soup.find("p", attrs={"class": "sdc-site-component-header--h2"}).get_text()
            body = p + soup.find("div", attrs={"class": "sdc-article-body"}).get_text()
            body = body.replace("Please use Chrome browser for a more accessible video player", "")
            body = re.sub('^\s+$', "", body, flags=re.M)
            time = soup.find("p", attrs={"class": "sdc-article-date__date-time"}).get_text()
            time = timezone.datetime.strptime(time, "%A %d %B %Y %H:%M, UK")

        except AttributeError:
            continue
        images = soup.find_all("img")
        images = [img.get("src") for img in images if img.get("src").startswith("https")][0]
        try:
            if New.objects.get(title=title):
                print(f"[DATABASE] - {title} in database")
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=images,
                       url=url,
                       date=time,
                       site="SkyNews"
                       )
            news.save()
            print(f"{title} has been saved successfully.")
        sleep(1)


def update_washington_post_db():
    res = requests.get(WP_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a
            if year in url.get("href")
            and "live" not in url.get("href")
            and "interactive" not in url.get("href")
            and "weather" not in url.get("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        print(url)
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        title = soup.find("h1").get_text()
        try:
            body = soup.find("div", attrs={"class": "article-body"}).get_text()
        except AttributeError:
            continue
        time = soup.find("span", attrs={"class": "display-date"}).get_text()
        print(time)
        if "a.m." in time:
            try:
                time = timezone.datetime.strptime(f"{today.year} {today.month} {today.day} {time[:-8]} AM",
                                                  "%Y %m %d %H:%M %p")
            except ValueError:
                time = timezone.datetime.strptime(time[:-8] + "AM",
                                                  "%B %d, %Y at %H:%M %p")
        elif "p.m." in time:
            try:
                time = timezone.datetime.strptime(f"{today.year} {today.month} {today.day} {time[:-8]} PM",
                                                  "%Y %m %d %H:%M %p")
            except ValueError:
                time = timezone.datetime.strptime(time[:-8] + "PM",
                                                  "%B %d, %Y at %H:%M %p")

        else:
            time = timezone.datetime.strptime(time, "%B %d, %Y")
        try:
            images = soup.find_all("img")
            images = [img.get("srcset") for img in images][0]
            img = images.split()[-2].split(",")[1]
        except AttributeError:
            img = "https://assets.themuse.com/uploaded/companies/1360/small_logo.png"
        except IndexError:
            img = "https://assets.themuse.com/uploaded/companies/1360/small_logo.png"
        try:
            if New.objects.get(title=title):
                print(f"[DATABASE] - {title} in database")
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="WashingtonPost"
                       )
            news.save()
            print(f"{title} has been saved successfully.")
        sleep(1)
