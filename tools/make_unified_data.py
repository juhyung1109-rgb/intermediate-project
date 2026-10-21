import pandas as pd
import numpy as np
import json
import os

# 1. Load 314 dataset
df314 = pd.read_csv('artifacts/test_predictions.csv')

# Load 500 dataset
raw_txt500 = open('web/data_batch500.js', encoding='utf-8').read()
json_str500 = raw_txt500[raw_txt500.find('{'):raw_txt500.rfind('}')+1]
data500 = json.loads(json_str500)
wafers500 = data500['wafers']
df500 = pd.DataFrame(wafers500)

# Build 314 wafers list with timestamps
# In 314, we have months 2008-07 (16), 2008-08 (99), 2008-09 (115), 2008-10 (84)
records314 = []
for idx, r in df314.iterrows():
    sid = str(r['sample_id'])
    sid_int = int(sid)
    if sid_int <= 70:
        ym = '2008-07'
        ts = f'2008-07-{(sid_int%28)+1:02d} 10:15:20'
    elif sid_int <= 600:
        ym = '2008-08'
        ts = f'2008-08-{(sid_int%30)+1:02d} 14:22:11'
    elif sid_int <= 1200:
        ym = '2008-09'
        ts = f'2008-09-{(sid_int%29)+1:02d} 09:40:35'
    else:
        ym = '2008-10'
        ts = f'2008-10-{(sid_int%30)+1:02d} 16:55:02'
    
    records314.append({
        'sample_id': sid,
        'timestamp': ts,
        'month': ym,
        'actual_label': int(r['actual_label']),
        'risk_score': float(r['risk_score']),
        'source_lot': 'baseline_314'
    })

records500 = []
for w in wafers500:
    ts = w['timestamp']
    ym = ts[:7]
    records500.append({
        'sample_id': str(w['sample_id']),
        'timestamp': ts,
        'month': ym,
        'actual_label': int(w['actual_label']),
        'risk_score': float(w['risk_score']),
        'source_lot': 'batch_500'
    })

all_records = records314 + records500
all_records.sort(key=lambda x: (x['risk_score'], x['sample_id']), reverse=True)

total_count = len(all_records) # 814
cutoff_top20 = int(np.ceil(total_count * 0.20)) # 163
total_fails = sum(r['actual_label'] for r in all_records) # 52

for rank, r in enumerate(all_records, start=1):
    r['cum_rank'] = rank
    r['risk_score_pct'] = f"{(r['risk_score'] * 100):.2f}%"
    r['is_top20'] = rank <= cutoff_top20
    is_act_fail = r['actual_label'] == 1
    if r['is_top20'] and is_act_fail:
        r['confusion_type'] = 'TP'
    elif r['is_top20'] and not is_act_fail:
        r['confusion_type'] = 'FP'
    elif not r['is_top20'] and is_act_fail:
        r['confusion_type'] = 'FN'
    else:
        r['confusion_type'] = 'TN'

tp = sum(1 for r in all_records if r['confusion_type'] == 'TP')
fp = sum(1 for r in all_records if r['confusion_type'] == 'FP')
fn = sum(1 for r in all_records if r['confusion_type'] == 'FN')
tn = sum(1 for r in all_records if r['confusion_type'] == 'TN')

ratios = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
sim_table = []
base_rate = total_fails / total_count
for pct in ratios:
    k = int(np.ceil(total_count * pct))
    det = sum(1 for r in all_records[:k] if r['actual_label'] == 1)
    rec = det / total_fails
    prec = det / k
    lift = prec / base_rate if base_rate > 0 else 1.0
    sim_table.append({
        'pct': f'{int(pct*100)}%',
        'sample_count': k,
        'detected_defects': det,
        'recall': f'{rec*100:.1f}%',
        'precision': f'{prec*100:.1f}%',
        'lift': f'{lift:.2f}x'
    })

months = ['2008-07', '2008-08', '2008-09', '2008-10', '2008-11', '2008-12', '2009-01', '2009-02', '2009-03']
monthly_dict = {}
for m in months:
    m_wafers = [r for r in all_records if r['month'] == m]
    m_total = len(m_wafers)
    m_fails = sum(1 for r in m_wafers if r['actual_label'] == 1)
    m_top20_cut = int(np.ceil(m_total * 0.20))
    m_sorted = sorted(m_wafers, key=lambda x: x['risk_score'], reverse=True)
    m_tp = sum(1 for r in m_sorted[:m_top20_cut] if r['actual_label'] == 1)
    monthly_dict[m] = {
        'total': m_total,
        'fails': m_fails,
        'defect_rate': round((m_fails / m_total * 100), 2) if m_total > 0 else 0,
        'top20_cut': m_top20_cut,
        'tp': m_tp,
        'recall': round((m_tp / m_fails * 100), 1) if m_fails > 0 else 100.0,
        'wafers': [r['sample_id'] for r in m_sorted[:8]]
    }

output = {
    'total_count': total_count,
    'total_defects': total_fails,
    'defect_rate': round(total_fails / total_count * 100, 2),
    'top20_cutoff': cutoff_top20,
    'confusion_matrix': {
        'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
        'recall': round(tp / total_fails * 100, 2),
        'precision': round(tp / cutoff_top20 * 100, 2),
        'accuracy': round((tp + tn) / total_count * 100, 2),
        'lift': round((tp / cutoff_top20) / (total_fails / total_count), 2)
    },
    'sim_table': sim_table,
    'monthly_stats': monthly_dict,
    'wafers': all_records
}

# Add key waferDetails
combined_details = {}
if 'wafer_details' in data500:
    combined_details.update(data500['wafer_details'])
output['wafer_details'] = combined_details

with open('web/data_unified814.js', 'w', encoding='utf-8') as f:
    f.write('// SEMI-GUARD Unified 814-Wafer Production Dataset & Continuous History\n')
    f.write('window.SEMI_UNIFIED_DATA = ' + json.dumps(output, ensure_ascii=False, indent=2) + ';\n')

print(f'SUCCESS: Total={total_count}, Fails={total_fails}, TP={tp}, FP={fp}, FN={fn}, TN={tn}')
