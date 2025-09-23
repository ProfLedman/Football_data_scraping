import time
import random
from app.config import settings

class AntiBotHandler:
    def __init__(self):
        self.delay_min = settings.REQUEST_DELAY_MIN
        self.delay_max = settings.REQUEST_DELAY_MAX
        self.retry_count = 0
    
    def random_delay(self, min_delay=None, max_delay=None):
        min_delay = min_delay or self.delay_min
        max_delay = max_delay or self.delay_max
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def exponential_backoff(self, attempt):
        base_delay = self.delay_min
        backoff_delay = base_delay * (settings.BACKOFF_FACTOR ** attempt)
        max_delay = self.delay_max * 3
        delay = min(backoff_delay, max_delay)
        time.sleep(delay)
    
    def should_retry(self):
        self.retry_count += 1
        return self.retry_count <= settings.MAX_RETRIES
    
    def reset_retry_count(self):
        self.retry_count = 0
    
    def human_like_scroll(self, driver):
        scroll_actions = [
            lambda: driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);"),
            lambda: driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);"),
            lambda: driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
        ]
        for action in scroll_actions:
            action()
            time.sleep(random.uniform(0.5, 1.5))