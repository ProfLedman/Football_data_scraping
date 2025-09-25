from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from pydantic import BaseModel
import uuid
import os
from typing import Dict, Optional

from app.config import settings
from app.services.task_manager import TaskManager
from app.scraper.core import FBrefScraper
from app.exporter.excel_exporter import ExcelExporter

# Pydantic model for generate-report request
class GenerateReportRequest(BaseModel):
    match_url: str
    match_id: str
    format: str = "xlsx"

# Global task manager
task_manager = TaskManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FBref Scraper Web App...")
    # Ensure data directory exists
    os.makedirs("data/exports", exist_ok=True)
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
    request: GenerateReportRequest
):
    """Start generating a report for a specific match"""
    task_id = str(uuid.uuid4())
    
    # Initialize task
    task_manager.create_task(task_id, {
        "match_url": request.match_url,
        "match_id": request.match_id,
        "format": request.format,
        "status": "initializing",
        "progress": 0,
        "message": "Starting report generation..."
    })
    
    # Start background task
    background_tasks.add_task(
        generate_report_task, 
        task_id, 
        request.match_url, 
        request.match_id, 
        request.format
    )
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get progress of a report generation task"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task.get("status", "unknown"),
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "match_url": task.get("match_url"),
        "match_id": task.get("match_id")
    }

@app.get("/api/download/{task_id}")
async def download_report(task_id: str):
    """Download generated report"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")
    
    if "file_path" not in task or not os.path.exists(task["file_path"]):
        raise HTTPException(status_code=500, detail="Report file not found")
    
    # Generate a better filename
    filename = f"fbref_report_{task_id}.xlsx"
    if "match_id" in task:
        filename = f"fbref_report_{task['match_id']}.xlsx"
    
    return StreamingResponse(
        open(task["file_path"], "rb"),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

async def generate_report_task(task_id: str, match_url: str, match_id: str, format: str):
    """Background task to generate report - FIXTURES ONLY VERSION"""
    try:
        task_manager.update_task(task_id, {
            "status": "discovering_fixture", 
            "progress": 20,
            "message": "Discovering fixture details..."
        })
        
        scraper = FBrefScraper()
        exporter = ExcelExporter()
        
        # Scrape match data ONLY (no player data)
        task_manager.update_task(task_id, {
            "status": "scraping_teams", 
            "progress": 60,
            "message": "Scraping team statistics..."
        })
        match_data = scraper.scrape_match_data(match_url)
        
        # SKIP PLAYER DATA COLLECTION FOR NOW
        task_manager.update_task(task_id, {
            "status": "building_file", 
            "progress": 80,
            "message": "Building Excel file with fixture data..."
        })
        
        # Pass empty dict for player_data
        file_path = exporter.export_match_report(match_data, {}, task_id)
        
        task_manager.update_task(task_id, {
            "status": "completed", 
            "progress": 100,
            "file_path": file_path,
            "message": "Fixture report generation complete"
        })
        
    except Exception as e:
        error_message = f"Error generating report: {str(e)}"
        print(error_message)
        task_manager.update_task(task_id, {
            "status": "error",
            "progress": 100,
            "message": error_message
        })

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FBref Scraper"}

@app.get("/api/debug/fixtures")
async def debug_fixtures(date: str, league: Optional[str] = None):
    """Debug endpoint to see raw fixture data"""
    scraper = FBrefScraper()
    fixtures = scraper.get_fixtures_by_date(date, league)
    return {"fixtures": fixtures}

# Test endpoint to verify parsing logic
@app.get("/api/test-parsing")
async def test_parsing():
    """Test endpoint to verify fixture parsing works"""
    from app.scraper.fixtures import FixtureScraper
    scraper = FixtureScraper()
    result = scraper.test_specific_fixture_parsing()
    return {"test_result": result}