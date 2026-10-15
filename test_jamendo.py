import json
import urllib.parse
import urllib.request

CLIENT_ID = "ef3920b9"

params = urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "format": "json",
    "limit": 5,
    "search": "jazz",
})
url = "https://api.jamendo.com/v3.0/tracks/?" + params

with urllib.request.urlopen(url, timeout=15) as response:
    data = json.loads(response.read().decode("utf-8"))

print("Статус:", data.get("headers", {}).get("status"))
for track in data.get("results", []):
    print(track.get("artist_name"), "-", track.get("name"))
    print("    ", track.get("audio"))