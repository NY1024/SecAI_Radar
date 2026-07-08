"""
ICML 2023-2026 专用抓取脚本。
1. 从 PMLR 抓取所有论文标题和作者
2. 按关键词筛选 AI 安全相关论文
3. 对匹配的论文逐篇抓取摘要
4. 合并到 papers.json 并更新 README
"""

import sys
import os
import logging
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.config.conferences import CONFERENCES
from scripts.scrapers.router import get_scraper
from scripts.scrapers.pmlr import PMLRScraper
from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import load_papers, save_papers, merge_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ICML_Scrape")


def main():
    icml_config = CONFERENCES["ICML"]
    scraper = get_scraper(icml_config)
    assert isinstance(scraper, PMLRScraper), f"Expected PMLRScraper, got {type(scraper)}"

    data = load_papers()
    existing_papers = data.get("papers", [])

    all_new_security_papers = []

    for year in [2023, 2024, 2025, 2026]:
        logger.info(f"=== ICML {year} ===")

        # Step 1: 抓取所有论文标题和作者（不带摘要）
        all_papers = scraper.scrape(year)
        logger.info(f"  Total papers on PMLR: {len(all_papers)}")

        if not all_papers:
            continue

        # Step 2: 按标题筛选 AI 安全相关（快速筛选，不需要摘要）
        security_papers = []
        for paper in all_papers:
            title = paper.get("title", "")
            if is_security_related(title, ""):
                paper["matched_keywords"] = get_matched_keywords(title, "")
                security_papers.append(paper)

        logger.info(f"  AI security related (by title): {len(security_papers)}")

        # Step 3: 对匹配的论文逐篇抓取摘要
        logger.info(f"  Fetching abstracts for {len(security_papers)} papers...")
        for i, paper in enumerate(security_papers):
            url = paper.get("url", "")
            if url and url.endswith(".html"):
                abstract = scraper.fetch_abstract(url)
                if abstract:
                    paper["abstract"] = abstract
                    # 用摘要重新匹配关键词（更全面）
                    paper["matched_keywords"] = get_matched_keywords(
                        paper.get("title", ""), abstract
                    )
                # 限速避免被 ban
                time.sleep(0.5)
            if (i + 1) % 10 == 0:
                logger.info(f"    Progress: {i+1}/{len(security_papers)} abstracts fetched")

        logger.info(f"  Done: {len(security_papers)} security papers with abstracts for ICML {year}")
        all_new_security_papers.extend(security_papers)

    # Step 4: 合并到现有数据
    logger.info(f"=== Merging {len(all_new_security_papers)} new papers into existing {len(existing_papers)} ===")
    merged, new_count = merge_papers(existing_papers, all_new_security_papers)
    logger.info(f"Total after merge: {len(merged)} (new: {new_count})")

    data["papers"] = merged
    save_papers(data)

    # Step 5: 更新 README
    generate_readme()
    logger.info("Done! README updated.")


if __name__ == "__main__":
    main()
