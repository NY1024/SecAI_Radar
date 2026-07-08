"""
SaTML (IEEE Secure and Trustworthy ML) 抓取器。
数据源: SaTML 官网 https://satml.org/{year}/accepted-papers

SaTML 是 ML 安全专门会议，所有论文都在 scope 内，不需要关键词筛选。

页面结构:
- 2023/2025: 论文在 <li class="list-group-item"> 中
    <div class="fw-bold"><b>Title</b></div>Author1, Author2, ...
    <span class="badge"><a href="...openreview...">OpenReview</a></span>
- 2024: 结构可能不同，需要灵活解析
- 标题在 <b> 或 <div class="fw-bold"> 中，作者在后面
- 论文链接在 <a> 中（OpenReview 链接）
"""

import re
import logging
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class SATMLScraper(BaseScraper):
    """SaTML accepted papers 抓取器。"""

    def scrape(self, year: int) -> list:
        base = self.config["urls"]["base"]

        # 尝试多种 URL 模式
        candidate_urls = [
            f"{base}/{year}/accepted-papers",
            f"{base}/{year}/accepted-papers/",
            f"{base}/{year}/accepted-papers.html",
            f"{base}/{year}/program",
            f"{base}/{year}/program/",
            f"{base}/{year}/program.html",
        ]

        papers = []
        for url in candidate_urls:
            html = self._fetch(url)
            if not html:
                continue

            soup = self._parse_html(html)
            papers = self._parse_accepted_page(soup, url, year)
            if papers:
                logger.info(f"Found {len(papers)} papers from {url}")
                break

        return papers

    def _parse_accepted_page(self, soup, source_url: str, year: int) -> list:
        """解析 SaTML accepted papers 页面，处理不同年份的结构差异。"""
        papers = []
        seen_titles = set()

        # 模式1: <li class="list-group-item"> 条目（2023, 2025 主要结构）
        entries = soup.find_all("li", class_="list-group-item")
        if len(entries) >= 3:
            logger.info(f"  Using list-group-item parser: {len(entries)} entries")
            for entry in entries:
                paper = self._parse_list_group_entry(entry, source_url, year, seen_titles)
                if paper:
                    papers.append(paper)
            if papers:
                return papers

        # 模式2: 所有 <li> 条目（兜底）
        entries = soup.find_all("li")
        # 过滤导航菜单的 <li>
        entries = [e for e in entries if "nav-item" not in " ".join(e.get("class", []))]
        if len(entries) >= 5:
            logger.info(f"  Using generic <li> parser: {len(entries)} entries")
            for entry in entries:
                paper = self._parse_generic_entry(entry, source_url, year, seen_titles)
                if paper:
                    papers.append(paper)
            if papers:
                return papers

        # 模式3: <p> 条目（2024 可能用 <p>）
        entries = soup.find_all("p")
        if len(entries) >= 5:
            logger.info(f"  Using <p> parser: {len(entries)} entries")
            for entry in entries:
                paper = self._parse_generic_entry(entry, source_url, year, seen_titles)
                if paper:
                    papers.append(paper)

        return papers

    def _parse_list_group_entry(self, entry, source_url: str, year: int, seen_titles: set) -> dict:
        """解析 <li class="list-group-item"> 结构。

        结构:
          <div class="ms-2 me-auto">
            <div class="fw-bold"><b>Title</b></div>
            Author1 (University), Author2 (University), ...
          </div>
          <span class="badge"><a href="...openreview...">OpenReview</a></span>
        """
        # 标题在 <div class="fw-bold"> 中的 <b> 标签
        title_div = entry.find("div", class_="fw-bold")
        if title_div:
            b_tag = title_div.find("b")
            title = (b_tag or title_div).get_text(strip=True)
        else:
            b_tag = entry.find("b")
            title = b_tag.get_text(strip=True) if b_tag else ""

        title = self._clean_title(title)
        if not title or len(title) < 10:
            return None

        lower_title = title.lower()
        if lower_title in seen_titles:
            return None
        if self._is_non_paper(lower_title):
            return None
        seen_titles.add(lower_title)

        # 提取作者: 在 fw-bold div 之后、badge 之前的文本
        authors = []
        content_div = entry.find("div", class_="ms-2")
        if content_div:
            # 获取 fw-bold div 之后的所有文本
            fw_bold = content_div.find("div", class_="fw-bold")
            if fw_bold:
                # 获取 fw-bold 的下一个兄弟文本节点
                full_text = content_div.get_text(separator=" ", strip=True)
                # 移除标题部分
                title_text = fw_bold.get_text(strip=True)
                author_text = full_text.replace(title_text, "", 1).strip()
                if author_text:
                    authors = [a.strip() for a in author_text.split(",") if a.strip() and len(a.strip()) > 2]
                    authors = authors[:10]

        # 提取链接: OpenReview 链接
        link = ""
        for a in entry.find_all("a"):
            href = a.get("href", "")
            if "openreview.net" in href or "forum" in href:
                link = href
                break

        return self._make_paper_entry(
            title=title,
            authors=authors[:5],
            abstract="",
            url=link or source_url,
            conference="SaTML",
            year=year,
        )

    def _parse_generic_entry(self, entry, source_url: str, year: int, seen_titles: set) -> dict:
        """通用解析: <li> 或 <p> 中的论文。"""
        text = entry.get_text(separator=" ", strip=True)
        if not text or len(text) < 15:
            return None

        # 查找标题: 优先 <b> 或 <strong> 或 <em>
        title_tag = entry.find("b") or entry.find("strong") or entry.find("em")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = ""
            # 查找链接
            for a in entry.find_all("a"):
                href = a.get("href", "")
                if "openreview" in href or "forum" in href:
                    link = href
                    break
                if not link and href:
                    link = href
        else:
            title = text
            link = ""

        title = self._clean_title(title)
        if not title or len(title) < 10:
            return None

        lower_title = title.lower()
        if lower_title in seen_titles:
            return None
        if self._is_non_paper(lower_title):
            return None
        seen_titles.add(lower_title)

        # 提取作者
        authors = []
        full_text = entry.get_text(separator=" ", strip=True)
        # 移除标题后提取作者
        author_text = full_text.replace(title, "", 1).strip()
        # 移除 "OpenReview" 等链接文本
        author_text = re.sub(r'\bOpenReview\b', '', author_text).strip()
        if author_text and len(author_text) > 3:
            authors = [a.strip() for a in re.split(r'[,;]', author_text) if a.strip() and len(a.strip()) > 2]
            authors = authors[:10]

        if link and not link.startswith("http"):
            link = f"{self.config['urls']['base']}/{link.lstrip('/')}"

        return self._make_paper_entry(
            title=title,
            authors=authors[:5],
            abstract="",
            url=link or source_url,
            conference="SaTML",
            year=year,
        )

    def _clean_title(self, title: str) -> str:
        """清理标题: 移除序号前缀等。"""
        title = re.sub(r'^\d+[\.\)]\s*', '', title)
        title = re.sub(r'^(paper|title)\s*[:\-]\s*', '', title, flags=re.I)
        return title.strip()

    def _is_non_paper(self, lower_title: str) -> bool:
        """判断是否为非论文条目（导航菜单等）。"""
        skip_words = ['accepted papers', 'program', 'committee', 'organizing',
                       'sponsor', 'call for papers', 'contact', 'home', 'submission',
                       'registration', 'travel', 'venue']
        return any(skip in lower_title for skip in skip_words)