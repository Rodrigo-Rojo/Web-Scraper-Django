from bs4 import BeautifulSoup
import requests
from .models import WebScraper
import re


SITE_URL = "https://www.idahostatejournal.com/"
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
}


def update_db():
    res = requests.get(SITE_URL, headers=header)
    site_html = res.text

    soup = BeautifulSoup(site_html, "html.parser")
    urls = soup.find_all("h5", class_="tnt-headline")
    urls = [f"https://www.idahostatejournal.com{url.a.get('href')}" for url in urls]

    for url in urls:
        res = requests.get("https://www.idahostatejournal.com/news/local/local-child-diagnosed-with-dementia-s"
                           "he-s-going-to-un-develop-before-our-eyes/article_c0bae9fc-f689-5bc3-b36b-1988f493d6b0.html",
                           headers=header)
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
        print(body_formatted)
        return

        news = WebScraper(title=new_title_formatted,
                          # '[^p\.m\.|^\s\.|a-z]*\.' to look for any dots in body except of p.m.
                          # then we proceed to add a new line
                          body=body_formatted,
                          img=new_img,
                          url=url
                          )
        news.save()
        print(f"{new_title_formatted} has been saved successfully.")
