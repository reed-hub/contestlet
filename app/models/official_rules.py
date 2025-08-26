from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base


class OfficialRules(Base):
    __tablename__ = "official_rules"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), unique=True, nullable=False)
    eligibility_text = Column(Text, nullable=False)
    sponsor_name = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    prize_value_usd = Column(Float, nullable=False)
    terms_url = Column(String)  # Optional URL to full terms and conditions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship back to contest
    contest = relationship("Contest", back_populates="official_rules")
