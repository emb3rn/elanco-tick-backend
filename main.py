from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session, sessionmaker
from models import TickSightings, engine
from datetime import datetime, timedelta
from typing import List, Literal, Optional, cast
from sklearn.linear_model import LinearRegression
from response_schemas import PredictionResponse, RiskResponse, StatisticsResponse, TickSightingsResponse, StandardResponse
import numpy as np
import pandas as pd

app = FastAPI()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def filter_query(
    query, 
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    species: Optional[str],
    location: Optional[str]
):
    if start_date:
        query = query.filter(TickSightings.date >= start_date)
    if end_date:
        query = query.filter(TickSightings.date <= end_date)
    if species:
        query = query.filter(TickSightings.species == species)
    if location:
        query = query.filter(TickSightings.location == location)
    return query

def predict(dataframe, days_ahead):
    # group data by the same date to get daily counts
    daily_counts = dataframe.groupby(dataframe['date'].dt.date).size().reset_index(name='daily_count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])

    # assign day numbers for X axis 
    min_date = daily_counts['date'].min()
    daily_counts['day_number'] = (daily_counts['date'] - min_date).dt.days

    X = daily_counts[['day_number']]
    y = daily_counts['daily_count']

    model = LinearRegression()
    model.fit(X, y)

    last_day_num = daily_counts['day_number'].max()
    days_to_predict = np.arange(last_day_num + 1, last_day_num + days_ahead + 1).reshape(-1, 1)
    
    predictions = model.predict(days_to_predict)

    predictions = np.maximum(predictions, 0) # ensure at least 0 in case trending downwards to avoid negative sightings

    return predictions

@app.get("/api/sightings/", response_model=StandardResponse[List[TickSightingsResponse]])
def get_sightings(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering sightings"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering sightings"),
    species: Optional[str] = Query(None, description="Species name for filtering sightings"),
    location: Optional[str] = Query(None, description="Region for filtering sightings"),
    db: Session = Depends(get_db)
):
    query = db.query(TickSightings)
    
    if query.first() is None:
        raise HTTPException(status_code=404, detail="No data in database. Please import data first.")

    query = filter_query(query, start_date, end_date, species, location)
    results = query.all()
    
    if not results:
        return StandardResponse(
            status="success",
            message="No results found for the given filters.",
            results=0,
            data=[]
        )
    
    return StandardResponse(
        results=len(results),
        data=results
    )

@app.get("/api/statistics/", response_model=StandardResponse[StatisticsResponse])
def get_statistics(
    location: Optional[str] = Query(None, description="Region for filtering statistics"),
    species: Optional[str] = Query(None, description="Species name for filtering statistics"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering statistics"),
    db: Session = Depends(get_db),
):
    query = db.query(TickSightings)

    if query.first() is None:
        raise HTTPException(status_code=404, detail="No data in database. Please import data first.")

    query = filter_query(query, start_date, end_date, species, location)

    # order by date
    results = query.order_by(TickSightings.date).all()

    if not results:
        return StandardResponse(
            status="success",
            message="No results found for the given filters.",
            results=0,
            data=None
        )
    
    total_months = ((results[-1].date.year - results[0].date.year) * 12) + results[-1].date.month - results[0].date.month + 1
    total_weeks = ((results[-1].date - results[0].date).days) / 7
    sightings_past_year = query.filter(TickSightings.date >= datetime.now() - timedelta(days=365)).count()

    stats_data = StatisticsResponse(
        total_sightings=len(results),
        oldest_sighting=cast(datetime, results[0].date),
        newest_sighting=cast(datetime, results[-1].date),
        average_monthly_sightings=round(len(results) / total_months if total_months > 0 else 0, 1),
        average_weekly_sightings=round(len(results) / total_weeks if total_weeks > 0 else 0, 1),
        sightings_past_year=sightings_past_year
    )

    return StandardResponse(
        results=1,
        data=stats_data
    )

@app.get("/api/predictions/", response_model=StandardResponse[PredictionResponse])
def predict_next_days(
    days: int = Query(7, le=365, description="Amount of days ahead to predict. Defaults to one week. Maximum is 365 days."),
    location: Optional[str] = Query(None, description="Region for filtering predictions"),
    species: Optional[str] = Query(None, description="Species name for filtering predictions"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering predictions"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering predictions"),
    db: Session = Depends(get_db)
):
    query = db.query(TickSightings.date)
    query = filter_query(query, start_date, end_date, species, location)
    results = query.all()

    if len(results) == 0:
        raise HTTPException(status_code=404, detail="No sightings found for the given filters to base predictions on.")
    
    df = pd.DataFrame([r.date for r in results], columns=['date']) #dataframe for easy grouping and linear model input
    prediction = predict(df, days)

    pred_data = PredictionResponse(
        predicted_total_sightings=round(prediction.sum(), 3),
        daily_predictions=[round(float(count), 3) for count in prediction.flatten()],
        average_daily=round(float(prediction.mean()), 3)
    )

    return StandardResponse(
        results=1,
        data=pred_data
    )

@app.get("/api/riskfactor/", response_model=StandardResponse[RiskResponse])
def get_risk_factor(
    lifestyle: Literal["indoor", "outdoor", "mixed"] = Query(None, description="Lifestyle for risk factor calculation"),
    coat: Literal["short", "medium", "long"] = Query(None, description="Coat type for risk factor calculation"),
    region_type: Literal["urban", "suburban", "rural"] = Query(None, description="Region type for risk factor calculation"),
):
    lifestyle_scores = {"indoor": 0.1, "mixed": 0.6, "outdoor": 1 }
    coat_scores = { "short": 0.1, "medium": 0.5, "long": 1 }
    region_scores = { "urban": 0.1, "suburban": 0.5, "rural": 1 }

    lifestyle_score = lifestyle_scores.get(lifestyle, 0)
    coat_score = coat_scores.get(coat, 0)
    region_score = region_scores.get(region_type, 0)

    # adds up to max 10/10 risk score
    risk_factor = (lifestyle_score * 5) + (coat_score * 3) + (region_score * 2)

    if lifestyle_score == 0 or coat_score == 0 or region_score == 0:
        raise HTTPException(status_code=400, detail="All parameters (lifestyle, coat, region_type) must be provided for risk factor calculation.")
    
    risk_info = (
        "Low risk: Standard tick prevention measures recommended." if risk_factor < 4 else
        "Medium risk: Enhanced tick prevention measures recommended." if risk_factor < 7 else
        "High risk: Consult a veterinarian for comprehensive tick prevention."
    )

    risk_data = RiskResponse(
        risk_factor=round(risk_factor, 2),
        risk_label=(
            "LOW" if risk_factor < 4 else
            "MEDIUM" if risk_factor < 7 else
            "HIGH"
        ),
        risk_info=risk_info  
    )

    return StandardResponse(
        results=1,
        data=risk_data
    )

@app.get("/", include_in_schema=False)
def read_root():
    return {
        "message": "TickSightings API",
        "docs": "/docs",
        "endpoints": [
            "/api/sightings/",
            "/api/statistics/",
            "/api/predictions/",
            "/api/riskfactor/"
        ]
    }

# for debug delete later
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
