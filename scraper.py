from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import pandas as pd

def setup_driver():
    """Setup Chrome driver with anti-detection options"""
    chrome_options = Options()
    
    # Anti-detection settings
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set a common user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Initialize driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional anti-detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_fbref_matches():
    """Scrape match data from FBref using Selenium"""
    driver = setup_driver()
    fixtures = []
    
    try:
        print("Loading FBref matches page...")
        driver.get("https://fbref.com/en/matches/")
        
        # Wait for page to load completely
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Optional: Scroll to ensure all content loads
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        print("Page loaded successfully. Parsing data...")
        
        # Loop through each competition section
        for header in soup.find_all("h2"):
            competition = header.get_text(strip=True).replace(" Scores & Fixtures", "")
            table = header.find_next("table")
            
            if not table:
                continue

            # Extract headers from the table
            try:
                headers_row = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
            except AttributeError:
                print(f"No headers found for {competition}, skipping...")
                continue

            tbody = table.find("tbody")
            if not tbody:
                continue

            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue  # skip header/separator rows

                row_data = {"Competition": competition}

                # Map cells to their respective headers
                for i, cell in enumerate(cells):
                    col_name = headers_row[i+1] if i+1 < len(headers_row) else f"Col_{i}"
                    row_data[col_name] = cell.get_text(strip=True) if cell else None

                    # Capture match link if available
                    link = cell.find("a")
                    if link and "href" in link.attrs:
                        row_data[f"{col_name}_URL"] = "https://fbref.com" + link["href"]

                fixtures.append(row_data)
        
        return fixtures
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
    
    finally:
        # Always close the driver
        driver.quit()
        print("Browser closed.")

def save_to_csv(fixtures, filename="fbref_fixtures.csv"):
    """Save fixtures data to CSV"""
    if fixtures:
        df = pd.DataFrame(fixtures)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return df
    return None

def main():
    """Main function to run the scraper"""
    print("Starting FBref scraper with Selenium...")
    
    # Scrape the data
    fixtures = scrape_fbref_matches()
    
    # Display results
    print(f"\nCollected {len(fixtures)} fixtures")
    
    if fixtures:
        # Show first 5 fixtures
        for i, fix in enumerate(fixtures[:5]):
            print(f"\nFixture {i+1}:")
            for key, value in fix.items():
                print(f"  {key}: {value}")
        
        # Save to CSV
        df = save_to_csv(fixtures)
        
        # Show summary by competition
        if df is not None and 'Competition' in df.columns:
            print(f"\nSummary by competition:")
            print(df['Competition'].value_counts())
    else:
        print("No fixtures found.")

if __name__ == "__main__":
    main()