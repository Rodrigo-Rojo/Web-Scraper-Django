from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import requests
from scraper.models import New
import re
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, StaleElementReferenceException, TimeoutException
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
    print(f"[DATABASE]: Updating Idaho State Journal.")
    res = requests.get(ISJ_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    urls = soup.find_all("h5", class_="tnt-headline")
    urls = [f"https://www.idahostatejournal.com{url.a.get('href')}" for url in urls]
    for url in urls:
        sleep(5)
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
                continue
        except ObjectDoesNotExist:
            news = New(title=new_title_formatted,
                       body=body_formatted,
                       img=img,
                       url=url,
                       site="Idaho State Journal",
                       date=time
                       )
            news.save()
    print(f"[DATABASE]: Idaho State Journal Update Successfully.")


def update_east_idaho_news_db():
    print(f"[DATABASE]: Updating East Idaho News.")

    res = requests.get(EIN_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a if url.get("href") is not None and str(year) in url.get("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        sleep(5)
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
                continue
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="East Idaho News"
                       )
            news.save()
    print(f"[DATABASE]: East Idaho News Update Done Successfully.")


def update_yahoo_news_db():
    print(f"[DATABASE]: Updating Yahoo News.")
    res = requests.get(YAHOO_URL, headers=header)
    soup = BeautifulSoup(res.text, "html.parser")
    a = soup.find_all("a")
    urls = [url.get("href") for url in a
            if url.get("href").endswith(".html")
            and not url.get("href").startswith("https://legal")
            and "live" not in url.get("href")]
    urls = [f"https://news.yahoo.com{url}" for url in urls if not url.startswith("https")]
    for url in urls:
        sleep(5)
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
                continue
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="Yahoo News"
                       )
            news.save()
    print(f"[DATABASE]: Yahoo News Update Done Successfully")


def update_new_york_times_db():
    print(f"[DATABASE]: Updating New York Times.")

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

        sleep(5)
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
        except AttributeError:
            time = timezone.datetime.now()

        try:
            all_images = soup.find_all("img")
            all_images = [img.get("src") for img in all_images if img.get("src").startswith("https")]
            img = all_images[0]
        except IndexError:
            img = "https://static01.nyt.com/vi-assets/images/share/1200x1200_t.png"
        try:
            if New.objects.get(title=title):
                continue
        except ObjectDoesNotExist:
            try:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time,
                           site="New York Times"
                           )
                news.save()
            except ValidationError:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=today,
                           site="New York Times"
                           )
                news.save()
    print(f"[DATABASE]: New York Times Update Done Successfully")


def update_associated_press_db():
    print(f"[DATABASE]: Updating Associated Press.")

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    driver.get(AP_URL)
    a = driver.find_elements(By.TAG_NAME, "a")

    urls = [url.get_attribute("href") for url in a
            if "article" in url.get_attribute("href")
            and "mailto" not in url.get_attribute("href")
            and "twitter" not in url.get_attribute("href")
            and "facebook" not in url.get_attribute("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        body_classes = ("Article", "article-0-2-23", "article-0-2-21")
        sleep(5)
        print(url)
        driver.get(url)

        title = driver.title
        for body_class in body_classes:
            try:
                body = driver.find_element(by=By.CLASS_NAME, value=body_class).text
            except NoSuchElementException:
                continue
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
                continue
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="Associated Press"
                       )
            news.save()
        except WebDriverException:
            driver.quit()
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

            continue
    print(f"[DATABASE]: Associated Press Update Done Successfully")


def update_cnn_db():
    print(f"[DATABASE]: Updating CNN.")

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    driver.get(CNN_URL)
    a = driver.find_elements(By.TAG_NAME, "a")
    urls = [url.get_attribute("href") for url in a
            if url.get_attribute("href") is not None
            and year in url.get_attribute("href")
            and "election" not in url.get_attribute("href")
            and "videos" not in url.get_attribute("href")
            and "gallery" not in url.get_attribute("href")
            and "financebuzz" not in url.get_attribute("href")
            and "specials" not in url.get_attribute("href")
            and "style" not in url.get_attribute("href")]
    urls = list(dict.fromkeys(urls))
    for url in urls:
        try:
            print(url)
            driver.get(url)
            title = driver.title
            try:
                body = driver.find_element(by=By.CLASS_NAME, value="l-container").text
            except NoSuchElementException:
                continue
            try:
                time = driver.find_element(by=By.CLASS_NAME, value="update-time").text
                if "Updated" in time and "GMT" not in time:
                    time = time[8:]
                    time = timezone.datetime.strptime(time, "%I:%M %p ET, %a %B %d, %Y")
                if "GMT" in time:
                    str_to_remove = time[17:27]
                    time = time.replace(str_to_remove, "")
                    time = timezone.datetime.strptime(time, "Updated %H%M GMT  %B %d, %Y")
            except NoSuchElementException:
                time = timezone.datetime.now()
            try:
                all_images = driver.find_elements(by=By.TAG_NAME, value="img")
                all_images = [i.get_attribute("src") for i in all_images
                              if "cnnnext/dam/assets/" in i.get_attribute("src")
                              and not "small" in i.get_attribute("src")]
                img = all_images[0]
            except (IndexError, StaleElementReferenceException):
                img = "https://www.logodesignlove.com/wp-content/uploads/2010/06/cnn-logo-white-on-red.jpg"
            try:
                if New.objects.get(title=title):
                    continue
            except ObjectDoesNotExist:
                news = New(title=title,
                           body=body,
                           img=img,
                           url=url,
                           date=time,
                           site="CNN"
                           )
                news.save()
        except WebDriverException as e:
            print(f"[WebdriverError Restarting] {e}")
            driver.quit()
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
            continue

    print(f"[DATABASE]: CNN Update Done Successfully")


def update_sky_news_db():
    print(f"[DATABASE]: Updating Sky News.")

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
        sleep(5)
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        try:
            title = soup.find("h1").get_text()

            p = soup.find("p", attrs={"class": "sdc-site-component-header--h2"}).get_text()

            body = p + soup.find("div", attrs={"class": "sdc-article-body"}).get_text()
            body = body.replace("Please use Chrome browser for a more accessible video player", "")
            body = re.sub('^\s+$', "", body, flags=re.M)

            time = soup.find("p", attrs={"class": "sdc-article-date__date-time"}).get_text()
            time = timezone.datetime.strptime(time, "%A %d %B %Y %H:%M, UK")
        except AttributeError as e:
            continue
        try:
            all_images = soup.find_all("img")
            all_images = [img.get("src") for img in all_images if img.get("src").startswith("https")]
            img = all_images[0]
        except AttributeError:
            img = "https://i.ytimg.com/vi/9Auq9mYxFEE/maxresdefault.jpg"
        try:
            if New.objects.get(title=title):
                continue
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="Sky News"
                       )
            news.save()
    print(f"[DATABASE]: Sky News Update Done Successfully.")


def update_washington_post_db():
    print(f"[DATABASE]: Updating Washington Post.")

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
        sleep(5)
        res = requests.get(url, headers=header)
        site_html = res.text
        soup = BeautifulSoup(site_html, "html.parser")
        title = soup.find("h1").get_text()
        try:
            body = soup.find("div", attrs={"class": "article-body"}).get_text()
        except AttributeError:
            continue
        time = soup.find("span", attrs={"class": "display-date"}).get_text()
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
                continue
        except ObjectDoesNotExist:
            news = New(title=title,
                       body=body,
                       img=img,
                       url=url,
                       date=time,
                       site="Washington Post"
                       )
            news.save()
    print(f"[DATABASE]: Washington Post Update Done Successfully.")

