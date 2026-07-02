import requests
import json
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient

def fetch_weather_data():
    """Fetches live weather data from the Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=51.5085&longitude=-0.1257&current_weather=true"
    print("Fetching data from API...")
    response = requests.get(url)
    response.raise_for_status() # This will raise an error if the API fails
    return response.json()

def upload_to_azure(weather_data):
    """Uploads the weather JSON data to Azure Blob Storage."""
    # We grab the connection string securely from the environment
    connection_string = os.getenv("AZURE_CONNECTION_STRING")
    container_name = "raw-data"
    
    if not connection_string:
         raise ValueError("AZURE_CONNECTION_STRING environment variable not found!")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"london_weather_{timestamp}.json"
    
    # Save locally first
    with open(file_name, "w") as f:
        json.dump(weather_data, f)
        
    print(f"Uploading {file_name} to Azure...")
    
    # Connect and upload
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    
    with open(file_name, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
        
    print("Success! File uploaded to Data Lake.")

if __name__ == "__main__":
    try:
        data = fetch_weather_data()
        upload_to_azure(data)
    except Exception as e:
        print(f"Pipeline failed: {e}")
