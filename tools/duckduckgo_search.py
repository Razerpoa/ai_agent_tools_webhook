from ddgs import DDGS
import logging

logger = logging.getLogger(__name__)

def search(query, max_results: int):
    """
    This function performs a DuckDuckGo search and returns the results.
    """
    logging.info(f"Search with query: {query}")
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(r)

    return results

