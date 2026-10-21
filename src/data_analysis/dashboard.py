"""Dataset/period-consistent views behind the local operations subpage."""
import math
import re
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import average_precision_score

from .tools import AnalysisTools, ratio_value
from .validation import DataError, clean_json


class DashboardService:
    def __init__(self, service):
        self.service = service

    def initial(self, owner):
        root = self.service.model.root
        sim_path = root / 'simulation/sim_batch_300_200906_200908.csv'
        if not sim_path.exists():
            sim_candidates = list((root / 'simulation').glob('sim_batch_*.csv'))
            if sim_candidates:
                sim_path = sim_candidates[0]
            else:
                raise DataError('시뮬레이션 관제 추론 데이터를 찾을 수 없습니다.')
        return self.service.ingest(owner, sim_path.name, sim_path.read_bytes(), 'simulation')

    def tools(self, owner, dataset_id, period='all', ratio=.2):
        ratio_value(ratio)
        original = self.service.tools(owner,dataset_id)
        frame = original.frame.copy()
        if period != 'all':
            if 'timestamp' not in frame:
                raise DataError('측정 시각이 없어 기간을 선택할 수 없습니다.')
            times = pd.to_datetime(frame.timestamp,format='mixed',errors='coerce',utc=True)
            if period in ['recent7','recent30']:
                days = 7 if period=='recent7' else 30
                end = times.max().normalize()+pd.Timedelta(days=1)
                mask = times.ge(end-pd.Timedelta(days=days)) & times.lt(end)
            elif re.fullmatch(r'\d{4}(-\d{2})?',period):
                mask = times.dt.strftime('%Y-%m' if len(period)==7 else '%Y').eq(period)
            else:
                raise DataError('유효하지 않은 기간입니다.')
            frame = frame.loc[mask].copy()
        if frame.empty:
            raise DataError('선택 기간에 표본이 없습니다.')
        ranked = frame.sort_values(['risk_score','row_id'],ascending=[False,True])
        ranked['risk_rank'] = np.arange(1,len(ranked)+1)
        ranked['is_top20_review'] = ranked.risk_rank <= math.ceil(len(ranked)*.2)
        metadata = {**original.metadata,'original_row_count':original.metadata['row_count'],
                    'row_count':len(ranked),'period':period,'review_ratio':ratio,'scope_count':len(ranked)}
        raw = original.raw.loc[original.raw.row_id.isin(ranked.row_id)].copy()
        pred = ranked[['row_id','sample_id','risk_score','abnormal_sensor_count','risk_rank','is_top20_review']].copy()
        tools = AnalysisTools(metadata,raw,pred,self.service.model)
        tools.frame = tools.frame.sort_values('risk_rank').reset_index(drop=True)
        selected = tools.frame.risk_rank <= math.ceil(len(ranked)*ratio)
        label = tools.frame.get('actual_label',pd.Series(np.nan,index=tools.frame.index))
        tools.frame['selected_for_review'] = selected
        tools.frame['category'] = np.select([label.eq(1)&selected,label.eq(0)&selected,label.eq(1)&~selected,label.eq(0)&~selected],['TP','FP','FN','TN'],default='미확인')
        return tools

    def overview(self,owner,dataset_id,period='all',ratio=.2):
        tools = self.tools(owner,dataset_id,period,ratio)
        full = self.service.tools(owner,dataset_id)
        frame = tools.frame
        periods=[]
        if 'timestamp' in full.frame:
            times=pd.to_datetime(full.frame.timestamp,format='mixed',errors='coerce',utc=True)
            periods=sorted(times.dropna().dt.strftime('%Y-%m').unique().tolist())
        metrics=tools.evaluate_predictions(ratio)
        labels=frame.get('actual_label',pd.Series(np.nan,index=frame.index))
        ap=float(average_precision_score(labels,frame.risk_score)) if labels.notna().all() and labels.nunique()==2 else None
        cols=[c for c in ['row_id','sample_id','timestamp','actual_label','risk_score','risk_rank','selected_for_review','category','abnormal_sensor_count'] if c in frame]
        return clean_json({'metadata':tools.metadata,'periods':periods,'profile':tools.profile_dataset(),
            'metrics':{**metrics,'average_precision':ap},'ratio':ratio,'rows':frame[cols].to_dict('records'),
            'review_curve':[tools.evaluate_predictions(r) for r in [.05,.1,.15,.2,.25,.3,.4,.5]],
            'time_summary':tools.time_summary(),'rolling':self.rolling(frame),'sensors':tools.sensors})

    @staticmethod
    def rolling(frame):
        if 'timestamp' not in frame or 'actual_label' not in frame:
            return {'rows':[],'reason':'측정 시각과 정답 라벨이 있어야 7일 추이를 계산합니다.'}
        times=pd.to_datetime(frame.timestamp,format='mixed',errors='coerce',utc=True)
        daily=frame.assign(day=times.dt.floor('D')).dropna(subset=['day']).groupby('day').agg(count=('row_id','size'),known=('actual_label','count'),failures=('actual_label','sum'))
        rolled=daily[['known','failures']].rolling('7D',closed='right').sum()
        daily['rolling_failure_rate']=rolled.failures/rolled.known.replace(0,np.nan)
        daily=daily.reset_index();daily['day']=daily.day.dt.strftime('%Y-%m-%d')
        return {'rows':clean_json(daily.tail(120).to_dict('records')),'total_days':len(daily),'note':'선택 범위에서 해당 일 포함 이전 7일의 확인 라벨을 분모로 계산합니다. 최근 120개 관측일을 표시합니다.'}

    def sample(self,owner,dataset_id,sample_id,period='all',ratio=.2):
        return self.tools(owner,dataset_id,period,ratio).diagnose_sample(str(sample_id),ratio)

    def drift(self,owner,dataset_id,period='all'):
        tools=self.tools(owner,dataset_id,period)
        if tools.metadata['model_version']!=self.service.model.version:raise DataError('현재 모델과 저장 결과의 버전이 다릅니다.')
        ref=self.service.model.reference();rows=[]
        for c in ref:
            a,b=tools.frame[c].dropna(),ref[c].dropna();sd=b.std(ddof=0)
            shift=(a.mean()-b.mean())/sd if len(a) and sd>0 else np.nan
            test=ks_2samp(a,b) if len(a)>=2 and len(b)>=2 else None
            rows.append({'sensor':c,'input_mean':a.mean(),'reference_mean':b.mean(),'shift_std':shift,
                         'std_ratio':a.std(ddof=0)/sd if sd>0 and len(a) else None,
                         'ks_distance':float(test.statistic) if test else None,'input_count':len(a),'reference_count':len(b)})
        rows.sort(key=lambda r:abs(r['shift_std']) if pd.notna(r['shift_std']) else -1,reverse=True)
        return clean_json({'rows':rows,'reference_count':len(ref),'scope_count':len(tools.frame),
            'temporal':tools.sensor_drift('all',30),
            'note':'평균 이동·표준편차 비·KS 거리는 탐색 지표입니다. 공정 원인이나 인터락 한계로 단정하지 않습니다.'})

    def report(self,owner,dataset_id,period='all',ratio=.2):
        data=self.overview(owner,dataset_id,period,ratio);m=data['metrics'];p=data['profile']
        lines=['# SEMI GUARD 분석 보고서','',f"파일: {data['metadata']['filename']}",f'기간: {period}',f'데이터셋: {dataset_id}',f"모델: {data['metadata']['model_version']}",'',f"표본 {p['row_count']}행 · 센서 {p['sensor_count']}개 · 원본 결측 {p['missing_cells']}셀",f'검토 비율: {ratio:.0%}','']
        if m['status']=='available':
            lines += [f"TP {m['TP']} / FP {m['FP']} / FN {m['FN']} / TN {m['TN']}",f"Recall: {m['recall']:.2%}" if m['recall'] is not None else 'Recall: 미정의',f"Precision: {m['precision']:.2%}",'']
        else:lines += ['전체 정답 라벨이 없어 성능을 평가하지 않습니다.','']
        lines += ['## 월별 집계','','|기간|표본|확인 라벨|확인 불량|불량률|','|---|---:|---:|---:|---:|']
        for r in data['time_summary'].get('rows',[]):
            rate=f"{r['confirmed_failure_rate']:.2%}" if r['confirmed_failure_rate'] is not None else '미확인'
            lines.append(f"|{r['period']}|{r['count']}|{r['known_label_count']}|{r['confirmed_failures']}|{rate}|")
        lines += ['','통계적 연관·SHAP은 고장 원인을 확정하지 않습니다. 합성 CSV의 성능을 실제 설비 성능으로 일반화하지 않습니다.']
        return '\n'.join(lines)+'\n'


class ScopedConversations:
    def __init__(self,repository,period,ratio):self.base=repository;self.period=period;self.ratio=ratio
    def context(self,dataset):return str(uuid.uuid5(uuid.NAMESPACE_URL,f'{dataset}:dashboard:{self.period}:{self.ratio}'))
    def conversation(self,owner,dataset,conversation):return self.base.conversation(owner,self.context(dataset),conversation)
    def save_conversation(self,owner,dataset,conversation,messages):return self.base.save_conversation(owner,self.context(dataset),conversation,messages)


class ScopedAgentService:
    def __init__(self,dashboard,period,ratio=.2):
        self.dashboard=dashboard;self.period=period;self.ratio=ratio
        self.repository=ScopedConversations(dashboard.service.repository,period,ratio)
    def tools(self,owner,dataset):return self.dashboard.tools(owner,dataset,self.period,self.ratio)
