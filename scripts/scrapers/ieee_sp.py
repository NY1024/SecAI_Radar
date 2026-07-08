"""
IEEE S&P (Oakland) Accepted Papers 抓取器。
页面结构: HTML 表格或 div 列表，含论文标题和作者。
"""

import re
from scripts.scrapers.base import BaseScraper


class IEEESecurityPrivacyScraper(BaseScraper):
    """IEEE S&P accepted papers 页面抓取器。"""

    def scrape(self, year: int) -> list:
        url = self.config.get("year_template", "").format(year=year)
        if not url:
            url = self.config["urls"]["accepted"]

        html = self._fetch(url)
        if not html:
            return []

        soup = self._parse_html(html)
        papers = []

        # S&P 页面通常用 <div> 或 <p> 列出论文
        # 尝试多种选择器
        entries = soup.select("div.paper, div.accepted-paper, li.paper, p")
        if not entries:
            # 回退: 查找所有包含作者模式的文本块
            entries = soup.find_all(["div", "p", "li"])

        for entry in entries:
            text = entry.get_text(separator=" ", strip=True)
            if not text or len(text) < 20:
                continue

            # 尝试分离标题和作者
            # S&P 格式常见: "Title. Authors" 或 "Title\nAuthors"
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if len(lines) >= 2:
                title = lines[0]
                authors = lines[1] if len(lines) > 1 else ""
            else:
                # 尝试按句号或逗号分割
                parts = re.split(r'[.]', text, maxsplit=1)
                title = parts[0].strip()
                authors = parts[1].strip() if len(parts) > 1 else ""

            if title and len(title) > 10:
                papers.append(self._make_paper_entry(
                    title=title,
                    authors=[a.strip() for a in re.split(r'[,;]', authors) if a.strip()],
                    abstract="",
                    url=url,
                    conference="S&P",
                    year=year,
                ))

        return papers
