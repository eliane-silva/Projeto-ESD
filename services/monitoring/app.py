from fastapi import FastAPI
from database import SessionLocal, engine
from models import Base, Action, Event

app = FastAPI(title="Monitoring Service")

Base.metadata.create_all(bind=engine)


@app.post("/action")
def register_action(platform: str, status: str, content_id: str):
    db = SessionLocal()
    action = Action(platform=platform, status=status, content_id=content_id)
    db.add(action)
    db.commit()
    db.close()
    return {"ok": True}