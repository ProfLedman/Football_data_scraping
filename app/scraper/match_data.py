import re
import pandas as pd
from typing import Dict, List
from bs4 import BeautifulSoup, Comment
from selenium.webdriver.remote.webdriver import WebDriver
from app.scraper.selenium_driver import safe_get, wait_for_element
from app.scraper.anti_bot import AntiBotHandler

class MatchDataScraper:
    def __init__(self):
        self.anti_bot = AntiBotHandler()
        self.base_url = "https://fbref.com"
    
    def scrape_match(self, driver: WebDriver, match_url: str) -> Dict:
        full_url = f"{self.base_url}{match_url}"
        
        try:
            if not safe_get(driver, full_url):
                raise Exception("Failed to load match page")
            
            wait_for_element(driver, "tag name", "table")
            self.anti_bot.human_like_scroll(driver)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            return {
                'match_info': self._extract_match_info(soup, match_url),
                'home_team': self._extract_team_data(soup, 'home'),
                'away_team': self._extract_team_data(soup, 'away'),
                'players': self._extract_player_ids(soup)
            }
        except Exception as e:
            print(f"Error scraping match data: {e}")
            return {}
    
    def _extract_match_info(self, soup: BeautifulSoup, match_url: str) -> Dict:
        match_info = {'url': match_url, 'match_id': match_url.split('/')[-2]}
        team_elements = soup.find_all('a', href=re.compile(r'/en/squads/'))
        teams = []
        for element in team_elements:
            team_name = element.get_text(strip=True)
            if team_name and team_name not in teams:
                teams.append(team_name)
                match_info[f'team_{len(teams)}'] = team_name
                match_info[f'team_{len(teams)}_url'] = element.get('href')
        return match_info
    
    def _extract_team_data(self, soup: BeautifulSoup, team_side: str) -> Dict:
        team_data = {}
        team_tables = soup.find_all('table', id=re.compile(f'.*_{team_side}.*'))
        
        for i, table in enumerate(team_tables):
            table_id = table.get('id', f'unknown_{i}')
            tables_data = self._extract_tables_from_html(str(table))
            
            for j, table_df in enumerate(tables_data):
                if not table_df.empty:
                    sheet_name = f"{team_side}_{table_id}_{j}"
                    team_data[sheet_name] = table_df.to_dict('records')
        
        return team_data
    
    def _extract_player_ids(self, soup: BeautifulSoup) -> List[Dict]:
        players = []
        player_links = soup.find_all('a', href=re.compile(r'/en/players/'))
        
        for link in player_links:
            href = link.get('href')
            if href and 'matchlogs' not in href:
                player_id = href.split('/')[-2]
                player_name = link.get_text(strip=True)
                if (player_id and player_name and 
                    player_id not in [p['id'] for p in players] and
                    len(player_name) > 1):
                    players.append({'id': player_id, 'name': player_name, 'url': href})
        
        return players[:22]
    
    def scrape_player_data(self, driver: WebDriver, player_url: str) -> Dict:
        full_url = f"{self.base_url}{player_url}"
        
        try:
            if not safe_get(driver, full_url):
                raise Exception("Failed to load player page")
            
            wait_for_element(driver, "tag name", "table")
            self.anti_bot.random_delay()
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            player_data = {}
            tables_data = self._extract_tables_from_html(driver.page_source)
            
            for i, table_df in enumerate(tables_data):
                if not table_df.empty:
                    player_data[f"player_table_{i}"] = table_df.to_dict('records')
            
            return player_data
        except Exception as e:
            print(f"Error scraping player data: {e}")
            return {}
    
    def _extract_tables_from_html(self, html_content: str) -> List[pd.DataFrame]:
        soup = BeautifulSoup(html_content, 'html.parser')
        tables_data = []
        
        for table in soup.find_all('table'):
            df = self._parse_html_table(table)
            if df is not None and not df.empty:
                tables_data.append(df)
        
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            for table in comment_soup.find_all('table'):
                df = self._parse_html_table(table)
                if df is not None and not df.empty:
                    tables_data.append(df)
        
        return tables_data
    
    def _parse_html_table(self, table) -> pd.DataFrame:
        try:
            headers = []
            header_row = table.find('thead')
            if header_row:
                for th in header_row.find_all('th'):
                    header_text = th.get_text(strip=True)
                    if header_text:
                        headers.append(header_text)
            
            rows = []
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                if cells:
                    rows.append([cell.get_text(strip=True) for cell in cells])
            
            if headers and rows:
                max_cols = max(len(row) for row in rows)
                if len(headers) < max_cols:
                    headers.extend([f'Unnamed_{i}' for i in range(len(headers), max_cols)])
                return pd.DataFrame(rows, columns=headers[:max_cols])
        except Exception as e:
            print(f"Error parsing table: {e}")
        
        return pd.DataFrame()