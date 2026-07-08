"""
SaTML (IEEE Secure and Trustworthy ML) 抓取器。
数据源: SaTML 官网 https://satml.org/{year}/accepted-papers

SaTML 是 ML 安全专门会议，所有论文都在 scope 内，不需要关键词筛选。

页面结构（因年份而异）:
- 2023: <li class="list-group-item"> 中 <div class="fw-bold"><b>Title</b></div> + 作者 + OpenReview 链接
- 2025: <ul class="paper-list"> 中 <li class="paper-item"> 含 <em class="paper-title">Title</em> + 作者 + Arxiv 链接 + <blockquote class="paper-abstract">
- 2026: <div class="block"> 三元组（标题<strong>/作者/按钮）+ 隐藏 <div id="abstract-rN"> 含 <p> 摘要
"""

import re
import logging
from scripts.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class SATMLScraper(BaseScraper):
    """SaTML accepted papers 抓取器。"""

    def scrape(self, year: int) -> list:
        base = self.config["urls"]["base"]

        candidate_urls = [
            f"{base}/{year}/accepted-papers",
            f"{base}/{year}/accepted-papers/",
            f"{base}/{year}/accepted-papers.html",
            f"{base}/{year}/program",
            f"{base}/{year}/program/",
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
        """解析 SaTML accepted papers 页面，自动适配不同年份的页面结构。"""
        # 模式1: 2023 风格 <li class="list-group-item">
        entries = soup.find_all("li", class_="list-group-item")
        if len(entries) >= 3:
            logger.info(f"  Using list-group-item parser: {len(entries)} entries")
            papers = []
            seen = set()
            for entry in entries:
                paper = self._parse_list_group_entry(entry, source_url, year, seen)
                if paper:
                    papers.append(paper)
            if papers:
                return papers

        # 模式2: 2025 风格 <ul class="paper-list"> <li class="paper-item">
        paper_lists = soup.find_all("ul", class_="paper-list")
        if paper_lists:
            total_items = sum(len(ul.find_all("li", class_="paper-item", recursive=False)) for ul in paper_lists)
            if total_items >= 3:
                logger.info(f"  Using paper-list parser: {total_items} items")
                papers = []
                seen = set()
                for ul in paper_lists:
                    for li in ul.find_all("li", class_="paper-item", recursive=False):
                        paper = self._parse_paper_list_entry(li, source_url, year, seen)
                        if paper:
                            papers.append(paper)
                if papers:
                    return papers

        # 模式3: 2026 风格 <div class="block"> 三元组
        blocks = soup.find_all("div", class_="block")
        non_abstract_blocks = [b for b in blocks if not b.get("id", "").startswith("abstract-")]
        if len(non_abstract_blocks) >= 6:
            logger.info(f"  Using block-triple parser: {len(non_abstract_blocks)} blocks")
            papers = self._parse_block_triples(non_abstract_blocks, soup, source_url, year)
            if papers:
                return papers

        # 模式4: 兜底通用 <li> 解析
        entries = soup.find_all("li")
        entries = [e for e in entries if "nav-item" not in " ".join(e.get("class", []))]
        if len(entries) >= 5:
            logger.info(f"  Using generic <li> parser: {len(entries)} entries")
            papers = []
            seen = set()
            for entry in entries:
                paper = self._parse_generic_entry(entry, source_url, year, seen)
                if paper:
                    papers.append(paper)
            if papers:
                return papers

        return []

    def _parse_list_group_entry(self, entry, source_url: str, year: int, seen_titles: set) -> dict:
        """解析 2023 风格 <li class="list-group-item">。"""
        title_div = entry.find("div", class_="fw-bold")
        if title_div:
            b_tag = title_div.find("b")
            title = (b_tag or title_div).get_text(strip=True)
        else:
            b_tag = entry.find("b")
            title = b_tag.get_text(strip=True) if b_tag else ""

        title = self._clean_title(title)
        if not title or len(title) < 10 or self._skip(title, seen_titles):
            return None
        seen_titles.add(title.lower())

        authors = self._extract_authors_from_list_group(entry, title)
        link = self._extract_openreview_link(entry)

        return self._make_paper_entry(
            title=title, authors=authors[:5], abstract="",
            url=link or source_url, conference="SaTML", year=year,
        )

    def _parse_paper_list_entry(self, li, source_url: str, year: int, seen_titles: set) -> dict:
        """解析 2025 风格 <li class="paper-item">。"""
        title_tag = li.find("em", class_="paper-title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        title = self._clean_title(title)
        if not title or len(title) < 10 or self._skip(title, seen_titles):
            return None
        seen_titles.add(title.lower())

        # 作者：在 title <em> 之后的文本
        authors = []
        full_text = li.get_text(separator=" ", strip=True)
        if title_tag:
            author_text = full_text.replace(title_tag.get_text(strip=True), "", 1).strip()
            author_text = re.sub(r'(📃|📚|📌|Abstract|Arxiv|Group\s*\d+)', '', author_text).strip()
            if author_text:
                authors = [a.strip() for a in re.split(r'[,;]', author_text)
                           if a.strip() and len(a.strip()) > 2][:10]

        # 摘要：<blockquote class="paper-abstract">
        abstract = ""
        bq = li.find("blockquote", class_="paper-abstract")
        if bq:
            abstract = bq.get_text(strip=True)

        # 链接：Arxiv 或 OpenReview
        link = ""
        for a in li.find_all("a"):
            href = a.get("href", "")
            if "arxiv.org" in href or "openreview.net" in href:
                link = href
                break

        return self._make_paper_entry(
            title=title, authors=authors[:5], abstract=abstract,
            url=link or source_url, conference="SaTML", year=year,
        )

    def _parse_block_triples(self, blocks, soup, source_url: str, year: int) -> list:
        """解析 2026 风格 <div class="block"> 三元组。

        结构: 每3个 block 为一组:
          Block 0: <strong>Title</strong>
          Block 1: Author1, Author2, ...
          Block 2: 按钮(Abstract/Arxiv/Group)
        摘要在隐藏的 <div id="abstract-rN"> 中。
        """
        papers = []
        seen = set()
        i = 0
        while i + 2 < len(blocks):
            title_block = blocks[i]
            author_block = blocks[i + 1]
            button_block = blocks[i + 2]

            # 标题在 <strong> 中
            strong = title_block.find("strong")
            if not strong:
                i += 1
                continue
            title = self._clean_title(strong.get_text(strip=True))
            if not title or len(title) < 10 or self._skip(title, seen):
                i += 3
                continue
            seen.add(title.lower())

            # 作者
            authors = []
            author_text = author_block.get_text(strip=True)
            if author_text:
                authors = [a.strip() for a in re.split(r'[,;]', author_text)
                           if a.strip() and len(a.strip()) > 2][:10]

            # 摘要：查找对应的 hidden div
            # onclick 调用 toggleAbstract('r1')，但 div id 是 abstract-r1
            abstract = ""
            abs_id = None
            for btn in button_block.find_all("button"):
                onclick = btn.get("onclick", "")
                m = re.search(r"toggleAbstract\('([^']+)'\)", onclick)
                if m:
                    abs_id = m.group(1)
                    break
            if abs_id:
                abstract_div = soup.find("div", id=f"abstract-{abs_id}")
                if not abstract_div:
                    abstract_div = soup.find("div", id=abs_id)
                if abstract_div:
                    abstract = abstract_div.get_text(strip=True)

            # 链接：Arxiv
            link = ""
            for a in button_block.find_all("a"):
                href = a.get("href", "")
                if "arxiv.org" in href:
                    link = href
                    break
                if "openreview.net" in href:
                    link = href
                    break

            papers.append(self._make_paper_entry(
                title=title, authors=authors[:5], abstract=abstract,
                url=link or source_url, conference="SaTML", year=year,
            ))
            i += 3

        return papers

    def _parse_generic_entry(self, entry, source_url: str, year: int, seen_titles: set) -> dict:
        """通用兜底解析: <li> 或 <p> 中的论文。"""
        text = entry.get_text(separator=" ", strip=True)
        if not text or len(text) < 15:
            return None

        title_tag = entry.find("b") or entry.find("strong") or entry.find("em")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = ""
            for a in entry.find_all("a"):
                href = a.get("href", "")
                if "openreview" in href or "arxiv" in href:
                    link = href
                    break
                if not link and href:
                    link = href
        else:
            title = text
            link = ""

        title = self._clean_title(title)
        if not title or len(title) < 10 or self._skip(title, seen_titles):
            return None
        seen_titles.add(title.lower())

        authors = []
        full_text = entry.get_text(separator=" ", strip=True)
        author_text = full_text.replace(title, "", 1).strip()
        author_text = re.sub(r'\b(OpenReview|Arxiv|Abstract|Group\s*\d+)\b', '', author_text).strip()
        if author_text and len(author_text) > 3:
            authors = [a.strip() for a in re.split(r'[,;]', author_text)
                       if a.strip() and len(a.strip()) > 2][:10]

        if link and not link.startswith("http"):
            link = f"{self.config['urls']['base']}/{link.lstrip('/')}"

        return self._make_paper_entry(
            title=title, authors=authors[:5], abstract="",
            url=link or source_url, conference="SaTML", year=year,
        )

    def _extract_authors_from_list_group(self, entry, title: str) -> list:
        """从 2023 风格 list-group-item 中提取作者。"""
        authors = []
        content_div = entry.find("div", class_="ms-2")
        if content_div:
            fw_bold = content_div.find("div", class_="fw-bold")
            if fw_bold:
                full_text = content_div.get_text(separator=" ", strip=True)
                title_text = fw_bold.get_text(strip=True)
                author_text = full_text.replace(title_text, "", 1).strip()
                if author_text:
                    authors = [a.strip() for a in author_text.split(",")
                               if a.strip() and len(a.strip()) > 2][:10]
        return authors

    def _extract_openreview_link(self, entry) -> str:
        """从 list-group-item 中提取 OpenReview 链接。"""
        for a in entry.find_all("a"):
            href = a.get("href", "")
            if "openreview.net" in href or "forum" in href:
                return href
        return ""

    def _clean_title(self, title: str) -> str:
        """清理标题: 移除序号前缀等。"""
        title = re.sub(r'^\d+[\.\)]\s*', '', title)
        title = re.sub(r'^(paper|title)\s*[:\-]\s*', '', title, flags=re.I)
        return title.strip()

    def _skip(self, title: str, seen_titles: set) -> bool:
        """判断是否应跳过（重复或非论文条目）。"""
        lower = title.lower()
        if lower in seen_titles:
            return True
        skip_words = ['accepted papers', 'program', 'committee', 'organizing',
                       'sponsor', 'call for papers', 'contact', 'home', 'submission',
                       'registration', 'travel', 'venue']
        return any(skip in lower for skip in skip_words)

    # 兼容旧代码
    _is_non_paper = _skip