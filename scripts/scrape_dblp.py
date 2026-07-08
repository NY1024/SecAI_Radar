"""
DBLP 抓取脚本（S&P, CCS, USENIX Security, NDSS, AAAI）2023-2026。

1. 从 DBLP 抓取五个会议的论文标题和作者
2. 所有会议统一应用 AI 安全关键词筛选——安全四大是综合安全会议，只有部分论文涉及 AI 安全
3. AAAI 是综合 AI 会议，同样用关键词筛选
4. 合并到 papers.json 并更新 README
"""

import sys
import os
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.config.conferences import CONFERENCES
from scripts.scrapers.router import get_scraper
from scripts.scrapers.dblp import DBLPScraper
from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import load_papers, save_papers, merge_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DBLP_Scrape")

# 抓取目标会议
TARGET_CONFERENCES = ["S&P", "CCS", "USENIX Security", "NDSS", "AAAI"]

# 抓取年份
YEARS = [2023, 2024, 2025, 2026]


def main():
    data = load_papers()
    existing_papers = data.get("papers", [])
    all_new_papers = []

    # 统计报告
    stats_report = {}

    for conf_name in TARGET_CONFERENCES:
        conf_config = CONFERENCES[conf_name]
        scraper = get_scraper(conf_config)
        assert isinstance(scraper, DBLPScraper), f"Expected DBLPScraper, got {type(scraper)}"

        stats_report[conf_name] = {}

        for year in YEARS:
            logger.info(f"=== {conf_name} {year} ===")

            all_papers = scraper.scrape(year)
            total_count = len(all_papers)
            logger.info(f"  Total papers from DBLP: {total_count}")

            if not all_papers:
                logger.warning(f"  No papers found for {conf_name} {year}")
                stats_report[conf_name][year] = {"total": 0, "kept": 0}
                continue

            # always_in_scope 的会议跳过筛选
            if conf_config.get("always_in_scope", False):
                for paper in all_papers:
                    paper["matched_keywords"] = ["always_in_scope"]
                stats_report[conf_name][year] = {"total": total_count, "kept": total_count}
                all_new_papers.extend(all_papers)
                logger.info(f"  All {total_count} papers kept (always_in_scope)")
                continue

            # 所有会议统一按 AI 安全关键词筛选（DBLP 无摘要，只用标题）
            kept_papers = []
            for paper in all_papers:
                title = paper.get("title", "")
                abstract = paper.get("abstract", "")
                if is_security_related(title, abstract):
                    paper["matched_keywords"] = get_matched_keywords(title, abstract)
                    kept_papers.append(paper)
            logger.info(f"  After keyword filter: {len(kept_papers)} (filtered out {total_count - len(kept_papers)})")
            stats_report[conf_name][year] = {"total": total_count, "kept": len(kept_papers)}
            all_new_papers.extend(kept_papers)

    # 合并到现有数据
    logger.info(f"=== Merging {len(all_new_papers)} new papers into existing {len(existing_papers)} ===")
    merged, new_count = merge_papers(existing_papers, all_new_papers)
    logger.info(f"Total after merge: {len(merged)} (new: {new_count})")

    data["papers"] = merged
    save_papers(data)

    # 更新 README
    generate_readme()
    logger.info("Done! README updated.")

    # 打印抓取报告
    print("\n" + "=" * 60)
    print("DBLP Scrape Report")
    print("=" * 60)
    grand_total = 0
    grand_kept = 0
    for conf_name in TARGET_CONFERENCES:
        print(f"\n{conf_name}:")
        for year in YEARS:
            info = stats_report[conf_name].get(year, {"total": 0, "kept": 0})
            total = info["total"]
            kept = info["kept"]
            grand_total += total
            grand_kept += kept
            print(f"  {year}: {kept}/{total} papers (keyword filtered)")
    print(f"\n{'=' * 60}")
    print(f"Grand total scraped: {grand_total}")
    print(f"Grand total kept:    {grand_kept}")
    print(f"New papers added:    {new_count}")
    print(f"Total in database:   {len(merged)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
