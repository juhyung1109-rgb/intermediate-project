import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('web/data_cumulative_all.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('{')
ridx = text.rfind('}')
data = json.loads(text[idx:ridx+1])

details = data.get('wafer_details', {})
w_sample = details.get('2050')
print('2050 sample detail:', json.dumps(w_sample, ensure_ascii=False, indent=2))
w_sample2 = details.get('2237')
print('2237 sample detail:', json.dumps(w_sample2, ensure_ascii=False, indent=2))
