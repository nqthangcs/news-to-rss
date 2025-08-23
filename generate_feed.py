import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Base scraper with reusable logic for a single feed."""

    def __init__(self, url: str, feed_title: str, feed_description: str):
        """
        :param url: url for the RSS feed
        :param feed_title: title for the RSS feed
        :param feed_description: description for the RSS feed
        """
        self.url = url
        self.feed_title = feed_title
        self.feed_description = feed_description
        self.headers = {
            "Sec-Ch-Ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Connection": "keep-alive",
        }

    def fetch(self) -> requests.Response:
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response

    @abstractmethod
    def _parse_content(self, response: requests.Response) -> list[dict]:
        """
        Parse the website and return a list of news items.
        Each dict must have keys:
            - title (str)
            - link (str)
            - date (datetime)
        """
        pass

    def parse_content(self, response: requests.Response) -> list[dict]:
        """
        Parse the website and return a list of news items.
        Each dict must have keys:
            - title (str)
            - link (str)
            - date (datetime)
        """
        news = self._parse_content(response)
        self._validate_news_list(news)
        return news
    
    def _validate_news_list(self, news: list[dict]) -> None:
        if not isinstance(news, list):
            raise TypeError("parse_content() must return a list")

        for i, item in enumerate(news):
            if not isinstance(item, dict):
                raise TypeError(f"Item {i} is not a dict: {item}")

            required_keys = {"title", "link", "date"}
            missing = required_keys - set(item.keys())
            if missing:
                raise ValueError(f"Item {i} is missing keys: {missing}")

            if not isinstance(item["title"], str):
                raise TypeError(f"Item {i} 'title' must be str, got {type(item['title'])}")
            if not isinstance(item["link"], str):
                raise TypeError(f"Item {i} 'link' must be str, got {type(item['link'])}")
            if not isinstance(item["date"], datetime):
                raise TypeError(f"Item {i} 'date' must be datetime, got {type(item['date'])}")

    def build_feed(self, news: list[dict], output_file: str = "feed.xml"):
        fg = FeedGenerator()
        fg.title(self.feed_title)
        fg.link(href=self.url, rel="alternate")
        fg.description(self.feed_description)

        # reverse list before adding → preserves DOM order in XML
        for item in reversed(news):
            fe = fg.add_entry()
            fe.title(item["title"])
            fe.link(href=item["link"])
            fe.pubDate(item["date"])

        fg.rss_file(output_file)
        print(f"✅ Feed saved to {output_file}")


class MultiScraper:
    """Run multiple scrapers and merge results."""

    def __init__(self, scrapers: list[BaseScraper], feed_title: str, feed_description: str):
        self.scrapers = scrapers
        self.feed_title = feed_title
        self.feed_description = feed_description

    def collect_news(self) -> list[dict]:
        all_news: list[dict] = []
        for scraper in self.scrapers:
            response = scraper.fetch()
            news = scraper.parse_content(response)
            all_news.extend(news)
        return all_news

    def build_feed(self, all_news: list[dict], output_file: str = "feed.xml"):
        # Merge all, then sort newest → oldest
        sorted_news = sorted(all_news, key=lambda x: x["date"], reverse=True)

        fg = FeedGenerator()
        fg.title(self.feed_title)
        fg.link(href=self.scrapers[0].url, rel="alternate")  # pick first as base
        fg.description(self.feed_description)

        # reverse list before adding → preserves DOM order in XML
        for item in reversed(sorted_news):
            fe = fg.add_entry()
            fe.title(item["title"])
            fe.link(href=item["link"])
            fe.pubDate(item["date"])

        fg.rss_file(output_file)
        print(f"✅ Feed saved to {output_file} ({len(sorted_news)} items)")


class FITScraper(BaseScraper):
    """Scraper for FIT@HCMUS announcements (single category)."""
    BASE = "https://www.fit.hcmus.edu.vn"

    def _parse_content(self, response: requests.Response) -> list[dict]:
        soup = BeautifulSoup(response.text, "html.parser")
        news: list[dict] = []

        for item in soup.select(".post-content"):
            title = item.find("a").text.strip()
            link = item.find("a")["href"]

            # Make link absolute
            if link.startswith("/"):
                link = self.BASE + link

            date_str = item.select_one("li.post-date span").text.strip()
            date = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=timezone.utc)

            news.append({"title": title, "link": link, "date": date})

        return news


def main():
    urls = [
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/thong-bao-chung",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/thong-bao-he-chinh-quy",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/tot-nghiep-qui-trinh-thuc-hien",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/thong-tin-hoc-bong",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/thong-bao-sau-dai-hoc",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/thong-bao-lien-thong-dh-ths",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/lich-truc-co-van-hoc-tap",
        "https://www.fit.hcmus.edu.vn/tin-tuc/c/thong-tin-tuyen-dung",
    ]

    # Create a scraper for each website.
    scrapers = [FITScraper(url, "FIT News", "Unofficial RSS for FIT@HCMUS category") for url in urls]

    # If you want one feed per category → call build_feed() on each scraper
    # If you want one merged feed → use MultiScraper
    multi = MultiScraper(scrapers, "FIT@HCMUS News Feed", "Unofficial RSS for FIT@HCMUS news")
    all_news = multi.collect_news()
    multi.build_feed(all_news, "feed.xml")


if __name__ == "__main__":
    main()
