import openmeteo_requests
from datetime import datetime, timedelta
openmeteo = openmeteo_requests.Client()


def fetch_weather(lat, lon, date_start, unit):
    start = datetime.fromisoformat(date_start)
    end = start + timedelta(days=1)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "UTC",
        "temperature_unit": unit,
        "daily": "temperature_2m_max,precipitation_sum",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
    }
    response = openmeteo.weather_api(url, params=params)[0]
    daily = response.Daily()
    return {
        "date": start.strftime("%Y-%m-%d"),
        "temperature_max": float(daily.Variables(0).ValuesAsNumpy()[0]),
        "precipitation_sum": float(daily.Variables(1).ValuesAsNumpy()[0]),
    }
