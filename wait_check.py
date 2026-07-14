import time, os
print("Waiting 180s for cold start...", flush=True)
time.sleep(180)
if os.path.exists('test_health2_output.txt'):
    f = open('test_health2_output.txt', 'r', encoding='utf-8')
    content = f.read()
    print(f"Contents: {content}", flush=True)
else:
    print("File not found yet", flush=True)