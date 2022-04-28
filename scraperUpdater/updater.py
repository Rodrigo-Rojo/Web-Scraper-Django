from apscheduler.schedulers.background import BackgroundScheduler
from .scraper import *


def start():
    scheduler = BackgroundScheduler()
    timer = 30
    jobs = (update_idaho_state_journal_db,
            update_cnn_db,
            update_sky_news_db,
            update_yahoo_news_db,
            update_washington_post_db,
            update_associated_press_db,
            update_east_idaho_news_db,
            update_new_york_times_db)

    for job in jobs:
        scheduler.add_job(job, 'interval', minutes=timer)
        timer += 3
        print(job)

    scheduler.start()
