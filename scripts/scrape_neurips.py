"""
NeurIPS 2023-2026 专用抓取脚本。
1. 从 NeurIPS 虚拟站点 JSON 获取所有论文标题、作者和摘要
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
from scripts.scrapers.neurips_virtual import NeurIPSVirtualScraper
from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import load_papers, save_papers, merge_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("NeurIPS_Scrape")


def main():
    neurips_config = CONFERENCES["NeurIPS"]
    scraper = get_scraper(neurips_config)
    assert isinstance(scraper, NeurIPSVirtualScraper), f"Expected NeurIPSVirtualScraper, got {type(scraper)}"

    data = load_papers()
    existing_papers = data.get("papers", [])

    all_new_security_papers = []

    for year in [2023, 2024, 2025, 2026]:
        logger.info(f"=== NeurIPS {year} ===")

        # Step 1: 从虚拟站点 JSON 获取所有论文（含标题、作者、摘要）
        all_papers = scraper.scrape(year)
        logger.info(f"  Total papers from NeurIPS virtual JSON: {len(all_papers)}")

        if not all_papers:
            logger.warning(f"  No papers found for NeurIPS {year} (may not be published yet)")
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
    logger.info(f"=== Merging {len(all_new_security_papers)} new NeurIPS papers into existing {len(existing_papers)} ===")
    merged, new_count = merge_papers(existing_papers, all_new_security_papers)
    logger.info(f"Total after merge: {len(merged)} (new: {new_count})")

    data["papers"] = merged
    save_papers(data)

    # Step 4: 更新 README
    generate_readme()
    logger.info("Done! README updated.")


if __name__ == "__main__":
    main()
