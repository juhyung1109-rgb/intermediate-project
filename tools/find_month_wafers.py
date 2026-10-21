import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('web/data_cumulative_all.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('{')
ridx = text.rfind('}')
data = json.loads(text[idx:ridx+1])
wafers = data['wafers']

months = sorted(list(set(w.get('month') or w.get('timestamp', '')[:7] for w in wafers)))
print('All months in data:', months)

for m in months:
    m_wafers = [w for w in wafers if (w.get('month') or w.get('timestamp', '')[:7]) == m]
    defects = [w for w in m_wafers if w.get('actual_label') == 1]
    normals = [w for w in m_wafers if w.get('actual_label') == 0]
    defects.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
    normals.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
    top_d = [f"#{w['sample_id']} ({(w['risk_score']*100):.2f}%)" for w in defects[:2]]
    top_n = [f"#{w['sample_id']} ({(w['risk_score']*100):.2f}%)" for w in normals[:2]]
    print(f"Month {m} (Total: {len(m_wafers)}, Defects: {len(defects)}): Top TP: {top_d}, Top FP/Normal: {top_n}")
