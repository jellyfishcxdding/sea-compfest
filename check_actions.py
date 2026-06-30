import urllib.request
import json

url = "https://api.github.com/repos/jellyfishcxdding/sea-compfest/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        if not data.get('workflow_runs'):
            print("No workflow runs found.")
        else:
            for run in data['workflow_runs'][:3]:
                print(f"Name: {run['name']} | Status: {run['status']} | Conclusion: {run['conclusion']}")
except Exception as e:
    print("Error:", e)
