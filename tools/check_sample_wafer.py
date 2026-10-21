import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('web/data_cumulative_all.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('{')
ridx = text.rfind('}')
data = json.loads(text[idx:ridx+1])

wafers = data['wafers']
sample_w = wafers[0]
print('Sample wafer structure in data.wafers:', json.dumps(sample_w, ensure_ascii=False, indent=2))
