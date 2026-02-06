from duckduckgo_search import DDGS

def search_web(query, max_results=5):
    """
    Searches DuckDuckGo and returns a summary text.
    """
    print(f"Searching web for: {query}...")
    try:
        results = DDGS().text(query, max_results=max_results)
        
        if not results:
            return None
            
        summary = "Web Search Results:\n"
        for i, r in enumerate(results):
            summary += f"{i+1}. {r['title']}: {r['body']}\n"
            
        return summary
    except Exception as e:
        print(f"Search failed: {e}")
        return None
