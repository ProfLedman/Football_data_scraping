from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.config import settings

def get_driver(headless: bool = None):
    """Get configured Chrome driver"""
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
    
    # Set window size and user agent
    chrome_options.add_argument(f"--window-size={settings.SELENIUM_WINDOW_SIZE}")
    chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
    
    # Initialize driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional anti-detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Set timeouts
    driver.implicitly_wait(settings.SELENIUM_IMPLICIT_WAIT)
    driver.set_page_load_timeout(settings.SELENIUM_PAGE_LOAD_TIMEOUT)
    
    return driver

def get_random_user_agent():
    """Get random user agent from list"""
    # This would load from config/user_agents.txt
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    return random.choice(user_agents)