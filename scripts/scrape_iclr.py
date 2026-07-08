"""
ICLR 2023-2026 专用抓取脚本。
1. 从 ICLR Virtual JSON 获取所有论文标题、作者和摘要
2. 按关键词筛选 AI 安全相关论文
3. 合并到 papers.json 并更新 README
"""

import sys
import os
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.config.conferences import CONFERENCES
from scripts.scrapers.router import get_scraper
from scripts.scrapers.iclr_virtual import ICLRVirtualScraper
from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import load_papers, save_papers, merge_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ICLR_Scrape")


def main():
    iclr_config = CONFERENCES["ICLR"]
    scraper = get_scraper(iclr_config)
    assert isinstance(scraper, ICLRVirtualScraper), f"Expected ICLRVirtualScraper, got {type(scraper)}"

    data = load_papers()
    existing_papers = data.get("papers", [])

    all_new_security_papers = []

    for year in [2023, 2024, 2025, 2026]:
        logger.info(f"=== ICLR {year} ===")

        # Step 1: 抓取所有论文（JSON 一次获取，包含标题、作者、摘要）
        all_papers = scraper.scrape(year)
        logger.info(f"  Total papers from ICLR Virtual: {len(all_papers)}")

        if not all_papers:
            continue

        # Step 2: 按标题+摘要筛选 AI 安全相关
        security_papers = []
        for paper in all_papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            if is_security_related(title, abstract):
                paper["matched_keywords"] = get_matched_keywords(title, abstract)
                security_papers.append(paper)

        logger.info(f"  AI security related: {len(security_papers)}")
        all_new_security_papers.extend(security_papers)

    # Step 3: 合并到现有数据
    logger.info(f"=== Merging {len(all_new_security_papers)} new ICLR papers into existing {len(existing_papers)} ===")
    merged, new_count = merge_papers(existing_papers, all_new_security_papers)
    logger.info(f"Total after merge: {len(merged)} (new: {new_count})")

    data["papers"] = merged
    save_papers(data)

    # Step 4: 更新 README
    generate_readme()
    logger.info("Done! README updated.")


if __name__ == "__main__":
    main()
