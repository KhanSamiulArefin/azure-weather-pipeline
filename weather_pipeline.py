import requests
import json
import os
import pandas as pd
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine

def fetch_weather_data():
    """Fetches live weather data from the Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=51.5085&longitude=-0.1257&current_weather=true"
    print("Fetching data from API...")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def upload_to_azure(weather_data):
    """Uploads the raw JSON data to Azure Blob Storage (Bronze Layer)."""
    connection_string = os.getenv("AZURE_CONNECTION_STRING")
    container_name = "raw-data"
    
    if not connection_string:
         raise ValueError("AZURE_CONNECTION_STRING environment variable not found!")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"london_weather_{timestamp}.json"
    
    with open(file_name, "w") as f:
        json.dump(weather_data, f)
        
    print(f"Uploading {file_name} to Azure...")
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    
    with open(file_name, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print("Success! Raw JSON uploaded to Data Lake.")

def transform_and_load_to_sql(weather_data):
    """Transforms JSON to a structured format and loads into PostgreSQL (Silver Layer)."""
    print("Transforming data for SQL...")
    
    # Extract only the specific metrics we care about
    current = weather_data['current_weather']
    clean_data = [{
        'observation_time': current['time'],
        'temperature_celsius': current['temperature'],
        'windspeed_kmh': current['windspeed'],
        'is_day': current['is_day']
    }]
    
    # Convert to a Pandas DataFrame (a structured table)
    df = pd.DataFrame(clean_data)
    
    # Connect to PostgreSQL using the secret URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not found!")
        
    engine = create_engine(db_url)
    
    # Send the table to the SQL database!
    print("Loading data into PostgreSQL Database...")
    df.to_sql('london_weather_metrics', con=engine, if_exists='append', index=False)
    print("Success! Clean data loaded to SQL Data Warehouse.")

if __name__ == "__main__":
    try:
        # Step 1: Extract
        data = fetch_weather_data()
        
        # Step 2: Load to Data Lake (Bronze)
        upload_to_azure(data)
        
        # Step 3: Transform and Load to Database (Silver)
        transform_and_load_to_sql(data)
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
