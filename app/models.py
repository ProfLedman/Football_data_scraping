from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class Fixture(BaseModel):
    league: str
    date: str
    time: str
    home_team: str
    away_team: str
    score: str
    home_team_url: Optional[str] = None
    away_team_url: Optional[str] = None
    match_url: Optional[str] = None
    match_id: str

class MatchData(BaseModel):
    match_info: Dict[str, Any]
    home_team: Dict[str, Any]
    away_team: Dict[str, Any]
    players: List[Dict[str, Any]]

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None