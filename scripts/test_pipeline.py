"""
测试脚本。
验证关键词筛选、数据合并去重和 README 生成流程的正确性。
"""

import sys
import os
import json
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scripts.filter.keyword_filter import is_security_related, get_matched_keywords
from scripts.storage.data_store import merge_papers, compute_stats, _dedup_key


def test_keyword_filter():
    """测试关键词筛选器。"""
    print("=== Testing Keyword Filter ===")

    # 应匹配
    assert is_security_related("Adversarial Attacks on Neural Networks")
    assert is_security_related("Backdoor Attacks in Federated Learning")
    assert is_security_related("Jailbreaking Large Language Models")
    assert is_security_related("A Study on Differential Privacy", "")
    assert is_security_related("Watermarking Deep Learning Models")

    # 不应匹配
    assert not is_security_related("Efficient Training of Transformer Models")
    assert not is_security_related("Image Classification with CNNs")
    assert not is_security_related("Natural Language Understanding Benchmarks")

    # 匹配关键词
    kws = get_matched_keywords("Adversarial Examples and Backdoor Attacks")
    assert "adversarial" in kws
    assert "backdoor" in kws

    print("  ✅ All keyword filter tests passed!\n")


def test_data_merge():
    """测试数据合并去重。"""
    print("=== Testing Data Merge & Dedup ===")

    existing = [
        {"title": "Paper A", "authors": ["Alice"], "conference": "S&P", "year": 2024},
        {"title": "Paper B", "authors": ["Bob"], "conference": "CCS", "year": 2024},
    ]

    new_papers = [
        {"title": "Paper A", "authors": ["Alice"], "conference": "S&P", "year": 2024},  # 重复
        {"title": "Paper C", "authors": ["Charlie"], "conference": "NDSS", "year": 2024},  # 新增
    ]

    merged, new_count = merge_papers(existing, new_papers)
    assert len(merged) == 3, f"Expected 3, got {len(merged)}"
    assert new_count == 1, f"Expected 1 new, got {new_count}"

    print("  ✅ All merge/dedup tests passed!\n")


def test_stats():
    """测试统计计算。"""
    print("=== Testing Stats Computation ===")

    papers = [
        {"conference": "S&P", "year": 2024},
        {"conference": "S&P", "year": 2024},
        {"conference": "NeurIPS", "year": 2024},
        {"conference": "NeurIPS", "year": 2025},
    ]

    stats = compute_stats(papers)
    assert stats["total_papers"] == 4
    assert stats["by_conference"]["S&P"] == 2
    assert stats["by_conference"]["NeurIPS"] == 2
    assert stats["by_year"]["2024"] == 3
    assert stats["by_year"]["2025"] == 1

    print("  ✅ All stats tests passed!\n")


def test_readme_generation():
    """测试 README 生成。"""
    print("=== Testing README Generation ===")

    from scripts.generators.readme_generator import _generate_papers_table, _generate_stats, _replace_section

    # 测试表格生成
    papers = [
        {
            "title": "Adversarial Attack Test",
            "authors": ["Alice", "Bob", "Charlie", "David"],
            "conference": "S&P",
            "year": 2024,
            "url": "https://example.com",
        },
    ]
    table = _generate_papers_table(papers)
    assert "Adversarial Attack Test" in table
    assert "S&P" in table
    assert "et al." in table

    # 测试统计生成
    stats = {"total_papers": 10, "by_conference": {"S&P": 5}, "by_year": {"2024": 10}}
    stats_md = _generate_stats(stats, "2024-01-01T00:00:00")
    assert "10" in stats_md
    assert "S&P" in stats_md

    # 测试 section 替换
    text = "<!-- PAPERS_TABLE_START -->\nold content\n<!-- PAPERS_TABLE_END -->"
    result = _replace_section(text, "PAPERS_TABLE_START", "PAPERS_TABLE_END", "new content")
    assert "new content" in result
    assert "old content" not in result

    print("  ✅ All README generation tests passed!\n")


def main():
    print("\n🧪 SecAI_Radar Test Suite\n")

    test_keyword_filter()
    test_data_merge()
    test_stats()
    test_readme_generation()

    print("🎉 All tests passed!")


if __name__ == "__main__":
    main()
