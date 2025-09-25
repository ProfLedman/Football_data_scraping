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
            print(f"DEBUG: Attempting to load URL: {url}")
            if not safe_get(driver, url):
                raise Exception(f"Failed to load fixtures page for {date}")
            
            print("DEBUG: Initial page source length:", len(driver.page_source))
            wait_for_element(driver, "css selector", "div.section_wrapper, table.stats_table", timeout=10)
            print("DEBUG: Page loaded, creating BeautifulSoup")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            print("DEBUG: Page structure:")
            print("- Title:", soup.title.string if soup.title else "No title")
            print("- Number of tables:", len(soup.find_all('table')))
            print("- Number of sections:", len(soup.find_all('div', class_='section_wrapper')))
            
            if soup.find('div', class_='error') or soup.find('div', class_='status-code'):
                print("DEBUG: Possible error page detected")
            
            fixtures = []
            leagues_found = set()
            big5_leagues = {
                "9": "Premier League", "12": "La Liga", "11": "Serie A",
                "20": "Bundesliga", "13": "Ligue 1"
            }
            
            # Get all schedule tables and their containers
            containers = soup.find_all('div', id=lambda x: x and x.startswith('all_sched_'))
            print(f"DEBUG: Found {len(containers)} schedule containers")
            
            for container in containers:
                container_id = container.get('id', '')
                print(f"DEBUG: Processing container {container_id}")
                
                # Extract league ID from container
                league_id = None
                for lid in big5_leagues.keys():
                    if f"_{lid}" in container_id.split("sched_")[-1]:
                        league_id = lid
                        print(f"DEBUG: Found league {lid} from container {container_id}")
                        break
                
                if not league_id:
                    # Try to find league from header
                    header = container.find('h2')
                    if header:
                        header_text = header.get_text(strip=True)
                        print(f"DEBUG: Found header: {header_text}")
                        for lid, name in big5_leagues.items():
                            if name.lower() in header_text.lower():
                                league_id = lid
                                break
                
                if not league_id:
                    print(f"DEBUG: No league ID found for container {container_id}")
                    continue
                
                league_name = big5_leagues[league_id]
                leagues_found.add(league_name)
                
                # Apply league filter if specified
                if league and league != league_id:
                    continue
                
                # Find the table within the container
                table = container.find('table', class_='stats_table')
                if not table:
                    print(f"DEBUG: No table found in container for {league_name}")
                    continue
                
                # Parse fixtures from this table
                table_fixtures = self._parse_league_section(table, league_name, date)
                if table_fixtures:
                    fixtures.extend(table_fixtures)
                    print(f"DEBUG: Found {len(table_fixtures)} fixtures for {league_name}")
                else:
                    print(f"DEBUG: No fixtures found in table for {league_name}")
            
            # Provide helpful debug information
            if not fixtures:
                if league:
                    league_name = big5_leagues.get(league, f"League {league}")
                    print(f"INFO: No fixtures found for {league_name} on {date}")
                else:
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
        
        # If section is already a table, use it directly
        if section.name == 'table':
            table = section
        else:
            table = section.find('table', class_='stats_table')
        
        if not table:
            print(f"DEBUG: No table found for {league_name}")
            return fixtures
        
        tbody = table.find('tbody')
        if not tbody:
            print(f"DEBUG: No tbody found for {league_name}")
            return fixtures
        
        print(f"DEBUG: Processing {len(tbody.find_all('tr'))} rows for {league_name}")
        
        for row in tbody.find_all('tr'):
            fixture = self._parse_fixture_row(row, league_name, date)
            if fixture:
                fixtures.append(fixture)
                print(f"DEBUG: Added fixture: {fixture['home_team']} vs {fixture['away_team']}")
        
        return fixtures 


    def _parse_fixture_row(self, row, league_name: str, date: str) -> Optional[Dict]:
        """Parse a single fixture row using data-stat attributes - FIXED VERSION"""
        try:
            # Use data-stat attributes for reliable parsing
            time_cell = row.find('td', {'data-stat': 'start_time'})
            home_cell = row.find('td', {'data-stat': 'home_team'})
            away_cell = row.find('td', {'data-stat': 'away_team'})
            score_cell = row.find('td', {'data-stat': 'score'})
            match_report_cell = row.find('td', {'data-stat': 'match_report'})
            
            # Extract text content
            match_time = time_cell.get_text(strip=True) if time_cell else ''
            
            # Extract team names from anchor tags
            home_team = ''
            home_url = None
            if home_cell:
                home_link = home_cell.find('a')
                if home_link:
                    home_team = home_link.get_text(strip=True)
                    home_url = home_link.get('href')
                else:
                    home_team = home_cell.get_text(strip=True)
            
            away_team = ''
            away_url = None
            if away_cell:
                away_link = away_cell.find('a')
                if away_link:
                    away_team = away_link.get_text(strip=True)
                    away_url = away_link.get('href')
                else:
                    away_team = away_cell.get_text(strip=True)
            
            score = score_cell.get_text(strip=True) if score_cell else ''
            
            # Skip rows that are clearly not fixtures
            if not home_team or not away_team or home_team == 'Home' or away_team == 'Away':
                return None
            
            # Extract match report URL
            match_url = None
            if match_report_cell:
                report_link = match_report_cell.find('a')
                if report_link and report_link.get('href'):
                    href = report_link['href']
                    # Accept both match report and head-to-head links
                    if href and ('/matches/' in href or '/stathead/matchup' in href):
                        match_url = href
            
            return {
                'league': league_name,
                'date': date,
                'time': match_time,
                'home_team': home_team,
                'away_team': away_team,
                'score': score,
                'home_team_url': home_url,
                'away_team_url': away_url,
                'match_url': match_url,
                'match_id': match_url.split('/')[-2] if match_url else f"{home_team}_{away_team}_{date}".replace(' ', '_')
            }
            
        except Exception as e:
            print(f"Error parsing fixture row: {e}")
            return None
        

    def test_specific_fixture_parsing(self):
        """Test method to verify we can parse the specific fixture structure"""
        test_html = """
        <tr data-row="2">
            <th scope="row" class="left sort_show" data-stat="round"></th>
            <td class="right sort_show" data-stat="gameweek">6</td>
            <td class="right " data-stat="start_time" csk="15:00:00"></td>
            <td class="right " data-stat="home_team">
                <a href="/en/squads/47c64c55/Crystal-Palace-Stats">Crystal Palace</a>
            </td>
            <td class="right iz" data-stat="home_xg"></td>
            <td class="center iz" data-stat="score"></td>
            <td class="right iz" data-stat="away_xg"></td>
            <td class="left " data-stat="away_team">
                <a href="/en/squads/822bd0ba/Liverpool-Stats">Liverpool</a>
            </td>
            <td class="right iz" data-stat="attendance"></td>
            <td class="left " data-stat="venue">Selhurst Park</td>
            <td class="left iz" data-stat="referee" csk="2025-09-27"></td>
            <td class="left " data-stat="match_report">
                <a href="/en/stathead/matchup/teams/822bd0ba/47c64c55/Liverpool-vs-Crystal-Palace-History">Head-to-Head</a>
            </td>
            <td class="left iz" data-stat="notes"></td>
        </tr>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(test_html, 'html.parser')
        row = soup.find('tr')
        
        fixture = self._parse_fixture_row(row, "Premier League", "2025-09-27")
        print("TEST PARSING RESULT:")
        print(fixture)
        
        return fixture