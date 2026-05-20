import os
import csv
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

SCRAPING_OUTPUT_DIR = Path(__file__).parent / "output"

class IITUScraper:
    BASE_URL = "https://iitu.edu.kz"
    NEWS_URL = "https://iitu.edu.kz/news/"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self, timeout: int = 15):
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(self.HEADERS)
        self._scraped_data: List[Dict] = []
        SCRAPING_OUTPUT_DIR.mkdir(exist_ok=True)
        logger.info("IITUScraper initialized")

    def __str__(self) -> str:
        return f"IITUScraper(items={len(self._scraped_data)})"
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            logger.info(f"Fetching: {url}")
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "lxml")
            logger.info(f"✅ Page fetched: {url} ({len(response.text)} chars)")
            return soup

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error: {url}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {url}: {e}")
            return None
    def scrape_news(self, max_items: int = 10) -> List[Dict]:
        soup = self._fetch_page(self.NEWS_URL)

        if soup is None:
            logger.warning("⚠️  Could not fetch IITU news, returning demo data")
            return self._get_demo_news()

        news_items = []

        try:
            selectors = [
                "article.post",
                ".news-item",
                ".post-item",
                "div.entry",
                "div.news",
            ]

            articles = []
            for selector in selectors:
                articles = soup.select(selector)
                if articles:
                    logger.info(f"Found {len(articles)} items with selector: {selector}")
                    break

            if not articles:
                articles = soup.find_all(["article", "div"], class_=lambda c: c and "post" in c.lower())

            for article in articles[:max_items]:
                item = self._parse_news_item(article)
                if item:
                    news_items.append(item)

        except Exception as e:
            logger.error(f"Error parsing news: {e}")

        if not news_items:
            logger.warning("No news found, returning demo data")
            return self._get_demo_news()

        self._scraped_data = news_items
        logger.info(f"✅ Scraped {len(news_items)} news items")
        return news_items
    def _parse_news_item(self, article) -> Optional[Dict]:
        """Извлечь данные одной новости из HTML-элемента."""
        try:
            title_tag = (
                    article.find("h2") or
                    article.find("h3") or
                    article.find(class_=lambda c: c and "title" in str(c).lower())
            )
            title = title_tag.get_text(strip=True) if title_tag else "Без заголовка"

            link_tag = article.find("a", href=True)
            link = link_tag["href"] if link_tag else ""
            if link and not link.startswith("http"):
                link = self.BASE_URL + link

            date_tag = article.find("time") or article.find(class_=lambda c: c and "date" in str(c).lower())
            pub_date = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime("%d.%m.%Y")

            desc_tag = article.find("p") or article.find(class_=lambda c: c and "excerpt" in str(c).lower())
            description = desc_tag.get_text(strip=True)[:200] if desc_tag else ""

            if not title or title == "Без заголовка":
                return None

            return {
                "title": title,
                "link": link,
                "date": pub_date,
                "description": description,
                "source": "IITU Official",
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"Failed to parse news item: {e}")
            return None

    def _get_demo_news(self) -> List[Dict]:
        return [
            {
                "title": "Открытие нового IT-лаборатории в IITU",
                "link": "https://iitu.edu.kz/news/1",
                "date": "15.01.2025",
                "description": "В университете IITU открылась новая современная IT-лаборатория...",
                "source": "IITU Official (demo)",
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "title": "Хакатон IITU 2025 — регистрация открыта",
                "link": "https://iitu.edu.kz/news/2",
                "date": "10.01.2025",
                "description": "Ежегодный хакатон IITU принимает заявки от студентов...",
                "source": "IITU Official (demo)",
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "title": "Студенты IITU выиграли международный конкурс",
                "link": "https://iitu.edu.kz/news/3",
                "date": "05.01.2025",
                "description": "Команда студентов заняла первое место на международном конкурсе...",
                "source": "IITU Official (demo)",
                "scraped_at": datetime.now().isoformat(),
            },
        ]

    def save_to_json(self, data: List[Dict], filename: str = "news.json") -> str:
        filepath = SCRAPING_OUTPUT_DIR / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    {"scraped_at": datetime.now().isoformat(), "items": data},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            logger.info(f"✅ Saved to JSON: {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"❌ Failed to save JSON: {e}")
            return ""

    def save_to_csv(self, data: List[Dict], filename: str = "news.csv") -> str:
        filepath = SCRAPING_OUTPUT_DIR / filename
        if not data:
            return ""

        try:
            fieldnames = list(data[0].keys())
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"✅ Saved to CSV: {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"❌ Failed to save CSV: {e}")
            return ""

    def save_to_txt(self, data: List[Dict], filename: str = "news.txt") -> str:
        filepath = SCRAPING_OUTPUT_DIR / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"IITU News — Scraped at {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                for i, item in enumerate(data, 1):
                    f.write(f"{i}. {item.get('title', 'N/A')}\n")
                    f.write(f"   Дата: {item.get('date', 'N/A')}\n")
                    f.write(f"   Ссылка: {item.get('link', 'N/A')}\n")
                    if item.get("description"):
                        f.write(f"   {item['description'][:100]}...\n")
                    f.write("\n")
            logger.info(f"✅ Saved to TXT: {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"❌ Failed to save TXT: {e}")
            return ""

    def scrape_and_save_all(self) -> Dict[str, str]:
        news = self.scrape_news(max_items=10)
        return {
            "json": self.save_to_json(news),
            "csv": self.save_to_csv(news),
            "txt": self.save_to_txt(news),
            "count": str(len(news)),
        }

    def format_news_for_bot(self, news: List[Dict], max_items: int = 5) -> str:
        if not news:
            return "📰 Новости IITU временно недоступны."

        lines = ["📰 *Последние новости IITU*\n"]
        for i, item in enumerate(news[:max_items], 1):
            title = item.get("title", "Без заголовка")
            date = item.get("date", "")
            link = item.get("link", "")

            line = f"{i}. *{title}*"
            if date:
                line += f"\n   📅 {date}"
            if link:
                line += f"\n   🔗 [Читать далее]({link})"
            lines.append(line + "\n")

        return "\n".join(lines)

_scraper_instance: Optional[IITUScraper] = None

def get_scraper() -> IITUScraper:
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = IITUScraper()
    return _scraper_instance

if __name__ == "__main__":
    scraper = IITUScraper()
    print("=== IITU Scraper Demo ===")
    results = scraper.scrape_and_save_all()
    print(f"Saved to: {results}")
    news = scraper.scrape_news()
    print(scraper.format_news_for_bot(news))