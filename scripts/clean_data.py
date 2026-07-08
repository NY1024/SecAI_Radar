"""
数据清洗脚本。
对 papers.json 中已有的所有论文统一应用 AI 安全关键词筛选，
移除不符合 AI 安全 scope 的论文（主要是安全四大中非 AI 安全的论文）。
同时为保留的论文补充 matched_keywords 字段。
"""

import sys
import os
import json
import logging
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.config.conferences import CONFERENCES
from scripts.storage.data_store import load_papers, save_papers
from scripts.generators.readme_generator import generate_readme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CleanData")


def main():
    data = load_papers()
    papers = data.get("papers", [])
    logger.info(f"Loaded {len(papers)} papers from database")

    before_by_conf = Counter(p.get("conference", "") for p in papers)

    kept_papers = []
    removed_count = 0
    for paper in papers:
        conf = paper.get("conference", "")
        conf_config = CONFERENCES.get(conf, {})
        # always_in_scope 的会议（如 SaTML）所有论文都在 AI 安全 scope 内，跳过筛选
        if conf_config.get("always_in_scope", False):
            if "matched_keywords" not in paper or not paper["matched_keywords"]:
                paper["matched_keywords"] = ["always_in_scope"]
            kept_papers.append(paper)
            continue

        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        if is_security_related(title, abstract):
            # 确保有 matched_keywords 字段
            if "matched_keywords" not in paper or not paper["matched_keywords"]:
                paper["matched_keywords"] = get_matched_keywords(title, abstract)
            kept_papers.append(paper)
        else:
            removed_count += 1

    after_by_conf = Counter(p.get("conference", "") for p in kept_papers)

    logger.info(f"Kept {len(kept_papers)} papers, removed {removed_count}")

    # 打印清洗报告
    print("\n" + "=" * 70)
    print("Data Cleaning Report")
    print("=" * 70)
    print(f"Before: {len(papers)} papers")
    print(f"After:  {len(kept_papers)} papers")
    print(f"Removed: {removed_count} papers")
    print()

    print(f"{'Conference':<20} {'Before':>8} {'After':>8} {'Removed':>8}")
    print("-" * 50)
    for conf in sorted(before_by_conf.keys(), key=lambda c: -before_by_conf[c]):
        before = before_by_conf[conf]
        after = after_by_conf.get(conf, 0)
        removed = before - after
        print(f"{conf:<20} {before:>8} {after:>8} {removed:>8}")

    print("=" * 70)

    # 保存清洗后的数据
    data["papers"] = kept_papers
    save_papers(data)

    # 更新 README
    generate_readme()
    logger.info(f"Data cleaned. {len(kept_papers)} papers remain. README updated.")


if __name__ == "__main__":
    main()
