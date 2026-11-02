import urllib.request
import os

os.makedirs('assets/images', exist_ok=True)
os.makedirs('assets/audio', exist_ok=True)
os.makedirs('output', exist_ok=True)

# Let's download a few clean royalty-free images for B-roll / Product scenes
urls = {
    'scene1_hook': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1080&q=80', # Studio headphone hook
    'scene2_problem': 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=1080&q=80', # Person wearing headphone / noisy street
    'scene3_solution': 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=1080&q=80', # Close-up tech design / ANC
    'scene4_proof': 'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=1080&q=80', # Lifestyle outdoor music
    'scene5_cta': 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=1080&q=80' # Discount / buy now tech vibe
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in urls.items():
    path = f'assets/images/{name}.jpg'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        print(f"Downloaded {name}: {os.path.getsize(path)} bytes")
    except Exception as e:
        print(f"Error {name}: {e}")
