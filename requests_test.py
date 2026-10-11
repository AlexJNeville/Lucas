import requests

response = requests.get("https://www.bing.com/search?q=southampton+vs+Arsenal")
data = response
print(data)
