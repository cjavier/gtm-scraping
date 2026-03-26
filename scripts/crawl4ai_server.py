"""
MCP server for Crawl4AI using FastMCP.
"""
import json
import warnings
warnings.filterwarnings("ignore")

from fastmcp import FastMCP

mcp = FastMCP("crawl4ai")


@mcp.tool()
async def crawl_webpage(url: str, include_links: bool = True) -> str:
    """Crawl a webpage and return its content as markdown."""
    from crawl4ai import AsyncWebCrawler, CacheMode

    try:
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
            if result.success:
                output = {
                    "success": True,
                    "url": url,
                    "title": result.metadata.get("title", "") if result.metadata else "",
                    "markdown": result.markdown[:50000] if result.markdown else "",
                }
            else:
                output = {"success": False, "url": url, "error": result.error_message or "Unknown error"}
        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "url": url, "error": str(e)})


@mcp.tool()
async def crawl_website(url: str, max_pages: int = 5, max_depth: int = 2) -> str:
    """Crawl multiple pages from a website starting from a URL."""
    from crawl4ai import AsyncWebCrawler, CacheMode

    try:
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
            pages = []
            if result.success:
                pages.append({
                    "url": url,
                    "title": result.metadata.get("title", "") if result.metadata else "",
                    "markdown": result.markdown[:20000] if result.markdown else "",
                })
                internal_links = []
                if result.links and "internal" in result.links:
                    internal_links = [l.get("href", "") for l in result.links["internal"][:max_pages - 1]]

                for link in internal_links[:max_pages - 1]:
                    if len(pages) >= max_pages:
                        break
                    try:
                        sub_result = await crawler.arun(url=link, cache_mode=CacheMode.BYPASS)
                        if sub_result.success:
                            pages.append({
                                "url": link,
                                "title": sub_result.metadata.get("title", "") if sub_result.metadata else "",
                                "markdown": sub_result.markdown[:20000] if sub_result.markdown else "",
                            })
                    except Exception:
                        continue

            output = {"success": True, "pages_crawled": len(pages), "pages": pages}
        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "url": url, "error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
