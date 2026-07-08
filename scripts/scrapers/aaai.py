"""
AAAI Accepted Papers 抓取器。
数据源: AAAI 官网 PDF 或 AAAI Digital Library。
"""

import re
import logging
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AAAIScraper(BaseScraper):
    """AAAI accepted papers 抓取器。"""

    def scrape(self, year: int) -> list:
        url = self.config["urls"]["accepted"].replace("2025", str(year))
        html = self._fetch(url)
        if not html:
            # 尝试 AAAI DL
            dl_url = f"https://ojs.aaai.org/index.php/AAAI/issue/view/{year}"
            html = self._fetch(dl_url)
            if not html:
                return []
            return self._parse_dl(html, year)

        soup = self._parse_html(html)
        papers = []

        # 尝试解析 HTML（如果 URL 返回的是 HTML）
        entries = soup.find_all(["li", "div", "p"])
        for entry in entries:
            text = entry.get_text(separator=" ", strip=True)
            if len(text) < 20:
                continue
            # AAAI 格式: "Paper Title, Author1, Author2, ..."
            parts = text.split(",")
            if len(parts) >= 2:
                title = parts[0].strip()
                authors = [p.strip() for p in parts[1:5]]
                if title and len(title) > 10:
                    papers.append(self._make_paper_entry(
                        title=title,
                        authors=authors,
                        abstract="",
                        url=url,
                        conference="AAAI",
                        year=year,
                    ))

        return papers

    def _parse_dl(self, html: str, year: int) -> list:
        """解析 AAAI Digital Library 页面。"""
        soup = self._parse_html(html)
        papers = []
        entries = soup.select("div.obj_article_summary, h3.title")
        for entry in entries:
            title_tag = entry.find("a") if entry.name != "a" else entry
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if title and len(title) > 10:
                papers.append(self._make_paper_entry(
                    title=title,
                    authors=[],
                    abstract="",
                    url=link,
                    conference="AAAI",
                    year=year,
                ))
        return papers
