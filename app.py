import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

st.set_page_config(page_title="Weather Dashboard", layout="wide")

st.title("Weather Analytics Dashboard")
st.write("Visualizing real-time weather data from Neon PostgreSQL.")

def get_data():
    """Connects to Neon and fetches data."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL not set! Please check your environment variables.")
        return None
    
    engine = create_engine(db_url)
    query = "SELECT * FROM london_weather_metrics ORDER BY observation_time DESC LIMIT 50"
    return pd.read_sql(query, engine)

if st.button("Refresh Data"):
    data = get_data()
    if data is not None:
        st.success("Data fetched successfully!")
        
        # Display the raw table
        st.subheader("Raw Data Preview")
        st.dataframe(data)
        
        # Display the trend chart
        st.subheader("Temperature Trend (Celsius)")
        # Ensure observation_time is datetime for the chart
        data['observation_time'] = pd.to_datetime(data['observation_time'])
        chart_data = data.set_index('observation_time')['temperature_celsius']
        st.line_chart(chart_data)
    else:
        st.warning("Could not fetch data.")
else:
    st.info("Click 'Refresh Data' to load the latest metrics from your database.")