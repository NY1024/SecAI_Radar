"""
数据存储管理。
负责加载、合并、去重和持久化论文数据。
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "papers.json")


def load_papers() -> dict:
    """加载现有论文数据。"""
    path = os.path.abspath(DATA_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"papers": [], "last_updated": None, "stats": {}}


def save_papers(data: dict):
    """保存论文数据到 JSON。"""
    path = os.path.abspath(DATA_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 更新时间戳
    data["last_updated"] = datetime.now().isoformat()

    # 更新统计
    data["stats"] = compute_stats(data.get("papers", []))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(data.get('papers', []))} papers to {path}")


def compute_stats(papers: list) -> dict:
    """计算统计数据。"""
    stats = {
        "total_papers": len(papers),
        "by_conference": {},
        "by_year": {},
    }
    for p in papers:
        conf = p.get("conference", "Unknown")
        year = p.get("year", 0)
        stats["by_conference"][conf] = stats["by_conference"].get(conf, 0) + 1
        stats["by_year"][str(year)] = stats["by_year"].get(str(year), 0) + 1
    return stats


def merge_papers(existing: list, new_papers: list) -> tuple:
    """
    合并新旧论文，去重。
    去重规则: 相同 conference + year + title(normalized) 视为同一篇。

    Returns:
        (merged_list, new_count)
    """
    seen = set()
    merged = []

    # 先加入已有论文
    for p in existing:
        key = _dedup_key(p)
        if key not in seen:
            seen.add(key)
            merged.append(p)

    new_count = 0
    for p in new_papers:
        key = _dedup_key(p)
        if key not in seen:
            seen.add(key)
            merged.append(p)
            new_count += 1

    return merged, new_count


def _dedup_key(paper: dict) -> str:
    """生成去重 key。"""
    title = paper.get("title", "").strip().lower()
    # 移除多余空格
    title = " ".join(title.split())
    return f"{paper.get('conference', '')}|{paper.get('year', '')}|{title}"
