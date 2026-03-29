from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database.db import SessionLocal
from database.models import TelegramEntity, BackupMapping
import os

app = FastAPI(title="Ame Bot Dashboard")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db=Depends(get_db)):
    total_entities = db.query(TelegramEntity).count()
    groups = db.query(TelegramEntity).filter_by(entity_type="group").count()
    channels = db.query(TelegramEntity).filter_by(entity_type="channel").count()
    active_backups = db.query(BackupMapping).filter_by(enabled=True).count()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "total_entities": total_entities,
        "groups": groups,
        "channels": channels,
        "active_backups": active_backups
    })

@app.get("/entities", response_class=HTMLResponse)
async def entities_view(request: Request, db=Depends(get_db)):
    entities = db.query(TelegramEntity).order_by(TelegramEntity.title).all()
    return templates.TemplateResponse("entities.html", {"request": request, "entities": entities})

@app.get("/backups", response_class=HTMLResponse)
async def backups_view(request: Request, db=Depends(get_db)):
    backups = db.query(BackupMapping).order_by(BackupMapping.enabled.desc()).all()
    
    # Obtener entidades que son grupos o canales para el formulario de nuevo backup
    available_entities = db.query(TelegramEntity).filter(
        TelegramEntity.entity_type.in_(['group', 'channel'])
    ).order_by(TelegramEntity.title).all()
    
    return templates.TemplateResponse("backups.html", {
        "request": request, 
        "backups": backups,
        "available_entities": available_entities
    })

@app.post("/backups/toggle/{backup_id}")
async def toggle_backup(backup_id: int, request: Request, db=Depends(get_db)):
    backup = db.query(BackupMapping).filter_by(id=backup_id).first()
    if backup:
        backup.enabled = not backup.enabled
        db.commit()
    return RedirectResponse(url="/backups", status_code=303)

@app.post("/backups/create")
async def create_backup(source_chat_id: int = Form(...), db=Depends(get_db)):
    entity = db.query(TelegramEntity).filter_by(telegram_id=source_chat_id).first()
    if entity:
        existing = db.query(BackupMapping).filter_by(source_chat_id=source_chat_id).first()
        if existing:
            existing.enabled = True
        else:
            new_mapping = BackupMapping(
                source_chat_id=source_chat_id,
                dest_chat_id=0,
                dest_chat_title=f"⏳ Pendiente: {entity.title}",
                enabled=True
            )
            db.add(new_mapping)
        db.commit()
    return RedirectResponse(url="/backups", status_code=303)
