import requests


url = 'http://127.0.0.1:8000/crgl/?url=https://losangeles.craigslist.org/search/cta'

data = requests.get(url)
print(data.text)