from enum import Enum
import os


class ServiceType(str, Enum):
    NEWS = "news"
    # 향후 추가될 다른 서비스들을 위해 유지
    # FINANCE = "fin"
    # ESG = "esg"
    # STOCK = "stock"
    # RATIO = "ratio"
    

# ✅ 환경 변수에서 서비스 URL 가져오기 (기본값: localhost:8002)
NEWS_SERVICE_URL = os.getenv("NEWS_SERVICE_URL", "http://localhost:8002")

SERVICE_URLS = {
    ServiceType.NEWS: NEWS_SERVICE_URL,
    # 향후 추가될 서비스들
    # ServiceType.FINANCE: os.getenv("FINANCE_SERVICE_URL"),
    # ServiceType.ESG: os.getenv("ESG_SERVICE_URL"),
    # ServiceType.STOCK: os.getenv("STOCK_SERVICE_URL"),
    # ServiceType.RATIO: os.getenv("RATIO_SERVICE_URL"),
}