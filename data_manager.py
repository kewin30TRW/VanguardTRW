from fetchData import update_all_data
from hmm_processor import process_data

class DataManager:
    def __init__(self, addresses):
        self.addresses = addresses

    def update_all_data(self):
        update_all_data()
        for file_path in self.addresses.values():
            process_data(file_path)


from apscheduler.schedulers.background import BackgroundScheduler

class SchedulerManager:
    def __init__(self, update_function):
        self.scheduler = BackgroundScheduler()
        self.update_function = update_function
        self.configure_scheduler()

    def configure_scheduler(self):
        self.scheduler.add_job(self.update_function, 'interval', hours=1)
        self.scheduler.start()