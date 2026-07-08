"""
USENIX Security Technical Sessions 抓取器。
页面结构: 按 session 分组的论文列表，含标题、作者、链接。
"""

import re
from scripts.scrapers.base import BaseScraper


class USENIXSecurityScraper(BaseScraper):
    """USENIX Security accepted papers 抓取器。"""

    def scrape(self, year: int) -> list:
        yy = str(year)[-2:]
        url = self.config.get("year_template", "").format(yy=yy)
        if not url:
            url = self.config["urls"]["accepted"]

        html = self._fetch(url)
        if not html:
            return []

        soup = self._parse_html(html)
        papers = []

        # USENIX 页面结构: <div class="paper"> 内含 <h2>/<a> 标题和作者列表
        entries = soup.select("div.paper, div.session-paper, article")
        if not entries:
            entries = soup.find_all("div", class_=re.compile(r"paper|session"))

        for entry in entries:
            # 标题
            title_tag = entry.find(["h2", "h3", "h4", "a"])
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            # 作者
            authors_text = ""
            auth_tag = entry.find("p", class_=re.compile(r"author|speaker"))
            if auth_tag:
                authors_text = auth_tag.get_text(strip=True)
            else:
                # 尝试从文本中提取
                text = entry.get_text(separator="\n", strip=True)
                lines = [l for l in text.split("\n") if l.strip()]
                if len(lines) > 1:
                    authors_text = lines[1]

            # 链接
            link = ""
            a_tag = entry.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                if href.startswith("/"):
                    link = f"https://www.usenix.org{href}"
                else:
                    link = href

            if title and len(title) > 10:
                papers.append(self._make_paper_entry(
                    title=title,
                    authors=[a.strip() for a in re.split(r'[,;]', authors_text) if a.strip()],
                    abstract="",
                    url=link or url,
                    conference="USENIX Security",
                    year=year,
                ))

        return papers
