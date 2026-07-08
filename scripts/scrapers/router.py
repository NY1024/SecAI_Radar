"""
抓取器路由。
根据配置中的 scraper 类型，实例化对应的抓取器。
"""

from scripts.scrapers.base import BaseScraper
from scripts.scrapers.ieee_sp import IEEESecurityPrivacyScraper
from scripts.scrapers.usenix_sec import USENIXSecurityScraper
from scripts.scrapers.ndss import NDSSScraper
from scripts.scrapers.acm_ccs import ACMCCSScraper
from scripts.scrapers.openreview import OpenReviewScraper
from scripts.scrapers.aaai import AAAIScraper
from scripts.scrapers.cvf import CVFScraper
from scripts.scrapers.acl_anthology import ACLAnthologyScraper
from scripts.scrapers.satml import SATMLScraper
from scripts.scrapers.pmlr import PMLRScraper
from scripts.scrapers.iclr_virtual import ICLRVirtualScraper
from scripts.scrapers.neurips_virtual import NeurIPSVirtualScraper
from scripts.scrapers.dblp import DBLPScraper

# 抓取器类型映射
SCRAPER_MAP = {
    "ieee_sp": IEEESecurityPrivacyScraper,
    "acm_ccs": ACMCCSScraper,
    "usenix_sec": USENIXSecurityScraper,
    "ndss": NDSSScraper,
    "openreview": OpenReviewScraper,
    "pmlr": PMLRScraper,
    "iclr_virtual": ICLRVirtualScraper,
    "neurips_virtual": NeurIPSVirtualScraper,
    "aaai": AAAIScraper,
    "cvf": CVFScraper,
    "acl_anthology": ACLAnthologyScraper,
    "satml": SATMLScraper,
    "dblp": DBLPScraper,
}


def get_scraper(conference_config: dict) -> BaseScraper:
    """根据配置获取对应的抓取器实例。"""
    scraper_type = conference_config.get("scraper", "")
    scraper_class = SCRAPER_MAP.get(scraper_type)
    if not scraper_class:
        raise ValueError(f"Unknown scraper type: {scraper_type}")
    return scraper_class(conference_config)