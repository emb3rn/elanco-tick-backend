import pandas as pd
import sys
from models import TickSightings, engine

if len(sys.argv) < 2:
    print("Error: Please provide the Excel filename.")
    print("Usage: python xlsx_importer.py <filename.xlsx>")
    sys.exit(1)

file_name = sys.argv[1]

try:
    df = pd.read_excel(file_name)
    
    # clean data: drop rows with missing required fields and convert date column
    df = df.dropna(subset=['date', 'location', 'species', 'latinName'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # save to database
    df.to_sql('tick_sightings', con=engine, if_exists='append', index=False)

    print(f"Successfully imported data from '{file_name}' into the database.")

except FileNotFoundError:
    print(f"Error: The file '{file_name}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")