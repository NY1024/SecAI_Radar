"""
主入口脚本。
支持抓取全部/指定会议、筛选 AI 安全论文、更新数据和 README。
"""

import argparse
import logging
import sys
import os
import json

# 将项目根目录加入 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.config.conferences import CONFERENCES, YEARS
from scripts.scrapers.router import get_scraper
from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import load_papers, save_papers, merge_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SecAI_Radar")


def scrape_conference(conf_name: str, year: int) -> list:
    """抓取单个会议的论文并筛选 AI 安全相关。"""
    conf_config = CONFERENCES.get(conf_name)
    if not conf_config:
        logger.error(f"Unknown conference: {conf_name}")
        return []

    logger.info(f"Scraping {conf_name} {year}...")
    scraper = get_scraper(conf_config)
    all_papers = scraper.scrape(year)
    logger.info(f"  Total papers found: {len(all_papers)}")

    # always_in_scope 的会议（如 SaTML）所有论文都在 AI 安全 scope 内，跳过筛选
    if conf_config.get("always_in_scope", False):
        for paper in all_papers:
            paper["matched_keywords"] = ["always_in_scope"]
        logger.info(f"  All {len(all_papers)} papers kept (always_in_scope)")
        return all_papers

    # 筛选 AI 安全相关
    security_papers = []
    for paper in all_papers:
        if is_security_related(paper.get("title", ""), paper.get("abstract", "")):
            paper["matched_keywords"] = get_matched_keywords(
                paper.get("title", ""), paper.get("abstract", "")
            )
            security_papers.append(paper)

    logger.info(f"  AI security related: {len(security_papers)}")
    return security_papers


def run_scraper(conf_name=None, year=None):
    """运行抓取流程。"""
    data = load_papers()
    existing_papers = data.get("papers", [])

    new_all = []
    if conf_name:
        years = [year] if year else YEARS
        for y in years:
            new_all.extend(scrape_conference(conf_name, y))
    else:
        for name, config in CONFERENCES.items():
            for y in YEARS:
                try:
                    new_all.extend(scrape_conference(name, y))
                except Exception as e:
                    logger.error(f"Failed to scrape {name} {y}: {e}")

    # 合并去重
    merged, new_count = merge_papers(existing_papers, new_all)
    logger.info(f"Total after merge: {len(merged)} (new: {new_count})")

    data["papers"] = merged
    save_papers(data)

    # 更新 README
    generate_readme()
    logger.info("Done! README updated.")


def generate_only():
    """仅重新生成 README 和数据文件。"""
    generate_readme()
    logger.info("README regenerated from existing data.")


def main():
    parser = argparse.ArgumentParser(description="SecAI_Radar - AI Security Paper Tracker")
    parser.add_argument("--all", action="store_true", help="Scrape all conferences")
    parser.add_argument("--conference", type=str, help="Scrape specific conference (e.g. S&P, NeurIPS)")
    parser.add_argument("--year", type=int, help="Specific year")
    parser.add_argument("--generate-only", action="store_true", help="Only regenerate README from existing data")

    args = parser.parse_args()

    if args.generate_only:
        generate_only()
    elif args.all:
        run_scraper()
    elif args.conference:
        run_scraper(conf_name=args.conference, year=args.year)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
