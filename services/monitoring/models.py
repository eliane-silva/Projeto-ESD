from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True)
    platform = Column(String)
    status = Column(String)
    content_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    platform = Column(String)
    type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)