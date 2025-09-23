import pandas as pd
import os
from datetime import datetime
from typing import Dict

class ExcelExporter:
    def __init__(self, output_dir: str = None):
        from app.config import settings
        self.output_dir = output_dir or settings.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_match_report(self, match_data: Dict, player_data: Dict, task_id: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fbref_report_{task_id}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            self._add_metadata_sheet(writer, match_data, task_id)
            self._add_team_sheets(writer, match_data)
            self._add_player_sheets(writer, player_data)
        
        return filepath
    
    def _add_metadata_sheet(self, writer, match_data: Dict, task_id: str):
        metadata = {
            'Generated': datetime.now().isoformat(),
            'Task ID': task_id,
            'Match URL': match_data.get('match_info', {}).get('url', 'Unknown'),
        }
        df = pd.DataFrame(list(metadata.items()), columns=['Key', 'Value'])
        df.to_excel(writer, sheet_name='Metadata', index=False)
    
    def _add_team_sheets(self, writer, match_data: Dict):
        for sheet_name, data in match_data.get('home_team', {}).items():
            safe_name = f"Home_{sheet_name}"[:31]
            pd.DataFrame(data).to_excel(writer, sheet_name=safe_name, index=False)
        
        for sheet_name, data in match_data.get('away_team', {}).items():
            safe_name = f"Away_{sheet_name}"[:31]
            pd.DataFrame(data).to_excel(writer, sheet_name=safe_name, index=False)
    
    def _add_player_sheets(self, writer, player_data: Dict):
        for player_id, player_info in player_data.items():
            player_name = player_info['info'].get('name', f'Player_{player_id}')
            for sheet_name, data in player_info.get('data', {}).items():
                safe_name = f"Player_{player_name}_{sheet_name}"[:31]
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in ('_', ' '))
                pd.DataFrame(data).to_excel(writer, sheet_name=safe_name, index=False)