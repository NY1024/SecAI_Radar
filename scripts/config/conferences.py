"""
CCF-A 类（及顶级）AI 与安全会议配置。
每条配置包含会议元信息、数据来源 URL 和抓取器类型。
"""

CONFERENCES = {
    # === 安全四大 (Security Big Four) ===
    "S&P": {
        "name": "S&P",
        "full_name": "IEEE Symposium on Security and Privacy",
        "full_name_cn": "IEEE 安全与隐私研讨会",
        "ccf_rank": "A",
        "category": "security",
        "scraper": "dblp",
        "dblp_key": "sp",
        "urls": {
            "accepted": "https://sp.ieee-security.org/2025/acceptedpapers.html",
        },
        "year_template": "https://sp.ieee-security.org/{year}/acceptedpapers.html",
    },
    "CCS": {
        "name": "CCS",
        "full_name": "ACM Conference on Computer and Communications Security",
        "full_name_cn": "ACM 计算机与通信安全会议",
        "ccf_rank": "A",
        "category": "security",
        "scraper": "dblp",
        "dblp_key": "ccs",
        "urls": {
            "accepted": "https://www.sigsac.org/ccs2025/accepted-papers.html",
        },
        "year_template": "https://www.sigsac.org/ccs{year}/accepted-papers.html",
    },
    "USENIX Security": {
        "name": "USENIX Security",
        "full_name": "USENIX Security Symposium",
        "full_name_cn": "USENIX 安全研讨会",
        "ccf_rank": "A",
        "category": "security",
        "scraper": "dblp",
        "dblp_key": "uss",
        "urls": {
            "accepted": "https://www.usenix.org/conference/usenixsecurity25/technical-sessions",
        },
        "year_template": "https://www.usenix.org/conference/usenixsecurity{yy}/technical-sessions",
    },
    "NDSS": {
        "name": "NDSS",
        "full_name": "Network and Distributed System Security Symposium",
        "full_name_cn": "网络与分布式系统安全研讨会",
        "ccf_rank": "A",
        "category": "security",
        "scraper": "dblp",
        "dblp_key": "ndss",
        "urls": {
            "accepted": "https://www.ndss-symposium.org/ndss2025/accepted-papers/",
        },
        "year_template": "https://www.ndss-symposium.org/ndss{year}/accepted-papers/",
    },
    "SaTML": {
        "name": "SaTML",
        "full_name": "IEEE Secure and Trustworthy ML Conference",
        "full_name_cn": "IEEE 安全可信机器学习会议",
        "ccf_rank": None,
        "category": "security",
        "scraper": "satml",
        "always_in_scope": True,
        "urls": {
            "base": "https://satml.org",
        },
    },
    # === AI/ML 顶会 (AI/ML Top Conferences) ===
    "NeurIPS": {
        "name": "NeurIPS",
        "full_name": "Neural Information Processing Systems",
        "full_name_cn": "神经信息处理系统大会",
        "ccf_rank": "A",
        "category": "ai",
        "scraper": "neurips_virtual",
        "urls": {
            "base": "https://neurips.cc",
        },
    },
    "ICML": {
        "name": "ICML",
        "full_name": "International Conference on Machine Learning",
        "full_name_cn": "国际机器学习大会",
        "ccf_rank": "A",
        "category": "ai",
        "scraper": "pmlr",
        "urls": {
            "base": "https://proceedings.mlr.press",
        },
    },
    "ICLR": {
        "name": "ICLR",
        "full_name": "International Conference on Learning Representations",
        "full_name_cn": "国际学习表征大会",
        "ccf_rank": "A",
        "category": "ai",
        "scraper": "iclr_virtual",
        "urls": {
            "base": "https://iclr.cc",
        },
    },
    "AAAI": {
        "name": "AAAI",
        "full_name": "AAAI Conference on Artificial Intelligence",
        "full_name_cn": "AAAI 人工智能大会",
        "ccf_rank": "A",
        "category": "ai",
        "scraper": "dblp",
        "dblp_key": "aaai",
        "urls": {
            "accepted": "https://aaai.org/wp-content/uploads/2025/01/AAAI-2025-Accepted-Paper-Names.pdf",
        },
    },
    "CVPR": {
        "name": "CVPR",
        "full_name": "IEEE/CVF Conference on Computer Vision and Pattern Recognition",
        "full_name_cn": "IEEE/CVF 计算机视觉与模式识别会议",
        "ccf_rank": "A",
        "category": "ai",
        "scraper": "cvf",
        "urls": {
            "base": "https://openaccess.thecvf.com",
        },
    },
    "ECCV": {
        "name": "ECCV",
        "full_name": "European Conference on Computer Vision",
        "full_name_cn": "欧洲计算机视觉会议",
        "ccf_rank": "B",
        "category": "ai",
        "scraper": "cvf",
        "urls": {
            "base": "https://openaccess.thecvf.com",
        },
        "biennial": True,
    },
    "ACL": {
        "name": "ACL",
        "full_name": "Annual Meeting of the Association for Computational Linguistics",
        "full_name_cn": "国际计算语言学协会年会",
        "ccf_rank": "A",
        "category": "ai",
        "scraper": "acl_anthology",
        "urls": {
            "base": "https://aclanthology.org",
        },
    },
    "EMNLP": {
        "name": "EMNLP",
        "full_name": "Empirical Methods in Natural Language Processing",
        "full_name_cn": "自然语言处理经验方法会议",
        "ccf_rank": "B",
        "category": "ai",
        "scraper": "acl_anthology",
        "urls": {
            "base": "https://aclanthology.org",
        },
    },
    "COLM": {
        "name": "COLM",
        "full_name": "Conference on Language Modeling",
        "full_name_cn": "语言建模大会",
        "ccf_rank": None,
        "category": "ai",
        "scraper": "openreview",
        "urls": {
            "api": "https://api2.openreview.net/venues?id=COLM.cc",
        },
        "openreview_venue": "COLM",
    },
}

# 当前年份列表，按降序排列
YEARS = [2026, 2025, 2024, 2023]
