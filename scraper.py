import urllib.request
import re
import json

def get_unsplash_id(query):
    try:
        url = 'https://unsplash.com/s/photos/' + query
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        match = re.search(r'itemprop="contentUrl" content="https://images\.unsplash\.com/photo-([a-zA-Z0-9-]+)\?', html)
        if match:
            return "photo-" + match.group(1)
            
        return 'Not found'
    except Exception as e:
        return str(e)

queries = ['motorcycle-helmet', 'dash-cam', 'motor-oil-bottle', 'yoga-mat', 'tennis-racket-isolated', 'vitamin-bottle', 'basketball-ball', 'computer-mouse', 'gaming-headset', 'mechanical-keyboard', 'skincare-serum-bottle', 'perfume-bottle']
results = {}
for q in queries:
    res = get_unsplash_id(q)
    results[q] = res
    print(f"{q}: {res}")

with open('scraped_ids.json', 'w') as f:
    json.dump(results, f)
