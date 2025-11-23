from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TickSightings(Base):
    __tablename__ = 'tick_sightings'

    id = Column(String(255), primary_key=True)
    date = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    species = Column(String(100), nullable=False)
    latinName = Column(String(100), nullable=False)

DATABASE_URL = "sqlite:///ticks.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

