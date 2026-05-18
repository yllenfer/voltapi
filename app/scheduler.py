from apscheduler.schedulers.background import BackgroundScheduler
from app.scraper_runner import run_all_scrapers

_scheduler = BackgroundScheduler()


def start_scheduler():
    # Re-scrape all providers every 6 hours
    _scheduler.add_job(run_all_scrapers, "interval", hours=6, id="scrape_all")
    _scheduler.start()
    print("Scheduler started — scraping every 6 hours")
