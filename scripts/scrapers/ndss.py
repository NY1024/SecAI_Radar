"""
NDSS Accepted Papers 抓取器。
页面结构: 有序列表或表格，含标题和作者。
"""

import re
from scripts.scrapers.base import BaseScraper


class NDSSScraper(BaseScraper):
    """NDSS accepted papers 抓取器。"""

    def scrape(self, year: int) -> list:
        url = self.config.get("year_template", "").format(year=year)
        if not url:
            url = self.config["urls"]["accepted"]

        html = self._fetch(url)
        if not html:
            return []

        soup = self._parse_html(html)
        papers = []

        # NDSS 页面结构: <div class="paper"> 或 <li>
        entries = soup.select("div.paper, li.paper, tr.paper, .accepted-paper")
        if not entries:
            entries = soup.find_all("li")

        for entry in entries:
            text = entry.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue

            title = lines[0]
            authors = lines[1] if len(lines) > 1 else ""

            # 链接
            link = ""
            a_tag = entry.find("a", href=True)
            if a_tag:
                link = a_tag["href"]

            if title and len(title) > 10:
                papers.append(self._make_paper_entry(
                    title=title,
                    authors=[a.strip() for a in re.split(r'[,;]', authors) if a.strip()],
                    abstract="",
                    url=link or url,
                    conference="NDSS",
                    year=year,
                ))

        return papers
