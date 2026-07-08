"""
抓取器基类。
所有会议抓取器继承 BaseScraper，统一接口。
"""

import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """会议论文抓取器基类。"""

    def __init__(self, conference_config: dict):
        self.config = conference_config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })

    def _fetch(self, url: str, retries: int = 3, delay: float = 2.0) -> Optional[str]:
        """带重试的 HTTP GET 请求。"""
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as e:
                logger.warning(f"Fetch attempt {attempt+1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        return None

    def _fetch_json(self, url: str, retries: int = 3, delay: float = 2.0) -> Optional[dict]:
        """带重试的 HTTP GET 请求，返回 JSON。"""
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as e:
                logger.warning(f"Fetch JSON attempt {attempt+1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """解析 HTML 字符串。"""
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    def scrape(self, year: int) -> list:
        """
        抓取指定年份的 accepted papers。

        Args:
            year: 会议年份

        Returns:
            论文列表，每条包含 title, authors, abstract, url, conference, year 字段
        """
        pass

    def _make_paper_entry(
        self, title: str, authors: list, abstract: str,
        url: str, conference: str, year: int
    ) -> dict:
        """构造统一的论文数据条目。"""
        return {
            "title": title.strip(),
            "authors": authors if isinstance(authors, list) else [authors],
            "abstract": abstract.strip() if abstract else "",
            "url": url,
            "conference": conference,
            "year": year,
            "scraped_at": datetime.now().isoformat(),
        }
