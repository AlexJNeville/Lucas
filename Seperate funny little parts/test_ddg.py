from ddgs import DDGS

def web_search(query):
    """Searches the web for real-time information, news, and research."""
    print("Searching...")
    with DDGS() as ddgs:
        search_results = [r for r in ddgs.text(query, max_results=5)]
        for x in range(0,len(search_results)):
            print(search_results[x]['body'])

res = input("")
web_search(res)
