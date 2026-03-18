#!/usr/bin/env python3
"""Weather forecasting for the Journalist agent.

Fetches weather data from wttr.in and formats briefings for scheduled time slots.
Location is configured via $WEATHER_LOCATION environment variable.

Usage:
    python scripts/weather_forecast.py <6am|12pm|4pm|8pm|sunday_9pm>
"""
import json
import os
import sys
from datetime import datetime, timedelta

import requests

LOCATION = os.environ.get("WEATHER_LOCATION", "Stuttgart")
WTTR_TIMEOUT = 10


def get_weather():
    """Fetch weather data from wttr.in as JSON."""
    try:
        resp = requests.get(
            f"https://wttr.in/{LOCATION}?format=j1",
            headers={"User-Agent": "curl/8.0"},
            timeout=WTTR_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def format_current(data):
    """Extract current conditions from weather data."""
    current = data.get("current_condition", [{}])[0]
    return {
        "desc": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
        "temp": current.get("temp_C", "--"),
        "feels_like": current.get("FeelsLikeC", "--"),
        "humidity": current.get("humidity", "--"),
        "wind": current.get("windspeedKmph", "--"),
        "pressure": current.get("pressure", "--"),
        "visibility": current.get("visibility", "--"),
        "uv_index": current.get("UVIndex", "0"),
        "precip": current.get("precipMM", "0.0"),
    }


def format_forecast(data, focus_hours=None, title="Forecast"):
    """Format weather data into a readable briefing."""
    if not data:
        return "Weather unavailable"

    current = format_current(data)

    output = f"**{LOCATION} Weather: {title}**\n\n"
    output += f"**Now:** {current['desc']}, {current['temp']}C (feels {current['feels_like']}C)\n"
    output += f"Humidity: {current['humidity']}% | Wind: {current['wind']} km/h\n"
    output += f"Pressure: {current['pressure']} mb | Visibility: {current['visibility']} km\n"
    output += f"UV Index: {current['uv_index']} | Precipitation: {current['precip']} mm\n\n"

    if focus_hours:
        hourly = data.get("weather", [{}])[0].get("hourly", [])
        output += "**Hourly Forecast:**\n\n"
        output += "| Time | Weather | Temp | Feels | Humidity | Rain |\n"
        output += "|------|---------|------|-------|----------|------|\n"
        for h in hourly[:focus_hours]:
            time_val = h.get("time", "")
            desc = h.get("weatherDesc", [{}])[0].get("value", "")
            temp = h.get("tempC", "")
            feels = h.get("FeelsLikeC", "")
            hum = h.get("humidity", "")
            rain = h.get("chanceofrain", "0")
            output += f"| {time_val} | {desc[:15]} | {temp}C | {feels}C | {hum}% | {rain}% |\n"

    return output


TIME_SLOTS = {
    "6am": (12, "Full Day Ahead"),
    "12pm": (9, "Rest of Day"),
    "4pm": (5, "Rest of Day"),
    "8pm": (18, "Tonight + Tomorrow"),
    "sunday_9pm": (24, "7-Day Outlook"),
}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: weather_forecast.py <{'|'.join(TIME_SLOTS.keys())}>", file=sys.stderr)
        sys.exit(1)

    time_slot = sys.argv[1]

    if time_slot not in TIME_SLOTS:
        print(f"Unknown time slot: {time_slot}", file=sys.stderr)
        print(f"Valid slots: {', '.join(TIME_SLOTS.keys())}", file=sys.stderr)
        sys.exit(1)

    data = get_weather()
    hours, title = TIME_SLOTS[time_slot]

    if time_slot == "sunday_9pm":
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_label = f"{week_start.strftime('%b %d')}-{week_end.strftime('%b %d')}, {week_end.strftime('%Y')}"
        print(f"**Weekly Weather Lookahead**")
        print(f"*{LOCATION}: Week of {week_label}*\n")

    print(format_forecast(data, hours, title))


if __name__ == "__main__":
    main()
