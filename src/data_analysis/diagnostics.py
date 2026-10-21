"""Live equivalents of the legacy tools' wafer detail and drift analyses."""
import math

import numpy as np
import pandas as pd
from scipy import stats

from .validation import DataError, clean_json


def sample_diagnosis(tools, sample_id, review_ratio=None):
    from .tools import ratio_value
    if not isinstance(sample_id,str) or not sample_id.strip():
        raise DataError('sample_id는 비어 있지 않은 문자열이어야 합니다.')
    if tools.metadata['model_version'] != tools.model.version:
        raise DataError('현재 모델과 저장 결과의 버전이 달라 표본 분석을 계산할 수 없습니다.')
    ratio = ratio_value(review_ratio if review_ratio is not None else tools.metadata.get('review_ratio',.2))
    ranked=tools.frame.sort_values(['risk_score','row_id'],ascending=[False,True]).copy()
    ranked['risk_rank']=np.arange(1,len(ranked)+1)
    found=ranked.loc[ranked.sample_id.astype(str).eq(sample_id)]
    if len(found)!=1:raise DataError('선택 데이터셋과 기간에서 표본 ID를 찾을 수 없습니다.')
    row=found.iloc[0];selected=bool(row.risk_rank<=math.ceil(len(ranked)*ratio))
    actual=row.get('actual_label',np.nan)
    category=('TP' if selected else 'FN') if actual==1 else (('FP' if selected else 'TN') if actual==0 else '미확인')
    ref=tools.model.reference();sensors=[]
    for c in ref:
        values=ref[c].dropna();mean=values.mean();std=values.std(ddof=1);raw=row.get(c,np.nan)
        valid=pd.notna(raw) and pd.notna(std) and std>0
        z=float((raw-mean)/std) if valid else None
        p05,p95=values.quantile(.05),values.quantile(.95)
        outside=bool(raw<p05 or raw>p95) if pd.notna(raw) and len(values) else None
        status='결측 확인' if pd.isna(raw) else ('기준 산포 없음' if not valid else ('편차 큼' if abs(z)>=2 else ('편차 주의' if abs(z)>=1.5 else '편차 낮음')))
        sensors.append({'sensor':c,'raw_value':raw,'reference_mean':mean,'reference_median':values.median(),
            'reference_std':std,'reference_p05':p05,'reference_p95':p95,'reference_count':len(values),
            'z_score':z,'missing':pd.isna(raw),'outside_reference':outside,'status':status})
    sensors.sort(key=lambda r:abs(r['z_score']) if r['z_score'] is not None else -1,reverse=True)
    counts={k:sum(1 for s in sensors if s['status']==k) for k in ['편차 큼','편차 주의','편차 낮음','결측 확인','기준 산포 없음']}
    shap=tools.explain_sample(int(row.row_id))
    rules={
        'TP':('D01','우선 품질 검토','검토 대상으로 선택된 정답 불량 표본입니다. 검사 기록과 위험 증가 SHAP 센서의 원측정값을 우선 확인하세요.'),
        'FP':('D02','예방 점검 후보 검토','검토 대상으로 선택됐지만 정답 라벨은 정상입니다. 오탐 배경과 센서 이력을 대조하고 반복 편차가 있는지 확인하세요.'),
        'FN':('D03','누락 불량 검토','정답 불량이 현재 검토 비율에서 제외됐습니다. 놓친 표본의 공통 특성과 검토 예산·모델 보완 필요성을 확인하세요.'),
        'TN':('D04','정기 모니터링','정답 정상이며 현재 검토 비율에서 제외된 표본입니다. 센서 편차와 데이터 품질을 정기적으로 확인하세요.'),
        '미확인':('D05','정답 확인과 검토 우선순위','정답 라벨이 없어 TP·FP·FN·TN을 확정할 수 없습니다. 위험 순위를 검토 우선순위로만 사용하고 검사 결과를 확보하세요.')}
    code,title,summary=rules[category]
    checks=['센서 원본값·결측·측정 시각과 계측 기록 대조','위험 증가와 감소 SHAP을 함께 확인','여러 표본과 시간 구간에서 편차 반복 여부 확인']
    if counts['결측 확인']:checks.insert(0,f"필수 센서 {counts['결측 확인']}개의 결측 및 모델 대체 입력 여부 확인")
    positive=shap.get('risk_increase',[])[:3];negative=shap.get('risk_decrease',[])[:3]
    return clean_json({'sample_id':sample_id,'scope_count':len(ranked),'period':tools.metadata.get('period','all'),
        'review_ratio':ratio,'selected_count':math.ceil(len(ranked)*ratio),'reference_count':len(ref),
        'row':{**{c:row[c] for c in ['row_id','sample_id','risk_score','risk_rank','abnormal_sensor_count']},
               'actual_label':actual,'category':category,'selected_for_review':selected,'rank_fraction':float(row.risk_rank/len(ranked))},
        'summary':f"현재 {len(ranked)}행 중 {int(row.risk_rank)}위이며 상위 검토 {ratio:.0%} {'대상' if selected else '밖'}입니다. {summary}",
        'top_sensors':sensors[:20], 'missing_sensors':[s['sensor'] for s in sensors if s['missing']],
        'sensor_status_counts':counts,'shap':shap,
        'recommendation':{'rule_id':code,'title':title,'summary':summary,'checks':checks,
            'evidence':{'sensor_status_counts':counts,'top_deviations':sensors[:3],
                        'risk_increase':positive,'risk_decrease':negative},
            'scope':'데이터와 점검 기록의 검토 권고입니다. 제품 통과·폐기, 부품 교체, 장비 정지 여부를 자동 결정하지 않습니다.'},
        'reference_method':'학습 정상군 원본값 기준. Z=(측정값−정상 평균)/표본 표준편차(ddof=1). 중앙값과 5~95% 참고 구간은 별도로 표시합니다.',
        'note':'1.5σ·2σ는 탐색용 표시 기준이며 설비 관리 한계가 아닙니다. SHAP과 통계로 물리적 고장 원인을 단정하지 않습니다.'})


