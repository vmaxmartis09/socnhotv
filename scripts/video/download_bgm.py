import urllib.request
import os

# Free sound / royalty free music snippet
music_urls = [
    # Wikimedia Commons free audio samples
    "https://upload.wikimedia.org/wikipedia/commons/4/4b/Lofi_hip_hop_loop.ogg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg",
    "https://actions.google.com/sounds/v1/sports/whistle_start.ogg"
]

music_path = "assets/audio/bgm.ogg"

# Let's search for a good royalty free lofi beat loop
test_url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

try:
    req = urllib.request.Request(test_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        with open("assets/audio/bgm.mp3", "wb") as f:
            f.write(resp.read())
    print("Downloaded bgm.mp3:", os.path.getsize("assets/audio/bgm.mp3"))
except Exception as e:
    print("Could not download pixabay:", e)
