import requests


def web_search(query: str, num_results=5):
    """Search the web using DuckDuckGo API"""

    Args:
        query (str): Search query
        num_results (int): Number of results to return (default: 5)

    Returns:
        list: List of search results with snippet and link
    """"""
    url = f"https://ddg - api.herokuapp.com / search?query={query}&limit={num_results}"
    resp = requests.get(url)
    if resp.status_code == 200:
        return [r["snippet"] + " - " + r["link"] for r in resp.json()["results"]]
    return []


if __name__ == "__main__":
    # Test the function
    results = web_search("Python web scraping", 3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result}")