def temporal_drift(tools, direction='both', limit=20):
    from .tools import limit_value
    limit_value(limit)
    if direction not in ['all','both','upward','downward']:
        raise DataError('direction은 all, both, upward, downward 중 하나여야 합니다.')
    if 'timestamp' not in tools.frame:
        return {'status':'unavailable','reason':'측정 시각이 있어야 시간에 따른 센서 드리프트를 계산합니다.','rows':[]}
    frame=tools.frame.copy();frame['_time']=pd.to_datetime(frame.timestamp,format='mixed',utc=True)
    # Timestamp ties are averaged: input row order cannot create a time trend.
    sensors=[c for c in tools.model.features if c in frame]
    daily=frame.groupby('_time')[sensors].mean().sort_index()
    if len(daily)<4:return {'status':'unavailable','reason':'서로 다른 측정 시각이 4개 이상 필요합니다.','rows':[]}
    elapsed=(daily.index-daily.index.min()).total_seconds().to_numpy()/86400
    span=float(elapsed.max());rows=[]
    for c in sensors:
        y=daily[c];mask=y.notna();valid=y[mask].to_numpy();x=elapsed[mask]
        if len(valid)<4 or x[-1]<=x[0] or np.std(valid,ddof=1)<=0:continue
        std=float(np.std(valid,ddof=1));reg=stats.linregress(x,valid);tau=float(stats.kendalltau(x,valid).statistic)
        # Preserve early/late mean comparison without the legacy overlap of 100-row windows.
        window=min(100,len(valid)//2);start=float(valid[:window].mean());end=float(valid[-window:].mean())
        norm=float(reg.slope*(x[-1]-x[0])/std);shift=(end-start)/std
        index=abs(norm)*math.sqrt(abs(float(reg.rvalue)*tau))
        kind='upward' if norm>=1 and shift>=.7 and tau>0 else ('downward' if norm<=-1 and shift<=-.7 and tau<0 else 'flat')
        rows.append({'sensor':c,'direction':kind,'drift_index':index,'normalized_drift_sigma':norm,
            'baseline_shift_sigma':shift,'pearson_r':float(reg.rvalue),'kendall_tau':tau,
            'slope_per_day':float(reg.slope),'start_mean':start,'end_mean':end,'window_count':window,
            'valid_time_count':len(valid),'missing_rows':int(frame[c].isna().sum())})
    rows.sort(key=lambda r:r['drift_index'],reverse=True)
    chosen=[r for r in rows if direction=='all' or (r['direction']!='flat' if direction=='both' else r['direction']==direction)][:limit]
    series=[]
    for r in chosen[:3]:
        monthly=frame.assign(period=frame['_time'].dt.strftime('%Y-%m')).groupby('period')[r['sensor']].agg(['mean','count'])
        series.append({'sensor':r['sensor'],'rows':monthly.reset_index().to_dict('records')})
    return clean_json({'status':'available','scope_count':len(frame),'time_count':len(daily),'span_days':span,
        'analyzed_sensors':len(rows),'direction_counts':{k:sum(r['direction']==k for r in rows) for k in ['upward','downward','flat']},
        'rows':chosen,'time_series':series,
        'method':'결측 제외, 같은 시각은 평균. 실제 경과 일수 기준 회귀·Pearson r·Kendall tau, 겹치지 않는 초기/후기 최대 100개 시각의 평균 비교.',
        'note':'상승·하강 분류는 |표준화 이동|≥1 및 |기저 이동|≥0.7과 tau 방향 일치의 탐색 규칙이며 물리적 마모·정비 효과를 입증하지 않습니다.'})
