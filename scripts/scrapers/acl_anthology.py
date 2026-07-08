"""
ACL Anthology 抓取器。
通过 GitHub 上的 ACL Anthology XML 数据获取论文（含标题、作者、完整摘要）。
数据源：https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml/{year}.{prefix}.xml

支持 ACL、EMNLP 等基于 ACL Anthology 的会议。
"""

import logging
import xml.etree.ElementTree as ET

from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# XML 数据源基础 URL
XML_BASE = "https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml"

# 每个会议每年的 XML 文件前缀列表
# ACL 包含主论文集和 Findings，EMNLP 只有主论文集
CONFERENCE_VOLUMES = {
    "ACL": ["acl", "findings"],
    "EMNLP": ["emnlp"],
}


class ACLAnthologyScraper(BaseScraper):
    """ACL Anthology XML 抓取器，用于 ACL 和 EMNLP。"""

    def scrape(self, year: int) -> list:
        conf_name = self.config.get("name", "ACL")
        volumes = CONFERENCE_VOLUMES.get(conf_name, [conf_name.lower()])

        all_papers = []
        for prefix in volumes:
            url = f"{XML_BASE}/{year}.{prefix}.xml"
            logger.info(f"Fetching {conf_name} {year} volume '{prefix}': {url}")
            papers = self._scrape_volume(url, conf_name, year)
            all_papers.extend(papers)
            logger.info(f"  Volume '{prefix}': {len(papers)} papers")

        return all_papers

    def _scrape_volume(self, url: str, conf_name: str, year: int) -> list:
        """抓取单个 XML 卷。"""
        xml_text = self._fetch(url)
        if not xml_text:
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"XML parse error for {url}: {e}")
            return []

        papers = []
        for paper_elem in root.findall(".//paper"):
            title = paper_elem.findtext("title", "").strip()
            if not title or len(title) < 5:
                continue

            abstract = paper_elem.findtext("abstract", "")
            abstract = abstract.strip() if abstract else ""

            # 作者列表
            authors = []
            for author_elem in paper_elem.findall(".//author"):
                first = author_elem.findtext("first", "").strip()
                last = author_elem.findtext("last", "").strip()
                name = f"{first} {last}".strip()
                if name:
                    authors.append(name)
                else:
                    # 有些作者只有 <text> 子标签
                    text = author_elem.findtext("text", "").strip()
                    if text:
                        authors.append(text)

            # 论文 URL（anthology ID 如 2024.acl-long.1）
            url_elem = paper_elem.find("url")
            paper_url = ""
            if url_elem is not None and url_elem.text:
                paper_id = url_elem.text.strip()
                paper_url = f"https://aclanthology.org/{paper_id}/"

            papers.append(self._make_paper_entry(
                title=title,
                authors=authors[:15],
                abstract=abstract,
                url=paper_url,
                conference=conf_name,
                year=year,
            ))

        return papers
