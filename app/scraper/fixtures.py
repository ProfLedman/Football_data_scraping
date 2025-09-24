import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from app.scraper.selenium_driver import safe_get, wait_for_element

class FixtureScraper:
    def __init__(self):
        self.base_url = "https://fbref.com"
    
    def scrape_fixtures(self, driver: WebDriver, date: str, league: Optional[str] = None) -> List[Dict]:
        """Scrape fixtures for a specific date, handling empty results gracefully"""
        url = f"{self.base_url}/en/matches/{date}"
        
        try:
            if not safe_get(driver, url):
                raise Exception(f"Failed to load fixtures page for {date}")
            
            # Wait for page to load - look for any content, not just tables
            wait_for_element(driver, "css selector", "div.section_wrapper, table.stats_table", timeout=10)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Debug: Check what we actually got from the page
            sections = soup.find_all('div', class_='section_wrapper')
            print(f"DEBUG: Found {len(sections)} sections on page for {date}")
            
            big5_leagues = {
                "9": "Premier League", "12": "La Liga", "11": "Serie A",
                "20": "Bundesliga", "13": "Ligue 1"
            }
            
            fixtures = []
            leagues_found = set()
            
            for section in soup.find_all('div', class_='section_wrapper'):
                league_id = self._extract_league_id(section)
                if not league_id:
                    continue
                    
                league_name = big5_leagues.get(league_id)
                if not league_name:
                    continue  # Skip non-Big5 leagues
                
                leagues_found.add(league_name)
                
                # Apply league filter if specified
                if league and league != league_id:
                    continue
                
                section_fixtures = self._parse_league_section(section, league_name, date)
                fixtures.extend(section_fixtures)
                print(f"DEBUG: Found {len(section_fixtures)} fixtures for {league_name}")
            
            # Provide helpful debug information
            if not fixtures:
                if league:
                    # Specific league requested but no fixtures found
                    league_name = big5_leagues.get(league, f"League {league}")
                    print(f"INFO: No fixtures found for {league_name} on {date}")
                else:
                    # No fixtures found for any Big-5 league
                    if leagues_found:
                        print(f"INFO: Big-5 leagues found but no fixtures: {leagues_found}")
                    else:
                        print(f"INFO: No Big-5 league sections found for {date}")
            
            return fixtures
            
        except Exception as e:
            print(f"Error scraping fixtures for {date}: {e}")
            return []
    
    def _extract_league_id(self, section) -> Optional[str]:
        """Extract league ID from section HTML"""
        section_html = str(section)
        patterns = [r'comps_(\d+)', r'sched_(\d+)']
        for pattern in patterns:
            match = re.search(pattern, section_html)
            if match:
                return match.group(1)
        return None
    
    def _parse_league_section(self, section, league_name: str, date: str) -> List[Dict]:
        """Parse a league section for fixtures"""
        fixtures = []
        table = section.find('table', class_='stats_table')
        if not table:
            return fixtures
        
        tbody = table.find('tbody')
        if not tbody:
            return fixtures
        
        for row in tbody.find_all('tr'):
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            fixture = self._parse_fixture_row(row, league_name, date)
            if fixture:
                fixtures.append(fixture)
        
        return fixtures
    
    def _parse_fixture_row(self, row, league_name: str, date: str) -> Optional[Dict]:
        """Parse a single fixture row with better error handling"""
        cells = row.find_all(['th', 'td'])
        if len(cells) < 8:
            return None
        
        try:
            time_cell, home_cell, score_cell, away_cell = cells[2], cells[3], cells[5], cells[7]
            match_time = time_cell.get_text(strip=True)
            home_team = home_cell.get_text(strip=True)
            away_team = away_cell.get_text(strip=True)
            score = score_cell.get_text(strip=True)
            
            # Skip rows that are clearly not fixtures (empty or placeholder content)
            if not home_team or not away_team or home_team == 'Home' or away_team == 'Away':
                return None
            
            match_url = None
            if len(cells) > 11:
                report_link = cells[11].find('a')
                if report_link and report_link.get('href'):
                    href = report_link['href']
                    if href and href.startswith('/en/matches/'):
                        match_url = href
            
            home_url = home_cell.find('a')
            away_url = away_cell.find('a')
            
            return {
                'league': league_name,
                'date': date,
                'time': match_time,
                'home_team': home_team,
                'away_team': away_team,
                'score': score,
                'home_team_url': home_url['href'] if home_url else None,
                'away_team_url': away_url['href'] if away_url else None,
                'match_url': match_url,
                'match_id': match_url.split('/')[-2] if match_url else f"{home_team}_{away_team}_{date}".replace(' ', '_')
            }
            
        except Exception as e:
            print(f"Error parsing fixture row: {e}")
            return None