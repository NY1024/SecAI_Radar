"""
ACM CCS Accepted Papers 抓取器。
页面结构: HTML 列表或表格，含标题和作者。
"""

import re
from scripts.scrapers.base import BaseScraper


class ACMCCSScraper(BaseScraper):
    """ACM CCS accepted papers 抓取器。"""

    def scrape(self, year: int) -> list:
        url = self.config.get("year_template", "").format(year=year)
        if not url:
            url = self.config["urls"]["accepted"]

        html = self._fetch(url)
        if not html:
            return []

        soup = self._parse_html(html)
        papers = []

        entries = soup.select("div.paper, li.paper, .accepted-paper, tr")
        if not entries:
            entries = soup.find_all(["li", "div", "p"])

        for entry in entries:
            text = entry.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines or len(lines[0]) < 10:
                continue

            title = lines[0]
            authors = lines[1] if len(lines) > 1 else ""

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
                    conference="CCS",
                    year=year,
                ))

        return papers
