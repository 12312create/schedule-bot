import os
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

OWM_BASE_URL = "https://api.openweathermap.org/data/2.5"

class WeatherAPI:

    def __init__(self, api_key: str = None, city: str = "Almaty"):
        self.__api_key = api_key or os.getenv("WEATHER_API_KEY", "")
        self._city = city
        self._last_response: Optional[Dict] = None
        self._request_count: int = 0
        logger.info(f"WeatherAPI initialized for city: {self._city}")

    def __str__(self) -> str:
        return f"WeatherAPI(city={self._city}, requests={self._request_count})"

    @property
    def city(self) -> str:
        return self._city

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        if not self.__api_key:
            logger.warning("⚠️  Weather API key not set. Using demo data.")
            return None

        params["appid"] = self.__api_key
        params["units"] = "metric"
        params["lang"] = "ru"

        try:
            self._request_count += 1
            response = requests.get(
                f"{OWM_BASE_URL}/{endpoint}",
                params=params,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            self._last_response = data
            logger.debug(f"Weather API response: status={response.status_code}")
            return data

        except requests.exceptions.ConnectionError:
            logger.error("❌ Weather API: Connection error")
            return None
        except requests.exceptions.Timeout:
            logger.error("❌ Weather API: Request timed out")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Weather API HTTP error: {e}")
            return None
        except ValueError as e:
            logger.error(f"❌ Weather API JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Weather API unexpected error: {e}")
            return None
    def get_current_weather(self, city: str = None) -> Optional[Dict]:
        target_city = city or self._city
        data = self._make_request("weather", {"q": target_city})

        if data is None:
            return self._get_demo_weather(target_city)

        return self._parse_current_weather(data)
    def _parse_current_weather(self, data: Dict) -> Dict:
        try:
            return {
                "city": data.get("name", "Алматы"),
                "country": data.get("sys", {}).get("country", "KZ"),
                "temperature": round(data.get("main", {}).get("temp", 0)),
                "feels_like": round(data.get("main", {}).get("feels_like", 0)),
                "temp_min": round(data.get("main", {}).get("temp_min", 0)),
                "temp_max": round(data.get("main", {}).get("temp_max", 0)),
                "humidity": data.get("main", {}).get("humidity", 0),
                "pressure": data.get("main", {}).get("pressure", 1013),
                "wind_speed": round(data.get("wind", {}).get("speed", 0), 1),
                "wind_deg": data.get("wind", {}).get("deg", 0),
                "description": data.get("weather", [{}])[0].get("description", ""),
                "icon_code": data.get("weather", [{}])[0].get("icon", "01d"),
                "visibility": data.get("visibility", 10000),
                "clouds": data.get("clouds", {}).get("all", 0),
                "sunrise": data.get("sys", {}).get("sunrise"),
                "sunset": data.get("sys", {}).get("sunset"),
                "timestamp": datetime.now().isoformat(),
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Weather parse error: {e}")
            return self._get_demo_weather(self._city)
    def _get_demo_weather(self, city: str = "Алматы") -> Dict:
        return {
            "city": city,
            "country": "KZ",
            "temperature": 18,
            "feels_like": 16,
            "temp_min": 12,
            "temp_max": 22,
            "humidity": 45,
            "pressure": 1013,
            "wind_speed": 3.5,
            "wind_deg": 90,
            "description": "переменная облачность",
            "icon_code": "02d",
            "visibility": 10000,
            "clouds": 40,
            "sunrise": None,
            "sunset": None,
            "timestamp": datetime.now().isoformat(),
            "is_demo": True,
        }

    def format_weather_message(self, weather: Dict) -> str:
        if not weather:
            return "❌ Не удалось получить данные о погоде."
        temp = weather.get("temperature", 0)
        if temp >= 30:
            temp_emoji = "🔥"
        elif temp >= 20:
            temp_emoji = "☀️"
        elif temp >= 10:
            temp_emoji = "⛅"
        elif temp >= 0:
            temp_emoji = "🌧"
        else:
            temp_emoji = "❄️"
        wind_deg = weather.get("wind_deg", 0)
        wind_directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
        wind_dir = wind_directions[int((wind_deg + 22.5) / 45) % 8]

        is_demo = weather.get("is_demo", False)
        demo_note = "\n_(демо-данные, API ключ не настроен)_" if is_demo else ""

        return (
            f"🌤 *Погода в {weather['city']}, {weather['country']}*\n\n"
            f"{temp_emoji} Температура: *{weather['temperature']}°C*\n"
            f"🌡 Ощущается как: {weather['feels_like']}°C\n"
            f"💧 Влажность: {weather['humidity']}%\n"
            f"💨 Ветер: {weather['wind_speed']} м/с ({wind_dir})\n"
            f"🌥 Облачность: {weather['clouds']}%\n"
            f"📋 {weather['description'].capitalize()}"
            f"{demo_note}"
        )
    def get_weather_for_schedule(self, city: str = None) -> str:
        weather = self.get_current_weather(city)
        if not weather:
            return ""

        temp = weather.get("temperature", 0)
        desc = weather.get("description", "")
        return f"🌤 {temp}°C, {desc}"

_weather_instance: Optional[WeatherAPI] = None

def get_weather_api() -> WeatherAPI:
    global _weather_instance
    if _weather_instance is None:
        _weather_instance = WeatherAPI()
    return _weather_instance

if __name__ == "__main__":
    print("=== Weather API Demo ===")
    api = WeatherAPI()
    weather = api.get_current_weather("Almaty")
    print(api.format_weather_message(weather))
    print(f"\nWeather summary: {api.get_weather_for_schedule()}")