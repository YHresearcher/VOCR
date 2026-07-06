import urllib.request
import sys
print("Hitting health endpoint (cold start may take 90-180s)...", flush=True)
try:
    r = urllib.request.urlopen('https://yhresearcher--vietocr-service-fastapi-app-ocrservice-health.modal.run', timeout=300)
    data = r.read().decode()
    print(f"SUCCESS: {data}", flush=True)
except Exception as e:
    print(f"Error ({e})", flush=True)