from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from app.core.datetime_utils import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationship to entries
    entries = relationship("Entry", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
