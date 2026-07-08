"""
CVF Open Access 抓取器。
用于 CVPR 和 ECCV。

CVPR 数据源: https://openaccess.thecvf.com/CVPR{year}?day=all
  - 论文标题在 <dt> 标签中
  - 论文链接在 <dd> 中的 <a href> 标签，href 包含 content_
  - CVF 站点不稳定（SSL 超时），需要 60s timeout 和多次重试

ECCV 数据源: https://www.ecva.net/papers.php
  - 论文标题在 <dt class="ptitle"> 中的 <a> 标签
  - 作者在紧随其后的 <dd> 中
  - 链接格式: papers/eccv_{year}/papers_ECCV/html/{id}_ECCV_{year}_paper.php
"""

import re
import logging
import time
import requests
from typing import Optional

from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# ECCV 论文列表页面 (ECVA)
ECVA_PAPERS_URL = "https://www.ecva.net/papers.php"


class CVFScraper(BaseScraper):
    """CVF/ECVA 抓取器，用于 CVPR 和 ECCV。"""

    def scrape(self, year: int) -> list:
        base = self.config["urls"]["base"]
        conf_name = self.config.get("name", "CVPR")

        # ECCV 是两年一届（偶数年）
        if self.config.get("biennial", False) and year % 2 != 0:
            logger.info(f"{conf_name} not held in {year} (biennial, even years only)")
            return []

        if conf_name == "ECCV":
            # ECCV 论文托管在 ecva.net/papers.php
            return self._scrape_eccv(year)
        else:
            # CVPR 使用 openaccess.thecvf.com
            return self._scrape_cvpr(base, conf_name, year)

    def _scrape_cvpr(self, base: str, conf_name: str, year: int) -> list:
        """抓取 CVPR（openaccess.thecvf.com）。"""
        url = f"{base}/{conf_name}{year}?day=all"
        logger.info(f"Fetching {conf_name} {year}: {url}")

        html = self._fetch_cvf(url)
        if not html:
            logger.warning(f"Failed to fetch {conf_name} {year} from {url}")
            return []

        soup = self._parse_html(html)
        papers = self._parse_cvpr_page(soup, base, conf_name, year, url)

        logger.info(f"  {conf_name} {year}: {len(papers)} papers")
        return papers

    def _scrape_eccv(self, year: int) -> list:
        """抓取 ECCV（ecva.net/papers.php）。"""
        logger.info(f"Fetching ECCV {year} from {ECVA_PAPERS_URL}")

        html = self._fetch_cvf(ECVA_PAPERS_URL)
        if not html:
            logger.warning(f"Failed to fetch ECCV {year} from {ECVA_PAPERS_URL}")
            return []

        soup = self._parse_html(html)
        papers = self._parse_eccv_page(soup, year)

        logger.info(f"  ECCV {year}: {len(papers)} papers")
        return papers

    def _fetch_cvf(self, url: str) -> Optional[str]:
        """CVF/ECVA 站点专用 fetch: 60s timeout, 5 retries with longer delay。"""
        for attempt in range(5):
            try:
                resp = self.session.get(url, timeout=60)
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as e:
                logger.warning(f"Fetch attempt {attempt+1}/5 failed for {url}: {e}")
                if attempt < 4:
                    time.sleep(5)
        return None

    def _parse_cvpr_page(self, soup, base: str, conf_name: str, year: int, page_url: str) -> list:
        """解析 CVPR open access 页面的 <dt>/<dd> 结构。"""
        papers = []
        seen_titles = set()

        dt_tags = soup.find_all("dt")
        logger.info(f"  Found {len(dt_tags)} <dt> tags")

        for dt in dt_tags:
            title_tag = dt.find("a")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                title = dt.get_text(strip=True)

            title = re.sub(r'^\d+[\.\)]\s*', '', title).strip()
            if not title or len(title) < 5:
                continue
            if title.lower() in seen_titles:
                continue

            link = ""
            dd = dt.find_next_sibling("dd")
            if dd:
                for a in dd.find_all("a"):
                    href = a.get("href", "")
                    if "content_" in href:
                        if href.startswith("http"):
                            link = href
                        else:
                            link = f"{base}/{href.lstrip('/')}"
                        break

            seen_titles.add(title.lower())
            papers.append(self._make_paper_entry(
                title=title,
                authors=[],
                abstract="",
                url=link or page_url,
                conference=conf_name,
                year=year,
            ))

        return papers

    def _parse_eccv_page(self, soup, year: int) -> list:
        """解析 ECVA papers.php 页面中的 ECCV 论文。

        结构:
          <dt class="ptitle"><br>
            <a href=papers/eccv_{year}/papers_ECCV/html/{id}_ECCV_{year}_paper.php>
              Title</a>
          </dt><dd>
            Author1, Author2, Author3</dd>
        """
        papers = []
        seen_titles = set()
        year_str = str(year)
        eccv_prefix = f"eccv_{year_str}"

        # 查找所有 <dt class="ptitle"> 标签
        dt_tags = soup.find_all("dt", class_="ptitle")
        logger.info(f"  Found {len(dt_tags)} <dt class='ptitle'> tags (all years, filtering for {year})")

        for dt in dt_tags:
            a_tag = dt.find("a")
            if not a_tag:
                continue

            href = a_tag.get("href", "")
            # 只保留目标年份的论文
            if eccv_prefix not in href:
                continue

            title = a_tag.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            if title.lower() in seen_titles:
                continue

            # 构建完整 URL
            if href.startswith("http"):
                link = href
            else:
                link = f"https://www.ecva.net/{href.lstrip('/')}"

            # 提取作者（在紧随其后的 <dd> 中）
            authors = []
            dd = dt.find_next_sibling("dd")
            if dd:
                author_text = dd.get_text(strip=True)
                # 作者格式: "Author1*, Author2, Author3"
                if author_text:
                    # 截断在第一个链接（pdf/DOI）之前
                    author_text = re.split(r'\[\s*(?:pdf|DOI)', author_text)[0].strip()
                    authors = [a.strip() for a in author_text.split(",") if a.strip()]
                    authors = authors[:15]

            seen_titles.add(title.lower())
            papers.append(self._make_paper_entry(
                title=title,
                authors=authors,
                abstract="",
                url=link,
                conference="ECCV",
                year=year,
            ))

        return papers
