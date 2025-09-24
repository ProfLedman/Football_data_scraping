from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.config import settings

import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver(headless: bool = None):
    """Get configured Chrome driver with better error handling"""
    if headless is None:
        headless = settings.SCRAPER_HEADLESS
    
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Anti-detection settings
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Disable GCM to avoid authentication errors
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    
    # Set window size and user agent
    chrome_options.add_argument(f"--window-size={settings.SELENIUM_WINDOW_SIZE}")
    chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
    
    try:
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Additional anti-detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set timeouts
        driver.implicitly_wait(settings.SELENIUM_IMPLICIT_WAIT)
        driver.set_page_load_timeout(settings.SELENIUM_PAGE_LOAD_TIMEOUT)
        
        return driver
    except Exception as e:
        print(f"Error creating Chrome driver: {e}")
        raise


def get_random_user_agent():
    """Get random user agent from list"""
    # This would load from config/user_agents.txt
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    return random.choice(user_agents)

def safe_get(driver, url, timeout=None):
    """Safely get a URL with optional timeout handling."""
    try:
        if timeout:
            driver.set_page_load_timeout(timeout)
        driver.get(url)
        return True
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return False
    

def wait_for_element(driver, by, value, timeout=10):
    """Wait for an element to be present and return it."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except Exception as e:
        print(f"Element not found: {value} ({by}) - {e}")
        return None