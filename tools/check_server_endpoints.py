import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server/app.py', 'r', encoding='utf-8') as f:
    py = f.read()

idx = py.find('@app.get("/api/wiki/list")')
print(py[idx:idx+1200])
