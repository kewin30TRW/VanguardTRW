from apscheduler.schedulers.background import BackgroundScheduler

class SchedulerManager:
    def __init__(self, update_function):
        self.scheduler = BackgroundScheduler()
        self.update_function = update_function
        self.configure_scheduler()

    def configure_scheduler(self):
        self.scheduler.add_job(self.update_function, 'interval', hours=1)
        self.scheduler.start()