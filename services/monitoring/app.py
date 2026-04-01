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


@app.post("/event")
def register_event(platform: str, type: str):
    db = SessionLocal()
    event = Event(platform=platform, type=type)
    db.add(event)
    db.commit()
    db.close()
    return {"ok": True}

@app.get("/metrics/{platform}")
def get_metrics(platform: str):
    db = SessionLocal()

    total = db.query(Action).filter(Action.platform == platform).count()

    success = db.query(Action).filter(
        Action.platform == platform,
        Action.status == "success"
    ).count()

    errors = db.query(Action).filter(
        Action.platform == platform,
        Action.status == "error"
    ).count()

    blocked = db.query(Action).filter(
        Action.platform == platform,
        Action.status == "blocked"
    ).count()

    db.close()

    return {
        "platform": platform,
        "total": total,
        "success": success,
        "errors": errors,
        "blocked": blocked,
        "success_rate": success / total if total > 0 else 0,
        "error_rate": errors / total if total > 0 else 0,
        "block_rate": blocked / total if total > 0 else 0
    }