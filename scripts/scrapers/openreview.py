"""
OpenReview API 抓取器。
用于 NeurIPS, ICML, ICLR 等使用 OpenReview 的会议。
通过 OpenReview API 获取 accepted papers 及摘要。
"""

import logging
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class OpenReviewScraper(BaseScraper):
    """OpenReview API 抓取器，适用于 NeurIPS/ICML/ICLR。"""

    def scrape(self, year: int) -> list:
        venue = self.config.get("openreview_venue", "")
        if not venue:
            logger.error("No openreview_venue in config")
            return []

        # 构造 API URL
        # OpenReview v2 API: 查找 venue 的所有 accepted papers
        venue_id = f"{venue}.cc/{year}/Conference"
        search_url = f"https://api2.openreview.net/notes?content.venueid={venue_id}&domain={venue}.cc&limit=1000"

        data = self._fetch_json(search_url)
        if not data or "notes" not in data:
            # 尝试 v1 API 回退
            return self._scrape_v1(venue, year)

        papers = []
        for note in data["notes"]:
            content = note.get("content", {})
            title = self._get_content_value(content, "title")
            abstract = self._get_content_value(content, "abstract")
            authors = self._get_content_value(content, "authors", as_list=True)
            pdf_url = self._get_pdf_url(note, venue, year)

            if title:
                papers.append(self._make_paper_entry(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=pdf_url,
                    conference=venue,
                    year=year,
                ))

        return papers

    def _scrape_v1(self, venue: str, year: int) -> list:
        """OpenReview v1 API 回退方案。"""
        # v1 API: 使用 venues 端点查找 conference
        venue_url = f"https://api.openreview.net/venues?id={venue}.cc"
        venue_data = self._fetch_json(venue_url)
        if not venue_data or "venues" not in venue_data:
            logger.warning(f"Could not find venue for {venue} {year}")
            return []

        # 找到对应年份的 conference
        conf_id = None
        for v in venue_data["venues"]:
            if str(year) in v and "Conference" in v:
                conf_id = v
                break

        if not conf_id:
            logger.warning(f"No conference found for {venue} {year}")
            return []

        # 获取 accepted papers
        notes_url = f"https://api.openreview.net/notes?invitation={conf_id}/-/Blinded_Submission&limit=1000"
        data = self._fetch_json(notes_url)
        if not data or "notes" not in data:
            return []

        papers = []
        for note in data["notes"]:
            content = note.get("content", {})
            title = content.get("title", {}).get("value", "") if isinstance(content.get("title"), dict) else content.get("title", "")
            abstract = content.get("abstract", {}).get("value", "") if isinstance(content.get("abstract"), dict) else content.get("abstract", "")
            authors_raw = content.get("authors", {}).get("value", []) if isinstance(content.get("authors"), dict) else content.get("authors", [])
            authors = authors_raw if isinstance(authors_raw, list) else [str(authors_raw)]

            if title:
                papers.append(self._make_paper_entry(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=f"https://openreview.net/forum?id={note.get('id', '')}",
                    conference=venue,
                    year=year,
                ))

        return papers

    def _get_content_value(self, content: dict, key: str, as_list: bool = False):
        """从 OpenReview content 中获取字段值，兼容 v1/v2 格式。"""
        val = content.get(key)
        if val is None:
            return [] if as_list else ""
        if isinstance(val, dict):
            val = val.get("value", [] if as_list else "")
        if as_list:
            return val if isinstance(val, list) else [str(val)] if val else []
        return str(val) if val else ""

    def _get_pdf_url(self, note: dict, venue: str, year: int) -> str:
        """构造论文 PDF/Forum 链接。"""
        note_id = note.get("id", "")
        if note_id:
            return f"https://openreview.net/forum?id={note_id}"
        return ""
