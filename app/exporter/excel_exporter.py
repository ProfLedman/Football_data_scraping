import pandas as pd
import os
from datetime import datetime
from typing import Dict
from urllib.parse import urljoin

class ExcelExporter:
    def __init__(self, output_dir: str = None):
        from app.config import settings
        self.output_dir = output_dir or settings.EXPORT_OUTPUT_DIR
        self.base_url = "https://fbref.com"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_match_report(self, match_data: Dict, player_data: Dict, task_id: str) -> str:
        """Export match report to Excel - FOCUSED ON FIXTURES ONLY (no player data)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fbref_fixtures_report_{task_id}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            self._add_metadata_sheet(writer, match_data, task_id)
            self._add_team_sheets(writer, match_data)
            # Skip player sheets for now - focus on fixtures only
            # self._add_player_sheets(writer, player_data)
        
        return filepath
    
    def _add_metadata_sheet(self, writer, match_data: Dict, task_id: str):
        """Add metadata sheet with match information"""
        # Get match info, handling nested structures
        match_info = match_data.get('match_info', {})
        match_url = match_info.get('url', '')
        
        # Ensure proper URL formation
        if match_url and not match_url.startswith(('http://', 'https://')):
            match_url = urljoin(self.base_url, match_url.lstrip('/'))
        
        # Extract team names from the correct location in match_data
        home_team = match_data.get('home_team', {}).get('name') or match_info.get('home_team', 'Unknown')
        away_team = match_data.get('away_team', {}).get('name') or match_info.get('away_team', 'Unknown')
        
        metadata = {
            'Generated': datetime.now().isoformat(),
            'Task ID': task_id,
            'Match URL': match_url,
            'Match ID': match_info.get('match_id', 'Unknown'),
            'Home Team': home_team,
            'Away Team': away_team,
            'Data Type': 'Fixtures Only (Player data disabled)',
            'Sheets Included': 'Metadata, Home Team Tables, Away Team Tables'
        }
        
        df = pd.DataFrame(list(metadata.items()), columns=['Key', 'Value'])
        df.to_excel(writer, sheet_name='Metadata', index=False)
    
    def _add_team_sheets(self, writer, match_data: Dict):
        """Add team data sheets - handle the actual scraper output structure"""
        # Home team data (from scraper's actual structure)
        home_team_data = match_data.get('home_team', {})
        for sheet_name, data in home_team_data.items():
            safe_name = self._sanitize_sheet_name(f"Home_{sheet_name}")
            if data and len(data) > 0:
                # Convert list of records to DataFrame
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=safe_name, index=False)
        
        # Away team data  
        away_team_data = match_data.get('away_team', {})
        for sheet_name, data in away_team_data.items():
            safe_name = self._sanitize_sheet_name(f"Away_{sheet_name}")
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=safe_name, index=False)
    
    def _sanitize_sheet_name(self, name: str) -> str:
        """Ensure sheet name is valid for Excel (max 31 chars, no invalid chars)"""
        # Remove invalid characters
        safe_name = "".join(c for c in name if c.isalnum() or c in ('_', ' ', '-'))
        # Truncate to 31 characters
        return safe_name[:31]