import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('web/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Pattern for the simulation ingest button block
pattern = r'<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">\s*<span style="font-size:0.78rem; color:#64748b; font-weight:600;">📥 시뮬레이션 인제스트:</span>[\s\S]*?<span>🔄 리셋</span>\s*</button>\s*</div>'

matches = list(re.finditer(pattern, html))
print(f"Found {len(matches)} simulation ingest blocks in index.html")

new_html = re.sub(pattern, '', html)

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Removed all simulation ingest button blocks from card headers!")
