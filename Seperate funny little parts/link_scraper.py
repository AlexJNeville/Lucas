import requests
from bs4 import BeautifulSoup

def get_nhs_condition_links():
    url = "https://www.nhs.uk/conditions/"
    # A User-Agent helps the website identify the request as coming from a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for errors
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # The conditions are usually inside <a> tags within the main content area
        links = []
        base_url = "https://www.nhs.uk"

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Filter for links that lead to condition pages
            # We avoid short links like "/conditions/" itself
            if href.startswith('/conditions/') and len(href) > 12:
                full_url = base_url + href
                if full_url not in links:  # Avoid duplicates
                    links.append(full_url)

        return sorted(links)

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Execute and print
condition_list = get_nhs_condition_links()

print(f"Found {len(condition_list)} condition links.")
for link in condition_list:
    print(f"'{link}',")
