from datetime import datetime
from pydantic import BaseModel
from typing import Generic, List, TypeVar, Optional

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    status: str = "success"
    message: Optional[str] = None
    results: Optional[int] = None
    data: Optional[T]

class TickSightingsResponse(BaseModel):
    id : str
    date: datetime
    location: str
    species: str
    latinName: str

    class Config:
        from_attributes = True

class StatisticsResponse(BaseModel):
    total_sightings: int
    oldest_sighting: datetime
    newest_sighting: datetime
    average_monthly_sightings: float
    average_weekly_sightings: float
    sightings_past_year: int

class PredictionResponse(BaseModel):
    predicted_total_sightings: float
    daily_predictions: List[float]
    average_daily: float

class RiskResponse(BaseModel):
    risk_factor: float
    risk_label: str
    risk_info: str