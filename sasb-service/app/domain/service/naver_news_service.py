from typing import List
from ...core.http_client import HttpApiClient
from ...config.settings import settings
from ..model.sasb_dto import NewsItem

class NaverNewsService:
    """
    Service for fetching news articles from the Naver News API.
    """
    def __init__(self):
        self.api_client = HttpApiClient(
            base_url="https://openapi.naver.com",
            headers={
                "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
            },
        )

    async def search_news(self, query: str, display: int = 100, start: int = 1) -> List[NewsItem]:
        """
        Searches for news articles using a given query.

        Args:
            query: The keyword to search for.
            display: The number of results to display per page (최대 100).
            start: The starting point of the search results.

        Returns:
            A list of NewsItem objects.
        """
        params = {
            "query": query,
            "display": display,
            "start": start,
        }
        try:
            response_data = await self.api_client.get("/v1/search/news.json", params=params)
            
            # Clean and format the raw API response into NewsItem objects
            items = []
            for item in response_data.get("items", []):
                # Naver API returns HTML tags in titles and descriptions, remove them for clarity
                clean_title = item.get("title", "").replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                clean_description = item.get("description", "").replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                
                items.append(
                    NewsItem(
                        title=clean_title,
                        link=item.get("originallink") or item.get("link", ""),
                        description=clean_description,
                    )
                )
            return items
        except Exception as e:
            print(f"An error occurred while fetching Naver news: {e}")
            # Depending on the desired error handling, you might want to return an empty list or re-raise
            return [] 