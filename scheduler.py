from apscheduler.schedulers.background import BackgroundScheduler
import atexit

def configure_scheduler(job_func, interval='cron', minute=10):
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_func, interval, minute=minute)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
