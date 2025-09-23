import time
import random
from typing import Dict, List, Optional
from app.scraper.selenium_driver import get_driver
from app.scraper.fixtures import FixtureScraper
from app.scraper.match_data import MatchDataScraper
from app.scraper.anti_bot import AntiBotHandler
from app.config import settings

class FBrefScraper:
    def __init__(self):
        self.driver = None
        self.anti_bot = AntiBotHandler()
        self.fixture_scraper = FixtureScraper()
        self.match_scraper = MatchDataScraper()
    
    def get_fixtures_by_date(self, date: str, league: Optional[str] = None) -> List[Dict]:
        """Get fixtures for a specific date"""
        self._setup_driver()
        
        try:
            fixtures = self.fixture_scraper.scrape_fixtures(self.driver, date, league)
            return fixtures
        finally:
            self._teardown_driver()
    
    def scrape_match_data(self, match_url: str) -> Dict:
        """Scrape comprehensive match data"""
        self._setup_driver()
        
        try:
            self.anti_bot.random_delay()
            match_data = self.match_scraper.scrape_match(self.driver, match_url)
            return match_data
        finally:
            self._teardown_driver()
    
    def scrape_player_data(self, match_data: Dict) -> Dict:
        """Scrape player data for a match"""
        self._setup_driver()
        
        try:
            player_data = {}
            players = match_data.get('players', [])
            
            for i, player in enumerate(players):
                self.anti_bot.random_delay()
                player_info = self.match_scraper.scrape_player(self.driver, player['url'])
                player_data[player['id']] = player_info
                
                # Update progress
                progress = 60 + (i / len(players)) * 30
                # Would update task progress here
            
            return player_data
        finally:
            self._teardown_driver()
    
    def _setup_driver(self):
        """Setup Selenium driver"""
        if not self.driver:
            self.driver = get_driver()
    
    def _teardown_driver(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None