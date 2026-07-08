"""
NeurIPS 虚拟站点抓取器。
通过 neurips.cc/static/virtual/data/neurips-{year}-orals-posters.json 获取论文数据。
该 JSON 包含所有 accepted papers 的标题、作者、摘要和 OpenReview 链接。
JSON 结构与 ICLR Virtual 站点完全一致。
"""

import logging
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class NeurIPSVirtualScraper(BaseScraper):
    """NeurIPS 虚拟站点 JSON 抓取器。"""

    def scrape(self, year: int) -> list:
        conf_name = self.config.get("name", "NeurIPS")
        url = f"https://neurips.cc/static/virtual/data/neurips-{year}-orals-posters.json"

        data = self._fetch_json(url)
        if not data or "results" not in data:
            logger.error(f"Failed to fetch NeurIPS {year} virtual JSON from {url}")
            return []

        results = data.get("results", [])
        logger.info(f"NeurIPS {year} virtual: {len(results)} total papers")

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

            # 论文链接（NeurIPS proceedings 页面）
            paper_url = item.get("paper_url") or ""
            paper_url = paper_url.strip() if isinstance(paper_url, str) else ""
            if not paper_url:
                # 回退到 OpenReview forum 链接
                fallback_url = item.get("url") or ""
                paper_url = fallback_url.strip() if isinstance(fallback_url, str) else ""

            papers.append(self._make_paper_entry(
                title=title,
                authors=authors[:15],
                abstract=abstract,
                url=paper_url,
                conference=conf_name,
                year=year,
            ))

        return papers
