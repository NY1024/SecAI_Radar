"""
DBLP 抓取器。
数据源: DBLP (https://dblp.org/)。
支持从 DBLP HTML 页面抓取会议论文的标题和作者信息。
"""

import logging
import time

from bs4 import NavigableString
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class DBLPScraper(BaseScraper):
    """DBLP 会议论文抓取器。

    通过 config 中的 dblp_key 字段（如 "sp", "ccs", "uss", "ndss", "aaai"）
    构造 DBLP URL，抓取并解析 HTML 页面。
    """

    def scrape(self, year: int) -> list:
        """抓取指定年份的 DBLP 会议论文。

        Args:
            year: 会议年份

        Returns:
            论文列表，每条包含 title, authors, abstract, url, conference, year 字段
        """
        key = self.config.get("dblp_key", "")
        if not key:
            logger.error(f"Missing 'dblp_key' in config for {self.config.get('name', 'unknown')}")
            return []

        url = f"https://dblp.org/db/conf/{key}/{key}{year}.html"
        logger.info(f"Fetching DBLP page: {url}")

        html = self._fetch(url)
        if not html:
            logger.warning(f"Failed to fetch DBLP page for {key} {year}: {url}")
            return []

        # 页面请求后 sleep 以避免被 DBLP 限流
        time.sleep(2)

        soup = self._parse_html(html)
        conf_name = self.config.get("name", "")

        papers = []
        entries = soup.find_all("cite", class_="data")
        logger.info(f"Found {len(entries)} <cite class='data'> entries on page")

        for idx, entry in enumerate(entries):
            # 查找标题
            title_tag = entry.find("span", class_="title")
            if not title_tag:
                # 跳过没有标题的条目（如 proceedings 前言）
                continue

            title = title_tag.get_text(strip=True)

            # 跳过 proceedings 前言
            if "Proceedings of" in title:
                continue

            # 提取作者：取 title span 之前的文本
            authors = self._extract_authors(entry, title_tag)

            # 构造论文 URL（使用 DBLP 页面 URL）
            paper_url = url

            papers.append(self._make_paper_entry(
                title=title,
                authors=authors,
                abstract="",
                url=paper_url,
                conference=conf_name,
                year=year,
            ))

        logger.info(f"Extracted {len(papers)} papers from DBLP {key} {year}")
        return papers

    def _extract_authors(self, cite_tag, title_tag) -> list:
        """从 cite 标签中提取作者列表。

        DBLP 格式: "Author1, Author2, Author3:Title..."
        作者在 title span 之前的文本中，用逗号分隔，
        最后一个作者后面有冒号。

        Args:
            cite_tag: <cite class="data"> BeautifulSoup Tag
            title_tag: <span class="title"> BeautifulSoup Tag

        Returns:
            作者名列表
        """
        text_before = ""
        for child in cite_tag.descendants:
            if child is title_tag:
                break
            if isinstance(child, NavigableString):
                text_before += str(child)

        text_before = text_before.strip()
        if not text_before:
            return []

        # 移除末尾的冒号
        text_before = text_before.rstrip(":").strip()

        # 按逗号分隔作者
        authors = [a.strip() for a in text_before.split(",") if a.strip()]
        return authors
