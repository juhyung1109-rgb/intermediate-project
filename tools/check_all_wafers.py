import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('web/data_cumulative_all.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('{')
ridx = text.rfind('}')
data = json.loads(text[idx:ridx+1])

details = data.get('wafer_details', {})
print('Total wafer_details:', len(details))

missing_shap = 0
has_shap = 0
for wid, d in details.items():
    if not d.get('shap_waterfall'):
        missing_shap += 1
    else:
        has_shap += 1

print(f"Details with shap_waterfall: {has_shap}, missing shap_waterfall: {missing_shap}")

wafers = data.get('wafers', [])
print('Total wafers in data:', len(wafers))
missing_in_details = [w['sample_id'] for w in wafers if str(w['sample_id']) not in details]
print('Wafers missing in wafer_details:', len(missing_in_details))
if missing_in_details:
    print('Sample missing sids:', missing_in_details[:10])
