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
    """生成中英文双语 Markdown 表格，带目录导航和分组。"""
    if not papers:
        return ("No data yet. Run `python scripts/main.py --all` or wait for GitHub Actions. / "
                "暂无数据。请运行 `python scripts/main.py --all` 或等待 GitHub Actions 自动执行。")

    # 按年份降序排序
    sorted_papers = sorted(
        papers,
        key=lambda p: (p.get("year", 0), p.get("conference", "")),
        reverse=True,
    )

    # 按年份 → 会议分组
    from collections import OrderedDict
    grouped = OrderedDict()
    for p in sorted_papers:
        year = p.get("year", 0)
        conf = p.get("conference", "Unknown")
        if year not in grouped:
            grouped[year] = OrderedDict()
        if conf not in grouped[year]:
            grouped[year][conf] = []
        grouped[year][conf].append(p)

    # 生成锚点 ID 的辅助函数
    def _anchor(year, conf):
        safe_conf = re.sub(r'[^a-zA-Z0-9]', '-', conf).lower()
        return f"papers-{year}-{safe_conf}"

    # === 生成目录 ===
    toc_lines = ["<details>", "<summary><b>📑 Paper Index / 论文目录</b></summary>", ""]
    for year in grouped:
        year_total = sum(len(v) for v in grouped[year].values())
        toc_lines.append(f"### {year} ({year_total} papers)")
        for conf in grouped[year]:
            count = len(grouped[year][conf])
            anchor_id = _anchor(year, conf)
            toc_lines.append(f"- [{year} {conf} ({count})](#{anchor_id})")
        toc_lines.append("")
    toc_lines.append("</details>")
    toc_lines.append("")
    toc = "\n".join(toc_lines)

    # === 生成分组表格 ===
    table_parts = [toc]
    for year in grouped:
        for conf in grouped[year]:
            conf_papers = grouped[year][conf]
            anchor_id = _anchor(year, conf)
            table_parts.append(f'<a id="{anchor_id}"></a>')
            table_parts.append(f"### {year} · {conf} ({len(conf_papers)} papers)")
            table_parts.append("")
            table_parts.append("| Year | Conference | Title | Authors | Link |")
            table_parts.append("|------|------------|-------|---------|------|")
            for p in conf_papers:
                p_year = p.get("year", "")
                p_conf = p.get("conference", "")
                title = p.get("title", "").replace("|", "\\|")
                authors = ", ".join(p.get("authors", [])[:3])
                if len(p.get("authors", [])) > 3:
                    authors += " et al."
                url = p.get("url", "")
                link = f"[📖]({url})" if url else ""
                table_parts.append(f"| {p_year} | {p_conf} | {title} | {authors} | {link} |")
            table_parts.append("")
            # 返回目录的链接
            table_parts.append("[⬆ Back to Index / 返回目录](#paper-list--论文列表)")
            table_parts.append("")

    return "\n".join(table_parts)


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