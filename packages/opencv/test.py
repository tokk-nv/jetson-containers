import os
import cv2
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

img_url = 'https://raw.githubusercontent.com/dusty-nv/jetson-containers/59f840abbb99f22914a7b2471da829b3dd56122e/test/data/test_0.jpg'
img_path = 'test_0.jpg'

def download_image(url, path, retries=5, timeout=30):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        print(f"📥 Downloading {url}...")
        response = session.get(url, allow_redirects=True, timeout=timeout)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        print("✅ Downloaded image successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return False

# Download image if it doesn't exist
if not os.path.exists(img_path):
    if not download_image(img_url, img_path):
        print("⚠️ Falling back to local test image if available...")
        if not os.path.exists(img_path):
            print("🚫 No fallback image found. Exiting test.")
            exit(1)

# Load and test image with OpenCV
img = cv2.imread(img_path)
if img is None:
    print("🚫 Failed to load image with OpenCV.")
    exit(1)

print(f"✅ Image loaded: shape={img.shape}")
