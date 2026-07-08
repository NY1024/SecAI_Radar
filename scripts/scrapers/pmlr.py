"""
PMLR (Proceedings of Machine Learning Research) 抓取器。
用于 ICML 及其他使用 PMLR 托管 proceedings 的会议。
通过 PMLR proceedings 页面获取论文标题、作者，再从详情页获取摘要。
"""

import re
import time
import logging
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# ICML 年份到 PMLR 卷号映射
ICML_PMLR_VOLUMES = {
    2020: "v119",
    2021: "v139",
    2022: "v162",
    2023: "v202",
    2024: "v235",
    2025: "v267",
}


class PMLRScraper(BaseScraper):
    """PMLR proceedings 抓取器，用于 ICML。"""

    def scrape(self, year: int) -> list:
        conf_name = self.config.get("name", "ICML")
        volume = ICML_PMLR_VOLUMES.get(year)

        if not volume:
            logger.warning(f"No PMLR volume mapping for {conf_name} {year}")
            return []

        base_url = f"https://proceedings.mlr.press/{volume}/"
        html = self._fetch(base_url)
        if not html:
            logger.error(f"Failed to fetch PMLR {volume} for {conf_name} {year}")
            return []

        soup = self._parse_html(html)
        papers_raw = soup.select("div.paper")
        logger.info(f"PMLR {volume}: found {len(papers_raw)} total papers")

        papers = []
        for div in papers_raw:
            title_tag = div.find("p", class_="title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            authors = []
            authors_tag = div.find("span", class_="authors")
            if authors_tag:
                authors_text = authors_tag.get_text(strip=True)
                authors = [a.strip() for a in re.split(r'[,;]', authors_text) if a.strip()]

            # 找到 abstract 详情页链接
            abs_url = ""
            links_tag = div.find("p", class_="links")
            if links_tag:
                for a in links_tag.find_all("a"):
                    href = a.get("href", "")
                    if a.text.strip().lower() == "abs" and href:
                        abs_url = href
                        break

            if not abs_url:
                # fallback: 尝试任何 .html 链接
                for a in div.find_all("a"):
                    href = a.get("href", "")
                    if href.endswith(".html"):
                        abs_url = href
                        break

            papers.append(self._make_paper_entry(
                title=title,
                authors=authors[:10],
                abstract="",  # 稍后单独获取
                url=abs_url or base_url,
                conference=conf_name,
                year=year,
            ))

        return papers

    def fetch_abstract(self, paper_url: str) -> str:
        """从 PMLR 论文详情页获取摘要。"""
        if not paper_url or not paper_url.endswith(".html"):
            return ""

        html = self._fetch(paper_url, retries=2, delay=1.0)
        if not html:
            return ""

        soup = self._parse_html(html)
        abstract_tag = soup.find("div", class_="abstract") or soup.find("p", class_="abstract")
        if abstract_tag:
            return abstract_tag.get_text(strip=True)

        # Fallback: meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            return meta.get("content", "").strip()

        return ""
