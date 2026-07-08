"""
README 生成器。
从 papers.json 读取数据，生成中英文双语 Markdown 表格替换 README 中的占位符。
"""

import json
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "papers.json")


def generate_readme():
    """读取数据，更新 README 中的论文表格和统计信息。"""
    readme_path = os.path.abspath(README_PATH)
    data_path = os.path.abspath(DATA_PATH)

    # 加载数据
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers = data.get("papers", [])
    last_updated = data.get("last_updated", "N/A")
    stats = data.get("stats", {})

    # 读取 README
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    # 生成论文表格
    table = _generate_papers_table(papers)
    readme = _replace_section(readme, "PAPERS_TABLE_START", "PAPERS_TABLE_END", table)

    # 生成统计
    stats_md = _generate_stats(stats, last_updated)
    readme = _replace_section(readme, "STATS_START", "STATS_END", stats_md)

    # 写回
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    logger.info(f"README updated with {len(papers)} papers")


def _generate_papers_table(papers: list) -> str:
    """生成中英文双语 Markdown 表格。"""
    if not papers:
        return ("No data yet. Run `python scripts/main.py --all` or wait for GitHub Actions. / "
                "暂无数据。请运行 `python scripts/main.py --all` 或等待 GitHub Actions 自动执行。")

    # 按年份降序、会议排序
    sorted_papers = sorted(
        papers,
        key=lambda p: (p.get("year", 0), p.get("conference", "")),
        reverse=True,
    )

    lines = [
        "| Year | Conference | Title | Authors | Link |",
        "|------|------------|-------|---------|------|",
    ]
    for p in sorted_papers:
        year = p.get("year", "")
        conf = p.get("conference", "")
        title = p.get("title", "").replace("|", "\\|")
        authors = ", ".join(p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += " et al."
        url = p.get("url", "")
        link = f"[📖]({url})" if url else ""
        lines.append(f"| {year} | {conf} | {title} | {authors} | {link} |")

    return "\n".join(lines)


def _generate_stats(stats: dict, last_updated: str) -> str:
    """生成中英文双语统计信息。"""
    total = stats.get("total_papers", 0)
    by_conf = stats.get("by_conference", {})
    by_year = stats.get("by_year", {})

    lines = [f"- Total papers / 总论文数: {total}"]
    lines.append(f"- Last updated / 最近更新: {last_updated}")

    if by_conf:
        conf_list = [f"{k}({v})" for k, v in sorted(by_conf.items(), key=lambda x: -x[1])]
        lines.append(f"- By conference / 各会议分布: {', '.join(conf_list)}")

    if by_year:
        year_list = [f"{k}({v})" for k, v in sorted(by_year.items(), key=lambda x: -int(x[0]))]
        lines.append(f"- By year / 各年份分布: {', '.join(year_list)}")

    return "\n".join(lines)


def _replace_section(text: str, start_marker: str, end_marker: str, content: str) -> str:
    """替换 README 中两个标记之间的内容。"""
    pattern = rf"(<!--\s*{start_marker}\s*-->)(.*?)(<!--\s*{end_marker}\s*-->)"

    def replacer(match):
        return match.group(1) + "\n" + content + "\n" + match.group(3)

    return re.sub(pattern, replacer, text, flags=re.DOTALL)
