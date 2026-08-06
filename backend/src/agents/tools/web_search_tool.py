"""
Web Search Tool - Tavily API Wrapper
Provides real-time web search capability for external information
like live exchange rates, current tax updates, market news, etc.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.infrastructure.logging import logger


class SearchResult(BaseModel):
    """Single search result from Tavily."""
    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the source")
    content: str = Field(..., description="Snippet/content from the source")
    score: Optional[float] = Field(default=None, description="Relevance score")


class WebSearchResponse(BaseModel):
    """Structured response from web search."""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list)
    answer: Optional[str] = Field(default=None, description="AI-generated answer summary")
    

class TavilySearchTool:
    """
    Web Search Tool powered by Tavily API.
    Fetches real-time external information unavailable in internal database.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily Search Tool.
        
        Args:
            api_key: Tavily API key (defaults to environment variable)
        """
        self.api_key = api_key
        self._client = None
        
    def _lazy_load_client(self):
        """Lazy load Tavily client to avoid import errors if not installed."""
        if self._client is None:
            try:
                from tavily import TavilyClient
                
                # Get API key from config if not provided
                if not self.api_key:
                    from src.infrastructure.config import config
                    self.api_key = config.env.TAVILY_API_KEY
                
                if not self.api_key:
                    logger.warning("TAVILY_API_KEY not set - web search will be unavailable")
                    return False
                
                self._client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily Search Tool initialized successfully")
                return True
                
            except ImportError:
                logger.warning("tavily-python package not installed. Install with: pip install tavily-python")
                return False
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {str(e)}")
                return False
        
        return True

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
        search_depth: str = "basic"
    ) -> WebSearchResponse:
        """
        Performs web search using Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default 5)
            include_answer: Whether to include AI-generated answer summary
            search_depth: "basic" or "advanced" search depth
            
        Returns:
            WebSearchResponse with results and optional answer
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return WebSearchResponse(query=query, results=[])
        
        if not self._lazy_load_client():
            logger.error("Tavily client not available - returning empty results")
            return WebSearchResponse(
                query=query,
                results=[],
                answer="Web search is currently unavailable. Please check TAVILY_API_KEY configuration."
            )
        
        try:
            logger.info(f"Performing Tavily search: '{query}' (depth={search_depth}, max_results={max_results})")
            
            response = self._client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer
            )
            
            # Parse results
            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score")
                ))
            
            answer = response.get("answer") if include_answer else None
            
            logger.info(f"Tavily search returned {len(results)} results")
            
            return WebSearchResponse(
                query=query,
                results=results,
                answer=answer
            )
            
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return WebSearchResponse(
                query=query,
                results=[],
                answer=f"Search error: {str(e)}"
            )

    def format_results_as_markdown(self, response: WebSearchResponse) -> str:
        """
        Formats search results into clean markdown text for LLM context injection.
        
        Args:
            response: WebSearchResponse to format
            
        Returns:
            Markdown-formatted string with results
        """
        if not response.results and not response.answer:
            return f"**Search Query:** {response.query}\n\nNo results found."
        
        md_parts = [f"**Search Query:** {response.query}\n"]
        
        # Add AI answer if available
        if response.answer:
            md_parts.append(f"**Summary Answer:**\n{response.answer}\n")
        
        # Add individual results
        if response.results:
            md_parts.append("**Search Results:**\n")
            for i, result in enumerate(response.results, 1):
                md_parts.append(f"{i}. **{result.title}**")
                md_parts.append(f"   - URL: {result.url}")
                md_parts.append(f"   - Content: {result.content}\n")
        
        return "\n".join(md_parts)

    async def search_async(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
        search_depth: str = "basic"
    ) -> WebSearchResponse:
        """
        Async version of search (runs in thread pool to avoid blocking).
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            include_answer: Whether to include AI-generated answer
            search_depth: "basic" or "advanced"
            
        Returns:
            WebSearchResponse with results
        """
        import asyncio
        return await asyncio.to_thread(
            self.search,
            query,
            max_results,
            include_answer,
            search_depth
        )


# Singleton instance
web_search_tool = TavilySearchTool()
