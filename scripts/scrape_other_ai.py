"""
CVPR/ECCV/EMNLP/SaTML 2023-2026 抓取脚本。
1. CVPR (2023-2026) / ECCV (偶数年) - CVF Open Access, 标题筛选
2. EMNLP (2023-2025) - ACL Anthology XML, 标题+摘要筛选
3. SaTML (2023-2025) - 官网, 全部收录（安全ML专门会议）
合并到 papers.json 并更新 README
"""

import sys
import os
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.config.conferences import CONFERENCES
from scripts.scrapers.router import get_scraper
from scripts.scrapers.cvf import CVFScraper
from scripts.scrapers.acl_anthology import ACLAnthologyScraper
from scripts.scrapers.satml import SATMLScraper
from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import load_papers, save_papers, merge_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("OtherAI_Scrape")


def scrape_cvf_conf(conf_key, years):
    """抓取 CVPR 或 ECCV（CVF 抓取器），标题关键词筛选。"""
    config = CONFERENCES[conf_key]
    scraper = get_scraper(config)
    assert isinstance(scraper, CVFScraper), f"Expected CVFScraper, got {type(scraper)}"

    security_papers = []
    for year in years:
        logger.info(f"=== {conf_key} {year} ===")
        all_papers = scraper.scrape(year)
        logger.info(f"  Total papers: {len(all_papers)}")

        if not all_papers:
            continue

        # CVPR/ECCV 无摘要，只用标题筛选
        for paper in all_papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            if is_security_related(title, abstract):
                paper["matched_keywords"] = get_matched_keywords(title, abstract)
                security_papers.append(paper)

        logger.info(f"  Security related: {len([p for p in security_papers if p['year'] == year and p['conference'] == conf_key])}")

    return security_papers


def scrape_emnlp(years):
    """抓取 EMNLP（ACL Anthology XML），标题+摘要筛选。"""
    config = CONFERENCES["EMNLP"]
    scraper = get_scraper(config)
    assert isinstance(scraper, ACLAnthologyScraper), f"Expected ACLAnthologyScraper, got {type(scraper)}"

    security_papers = []
    for year in years:
        logger.info(f"=== EMNLP {year} ===")
        all_papers = scraper.scrape(year)
        logger.info(f"  Total papers: {len(all_papers)}")

        if not all_papers:
            continue

        for paper in all_papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            if is_security_related(title, abstract):
                paper["matched_keywords"] = get_matched_keywords(title, abstract)
                security_papers.append(paper)

        logger.info(f"  Security related: {len([p for p in security_papers if p['year'] == year])}")

    return security_papers


def scrape_satml(years):
    """抓取 SaTML（官网），全部收录，不需筛选。"""
    config = CONFERENCES["SaTML"]
    scraper = get_scraper(config)
    assert isinstance(scraper, SATMLScraper), f"Expected SATMLScraper, got {type(scraper)}"

    all_papers = []
    for year in years:
        logger.info(f"=== SaTML {year} ===")
        papers = scraper.scrape(year)
        logger.info(f"  Total papers: {len(papers)}")

        if not papers:
            continue

        # SaTML 是安全ML专门会议，所有论文都在 scope 内
        for paper in papers:
            paper["matched_keywords"] = ["SaTML (all papers in scope)"]
        all_papers.extend(papers)

    return all_papers


def main():
    data = load_papers()
    existing_papers = data.get("papers", [])
    all_new_papers = []

    # === CVPR (2023-2026) ===
    cvpr_years = [2023, 2024, 2025, 2026]
    cvpr_papers = scrape_cvf_conf("CVPR", cvpr_years)
    all_new_papers.extend(cvpr_papers)
    logger.info(f"CVPR total security papers: {len(cvpr_papers)}")

    # === ECCV (偶数年: 2024, 2026) ===
    eccv_years = [2024, 2026]
    eccv_papers = scrape_cvf_conf("ECCV", eccv_years)
    all_new_papers.extend(eccv_papers)
    logger.info(f"ECCV total security papers: {len(eccv_papers)}")

    # === EMNLP (2023-2025, 2026 尚未发布) ===
    emnlp_years = [2023, 2024, 2025]
    emnlp_papers = scrape_emnlp(emnlp_years)
    all_new_papers.extend(emnlp_papers)
    logger.info(f"EMNLP total security papers: {len(emnlp_papers)}")

    # === SaTML (2023-2025) ===
    satml_years = [2023, 2024, 2025]
    satml_papers = scrape_satml(satml_years)
    all_new_papers.extend(satml_papers)
    logger.info(f"SaTML total papers: {len(satml_papers)}")

    # === 合并到现有数据 ===
    logger.info(f"=== Merging {len(all_new_papers)} new papers into existing {len(existing_papers)} ===")
    merged, new_count = merge_papers(existing_papers, all_new_papers)
    logger.info(f"Total after merge: {len(merged)} (new: {new_count})")

    data["papers"] = merged
    save_papers(data)

    # === 更新 README ===
    generate_readme()
    logger.info("Done! README updated.")

    # === 汇总报告 ===
    logger.info("=" * 60)
    logger.info("SCRAPING SUMMARY")
    logger.info("=" * 60)
    for conf, papers in [("CVPR", cvpr_papers), ("ECCV", eccv_papers),
                         ("EMNLP", emnlp_papers), ("SaTML", satml_papers)]:
        by_year = {}
        for p in papers:
            y = p["year"]
            by_year[y] = by_year.get(y, 0) + 1
        year_str = ", ".join(f"{y}: {c}" for y, c in sorted(by_year.items()))
        logger.info(f"  {conf}: {len(papers)} total ({year_str})")
    logger.info(f"  Total new papers merged: {new_count}")


if __name__ == "__main__":
    main()
