import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.models.forecast import DailyForecast, LocationForecast
from app.scrapers.utils import extract_icon_type, parse_date, parse_temperature


class ForecastScraper:
    """Scraper for SENAMHI weather forecasts."""
    def __init__(self):
        """Initialize scraper with configuration from settings."""
        self.base_url = settings.senamhi_forecast_url
        self.timeout = settings.request_timeout
        self.user_agent = settings.user_agent
    
    def _make_request(self) -> BeautifulSoup:
        """Fetch and parse SENAMHI forecast page."""
        headers = {
            "User-Agent": self.user_agent,
        }
        
        response = requests.get(
            self.base_url,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        return BeautifulSoup(response.content, "lxml")
    
    def _parse_forecast_row(self, row_div) -> DailyForecast:
        """Parse a single day forecast from HTML row."""
        cols = row_div.find_all("div", class_=re.compile(r"col-sm-\d+"))
        
        if len(cols) < 5:
            raise ValueError(f"Expected at least 5 columns, found {len(cols)}")
        
        date_text = cols[0].get_text(strip=True)
        date = parse_date(date_text)
        
        img_tag = cols[1].find("img")
        icon_url = img_tag["src"] if img_tag else ""
        weather_icon = extract_icon_type(icon_url)
        
        temp_max_text = cols[2].get_text(strip=True)
        temp_max = parse_temperature(temp_max_text)
        
        temp_min_text = cols[3].get_text(strip=True)
        temp_min = parse_temperature(temp_min_text)
        
        description = cols[4].get_text(strip=True)
        
        return DailyForecast(
            date=date,
            day_name=date_text.split(",")[0].strip(),
            temp_max=temp_max,
            temp_min=temp_min,
            weather_icon=weather_icon,
            description=description,
        )
    
    def _parse_location_cell(self, cell) -> LocationForecast:
        """Parse all forecasts for a single location from table cell."""
        name_span = cell.find("span", class_="nameCity")
        if not name_span:
            raise ValueError("Location name not found")
        
        full_name = name_span.get_text(strip=True)
        
        # Extract location and department
        match = re.match(r"([A-ZÁÉÍÓÚÑ\s]+)\s*-\s*([A-ZÁÉÍÓÚÑ\s]+)", full_name)
        if not match:
            raise ValueError(f"Cannot parse location from: {full_name}")
        
        location = match.group(1).strip()
        department = match.group(2).strip()
        
        forecast_rows = cell.find_all("div", class_="row m-3")
        
        daily_forecasts = []
        for row in forecast_rows:
            try:
                forecast = self._parse_forecast_row(row)
                daily_forecasts.append(forecast)
            except Exception as e:
                print(f"Warning: Failed to parse forecast row: {e}")
                continue
        
        return LocationForecast(
            location=location,
            department=department,
            full_name=full_name,
            forecasts=daily_forecasts,
        )
    
    def scrape_forecasts(self, departments: list[str] | None = None) -> list[LocationForecast]:
        """
        Scrape forecasts for specified departments.
        
        If departments is None, uses departments from settings.
        """
        if departments is None:
            departments = settings.get_departments_list()
        
        departments_upper = [d.upper() for d in departments]
        
        soup = self._make_request()
        
        table = soup.find("table")
        if not table:
            raise ValueError("Forecast table not found")
        
        rows = table.find_all("tr")
        
        forecasts = []
        
        for row in rows:
            cell = row.find("td")
            if not cell:
                continue
            
            name_span = cell.find("span", class_="nameCity")
            if not name_span:
                continue
            
            full_name = name_span.get_text(strip=True)
            
            # Check if location belongs to any of the specified departments
            matches_department = False
            for dept in departments_upper:
                if f"- {dept}" in full_name.upper():
                    matches_department = True
                    break
            
            if not matches_department:
                continue
            
            try:
                location_forecast = self._parse_location_cell(cell)
                forecasts.append(location_forecast)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error parsing {full_name}: {e}")
                continue
        
        return forecasts