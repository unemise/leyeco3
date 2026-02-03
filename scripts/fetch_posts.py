import urllib.request, json

for param in ['', '?in_ph=1']:
    url = 'http://127.0.0.1:5000/api/posts' + param
    j = json.loads(urllib.request.urlopen(url).read())
    print(param or 'all', '->', len(j))
    print(j[:2])
