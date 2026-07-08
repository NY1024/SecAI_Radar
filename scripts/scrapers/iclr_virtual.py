"""
ICLR Virtual 站点抓取器。
通过 iclr.cc/static/virtual/data/iclr-{year}-orals-posters.json 获取论文数据。
该 JSON 包含所有 accepted papers 的标题、作者、摘要和 OpenReview 链接。
"""

import logging
import requests
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ICLRVirtualScraper(BaseScraper):
    """ICLR Virtual 站点 JSON 抓取器。"""

    def scrape(self, year: int) -> list:
        conf_name = self.config.get("name", "ICLR")
        url = f"https://iclr.cc/static/virtual/data/iclr-{year}-orals-posters.json"

        data = self._fetch_json(url)
        if not data or "results" not in data:
            logger.error(f"Failed to fetch ICLR {year} virtual JSON from {url}")
            return []

        results = data.get("results", [])
        logger.info(f"ICLR {year} virtual: {len(results)} total papers")

        papers = []
        for item in results:
            # 'name' 字段是标题
            title = item.get("name", "").strip()
            if not title:
                continue

            # 作者：从 authors 列表中提取 fullname
            authors_raw = item.get("authors", [])
            authors = []
            if isinstance(authors_raw, list):
                for a in authors_raw:
                    if isinstance(a, dict):
                        name = a.get("fullname", "").strip()
                        if name:
                            authors.append(name)
                    elif isinstance(a, str):
                        authors.append(a.strip())

            abstract = item.get("abstract") or ""
            abstract = abstract.strip()

            # OpenReview 论文链接
            paper_url = item.get("paper_url", "").strip()

            # 关键词
            keywords = item.get("keywords", [])
            if isinstance(keywords, list):
                keywords = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
            else:
                keywords = []

            papers.append(self._make_paper_entry(
                title=title,
                authors=authors[:15],
                abstract=abstract,
                url=paper_url,
                conference=conf_name,
                year=year,
            ))

        return papers
