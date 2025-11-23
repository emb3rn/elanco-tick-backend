# elanco-tick-backend
A backend API using **FastAPI** that allows users to view sightings, statistics, machine learning insights and risk factors about tick sightings in their area. By Oskar Durys

# Elanco Tick Sightings Backend MVP

## Overview
This is my project Minimum Viable Product (MVP) that allows potential users to view tick sightings, statistics, machine learning insights (through a linear regression model), and query about the risk factor for their pet depending on multiple factors. This is done through multiple routes using FastAPI and SQLAlchemy, as detailed below.

## Key Features
* **Data Ingestion Pipeline:** Automated ETL process to clean and import raw Excel data into a structured SQLite database.
* **Search & Filtering:** Dynamic API endpoints allowing users to filter sightings by date range, location, and species. Filters are consistent across all endpoints.
* **Statistical Analysis:** Aggregated insights including weekly/monthly trends and historical comparisons.
* **Predictive Analytics (ML Extension):** A Linear Regression model that analyzes historical trends to forecast tick activity for the upcoming week by default, or by the desired length of time.
* **Risk Assessment Tool:** An algorithm that calculates a customized risk score for pets based on lifestyle, coat type, and region. Important as users realistically just want to know the effect and risks on their pets.

## Technology Stack
| Component | Technology | Reason for Choice |
| :--- | :--- | :--- |
| **Language** | Python 3.9+ | Experience and familiarity, along with robust library ecosystem for both API development and data manipulation. |
| **Framework** | FastAPI | Very high performance and easy to use modern web framework with automatic Swagger UI documentation. Avoids human documentation mistakes and helps agile development. |
| **Database** | SQLite + SQLAlchemy | Lightweight, serverless database ideal for MVPs, accessed via a powerful ORM. |
| **Data Processing** | Pandas | Industry standard for efficient data cleaning, manipulation, and time-series aggregation. |
| **Machine Learning** | Scikit-Learn | Easy to use library for implementing the Linear Regression prediction model. |

## Project Structure
* `main.py`: The entry point for the FastAPI application, containing all route logic and endpoints.
* `models.py`: Defines the database schema using SQLAlchemy ORM.
* `response_schemas.py`: Pydantic definitions for the JSend-compliant JSON responses.
* `xlsx_importer.py`: A utility script to Extract, Transform, and Load (ETL) data from the raw Excel file into the database.
* `requirements.txt`: List of project dependencies.

## Installation & Setup

### 1. Prerequisites
Check you have Python installed on your system.
```bash
python --version
````

### 2\. Clone the Repository

```bash
git clone https://github.com/emb3rn/elanco-tick-backend.git
cd elanco-tick-backend
```

### 3\. Install Dependencies

You can use a virtual environment, but it is not necessary for the code to function.

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
# Activate it (Windows)
venv\Scripts\activate
# Activate it (Mac/Linux)
source venv/bin/activate
```

```bash
# Install packages
pip install -r requirements.txt
```

### 4\. Database Setup (Import Data)

Before running the server, you must ingest the data. This script takes a file name as a system argument and creates the database, then populates it with the provided dataset.

```bash
python xlsx_importer.py <your_xlsx_file.xlsx>
```

### 5\. Run the Server

Use `uvicorn` to run the app:

```bash
uvicorn main:app --reload
```

Alternatively, with newer versions of `fastapi` you can also use:

```bash
fastapi run main.py
```

## API Documentation

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### API Response Format (JSend)

All endpoints return a standardized JSON response following the **JSend** specification. This ensures consistent error handling and data structure for the frontend.

**Standard Response Structure:**

```json
{
  "status": "success",  // "success" or "error"
  "message": null,      // Error details or informational messages (if any)
  "results": 1,         // Count of items found
  "data": { ... }       // The requested payload (List or Object)
}
```

### Key Endpoints

All of these endpoints have optional filters by location, start/end date, tick species.

  * `GET /api/sightings/`: Retrieve raw sighting data with optional filters (Date, Species, Location).
  * `GET /api/statistics/`: Get aggregated stats (Total count, Average per week, etc.).
  * `GET /api/predictions/`: Get a 7-day forecast of tick activity based on linear regression.
  * `GET /api/riskfactor/`: Calculate risk score for a specific pet profile.

For example you can find the sightings in Manchester through:

`http://localhost:8000/api/sightings/?location=Manchester`

## Future Improvements

  * **Geospatial Visualization:** Integrate GeoJSON to plot sightings on an interactive map.
  * **Advanced ML Models:** Implement seasonal decomposition to better handle annual tick cycles (e.g., Spring spikes).
  * **Authentication:** Add API Key or OAuth2 security for write access.
  * **PUT Routes to API:** Allow properly authenticated users (e.g Vets) to append sightings to the database, allows users to collaborate and expand the amount of data.
  * **Outbreak Detectors:** Using standard deviation, detect when sightings in a day have spiked compared to the daily average, or the predicted amount through `api/predictions` indicating an outbreak.
