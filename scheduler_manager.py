from apscheduler.schedulers.background import BackgroundScheduler
import atexit

class SchedulerManager:
    def __init__(self, update_function):
        self.scheduler = BackgroundScheduler()
        self.update_function = update_function
        self.configure_scheduler()
        atexit.register(lambda: self.scheduler.shutdown())

    def configure_scheduler(self):
        self.scheduler.add_job(self.update_function, trigger='cron', minute=10)
        self.scheduler.start()