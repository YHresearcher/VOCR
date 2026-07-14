import urllib.request
import json
import time

print("Hitting health endpoint (cold start may take 60-90s)...")
start = time.time()
try:
    r = urllib.request.urlopen(
        'https://yhresearcher--vietocr-service-fastapi-app-ocrservice-health.modal.run',
        timeout=120
    )
    data = json.loads(r.read().decode())
    elapsed = time.time() - start
    print(f"Response ({elapsed:.1f}s): {json.dumps(data, indent=2)}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Error ({elapsed:.1f}s): {e}")