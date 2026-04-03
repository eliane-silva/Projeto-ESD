from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
from models import Base, Action, Event
from config import settings

app = FastAPI(title="Monitoring Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(bind=engine)


@app.post(settings.monitoring_action)
def register_action(platform: str, status: str, content_id: str):
    db = SessionLocal()
    action = Action(platform=platform, status=status, content_id=content_id)
    db.add(action)
    db.commit()
    db.close()
    return {"ok": True}


@app.post(settings.monitoring_event)
def register_event(platform: str, type: str):
    db = SessionLocal()
    event = Event(platform=platform, type=type)
    db.add(event)
    db.commit()
    db.close()
    return {"ok": True}

@app.get(settings.monitoring_metrics)
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

    block_events = db.query(Event).filter(
        Event.platform == platform,
        Event.type == "BLOCK"
    ).count()

    rate_increase = db.query(Event).filter(
        Event.platform == platform,
        Event.type == "RATE_INCREASE"
    ).count()

    rate_decrease = db.query(Event).filter(
        Event.platform == platform,
        Event.type == "RATE_DECREASE"
    ).count()

    db.close()

    return {
        "platform": platform,

        # actions
        "total": total,
        "success": success,
        "errors": errors,
        "blocked": blocked,

        # rates
        "success_rate": success / total if total > 0 else 0,
        "error_rate": errors / total if total > 0 else 0,
        "block_rate": blocked / total if total > 0 else 0,

        # events
        "events": {
            "block_events": block_events,
            "rate_increase": rate_increase,
            "rate_decrease": rate_decrease
        }
    }