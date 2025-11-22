import io
import requests
from PIL import Image

# create a tiny image in memory
img = Image.new('RGB', (20, 20), color=(255, 0, 0))
b = io.BytesIO()
img.save(b, format='JPEG')
b.seek(0)

files = {'file': ('test.jpg', b, 'image/jpeg')}
# add some form fields
data = {'rash_type': 'test_rash', 'confidence': '42.0'}

resp = requests.post('http://127.0.0.1:5000/api/scans', files=files, data=data)
print('STATUS', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
