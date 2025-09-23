from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
from typing import Dict, Optional

from app.config import settings
from app.services.task_manager import TaskManager
from app.scraper.core import FBrefScraper
from app.exporter.excel_exporter import ExcelExporter

# Global task manager
task_manager = TaskManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FBref Scraper Web App...")
    yield
    # Cleanup
    print("Shutting down FBref Scraper Web App...")
    task_manager.cleanup()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/leagues")
async def get_supported_leagues():
    """Get list of supported leagues"""
    return {
        "leagues": [
            {"id": "9", "name": "Premier League"},
            {"id": "12", "name": "La Liga"},
            {"id": "11", "name": "Serie A"},
            {"id": "20", "name": "Bundesliga"},
            {"id": "13", "name": "Ligue 1"}
        ]
    }

@app.get("/api/fixtures")
async def get_fixtures(date: str, league: Optional[str] = None):
    """Get fixtures for a specific date and league"""
    try:
        scraper = FBrefScraper()
        fixtures = scraper.get_fixtures_by_date(date, league)
        return {"fixtures": fixtures, "date": date, "league": league}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-report")
async def generate_report(
    background_tasks: BackgroundTasks,
    match_url: str,
    match_id: str,
    format: str = "xlsx"
):
    """Start generating a report for a specific match"""
    task_id = str(uuid.uuid4())
    
    # Initialize task
    task_manager.create_task(task_id, {
        "match_url": match_url,
        "match_id": match_id,
        "format": format,
        "status": "initializing"
    })
    
    # Start background task
    background_tasks.add_task(generate_report_task, task_id, match_url, match_id, format)
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get progress of a report generation task"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@app.get("/api/download/{task_id}")
async def download_report(task_id: str):
    """Download generated report"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")
    
    if "file_path" not in task:
        raise HTTPException(status_code=500, detail="No file available")
    
    return StreamingResponse(
        open(task["file_path"], "rb"),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.xlsx"}
    )

async def generate_report_task(task_id: str, match_url: str, match_id: str, format: str):
    """Background task to generate report"""
    try:
        task_manager.update_task(task_id, {"status": "discovering_fixture", "progress": 10})
        
        scraper = FBrefScraper()
        exporter = ExcelExporter()
        
        # Scrape match data
        task_manager.update_task(task_id, {"status": "scraping_teams", "progress": 30})
        match_data = scraper.scrape_match_data(match_url)
        
        task_manager.update_task(task_id, {"status": "scraping_players", "progress": 60})
        player_data = scraper.scrape_player_data(match_data)
        
        # Generate report
        task_manager.update_task(task_id, {"status": "building_file", "progress": 80})
        file_path = exporter.export_match_report(match_data, player_data, task_id)
        
        task_manager.update_task(task_id, {
            "status": "completed", 
            "progress": 100,
            "file_path": file_path,
            "message": "Report generation complete"
        })
        
    except Exception as e:
        task_manager.update_task(task_id, {
            "status": "error",
            "progress": 100,
            "message": f"Error: {str(e)}"
        })