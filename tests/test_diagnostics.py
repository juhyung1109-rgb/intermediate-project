import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from server.dashboard_api import create_dashboard_router
from src.data_analysis.dashboard import DashboardService
from src.data_analysis.inference import ModelService
from src.data_analysis.repository import SQLiteRepository
from src.data_analysis.service import DatasetService
from src.data_analysis.validation import DataError
from test_analysis import CSV, FakeModel

ROOT=Path(__file__).resolve().parents[1]


class ExplainingFixture(FakeModel):
    def explain(self,frame,row_id,model_version):
        return {'base_value':-1.,'sum_all_shap':.5,'model_raw_output':-.5,
                'rows':[{'feature':'feature_1','shap':.5,'model_input':1}],
                'risk_increase':[{'feature':'feature_1','shap':.5}],'risk_decrease':[]}


@pytest.fixture
def fixture_service(tmp_path):
    return DatasetService(SQLiteRepository(tmp_path/'fixture.sqlite3'),ExplainingFixture())


@pytest.fixture(scope='module')
def real(tmp_path_factory):
    model=ModelService(ROOT)
    assert model.model is not None,model.error
    service=DatasetService(SQLiteRepository(tmp_path_factory.mktemp('diagnostics')/'real.sqlite3'),model)
    result=service.ingest('owner','batch500.csv',(ROOT/'simulation/secom_test_batch_200811_200903.csv').read_bytes())
    return service,result['dataset_id']


def test_reference_statistics_missing_and_review_categories(fixture_service):
    s=fixture_service;id=s.ingest('owner','small.csv',CSV)['dataset_id'];tools=s.tools('owner',id)
    result=tools.execute('diagnose_sample',{'sample_id':'005'})['data']
    assert result['row']['category']=='FN' and result['recommendation']['rule_id']=='D03'
    assert result['top_sensors'][0]['z_score']==pytest.approx(6.)
    assert result['top_sensors'][0]['reference_median']==20.
    assert result['missing_sensors']==['feature_2']
    assert result['sensor_status_counts']['결측 확인']==1
    assert next(r for r in result['top_sensors'] if r['sensor']=='feature_2')['raw_value'] is None
    more=tools.diagnose_sample('005',.5)
    assert more['row']['category']=='TP' and more['recommendation']['rule_id']=='D01'
    json.dumps(result,allow_nan=False)
    with pytest.raises(DataError):tools.diagnose_sample('not-present')
    with pytest.raises(DataError):tools.diagnose_sample('005',1)


def test_unlabelled_and_zero_reference_variance(fixture_service):
    s=fixture_service
    s.model.reference=lambda:pd.DataFrame({'feature_1':[1.,1.],'feature_2':[2.,2.]})
    id=s.ingest('owner','unknown.csv',b'sample_id,feature_1,feature_2\nx,10,2\n')['dataset_id']
    d=s.tools('owner',id).diagnose_sample('x')
    assert d['row']['category']=='미확인' and d['recommendation']['rule_id']=='D05'
    assert all(r['z_score'] is None for r in d['top_sensors'])
    assert d['sensor_status_counts']['기준 산포 없음']==2


def test_actual_shap_waterfall_and_reference_values(real):
    s,id=real;tools=s.tools('owner',id);d=tools.diagnose_sample('2184');shap=d['shap']
    row=tools.frame.loc[tools.frame.sample_id.eq('2184')].iloc[0];ref=s.model.reference()
    expected=((row[ref.columns]-ref.mean())/ref.std(ddof=1)).abs().sort_values(ascending=False).head(5)
    assert [r['sensor'] for r in d['top_sensors']]==expected.index.tolist()
    for sensor in d['top_sensors']:
        assert sensor['raw_value']==row[sensor['sensor']]
        assert sensor['reference_median']==ref[sensor['sensor']].median()
    current=shap['base_value']
    for r in shap['waterfall']:
        assert r['start']==pytest.approx(current);current=r['end']
    assert current==pytest.approx(shap['model_raw_output'])
    assert sum(r['shap'] for r in shap['waterfall'])==pytest.approx(shap['sum_all_shap'])
    assert shap['reconstructed_risk_score']==pytest.approx(row.risk_score,abs=1e-10)
    assert all(r['shap']>0 for r in shap['risk_increase'])
    assert all(r['shap']<0 for r in shap['risk_decrease'])


def test_diagnostic_period_scope_and_model_guard(real):
    s,id=real;dashboard=DashboardService(s)
    d=dashboard.sample('owner',id,'2184','2008-12',.2)
    assert d['scope_count']==100 and d['row']['risk_rank']<=100
    with pytest.raises(DataError):dashboard.sample('owner',id,'2184','2009-01')
    tools=s.tools('owner',id);tools.metadata['model_version']='old'
    with pytest.raises(DataError):tools.diagnose_sample('2184')


def test_global_shap_matches_actual_rows_and_sampling(real):
    s,id=real;tools=DashboardService(s).tools('owner',id,'2008-12')
    result=tools.execute('global_shap',{'limit':5,'max_samples':500})['data']
    assert result['analyzed_count']==result['scope_count']==100
    # Check the aggregation against a fresh TreeExplainer batch calculation.
    names,_,values,_=s.model._shap_values(tools.frame,s.model.version)
    first=result['rows'][0]
    assert first['mean_abs_shap']==pytest.approx(np.abs(values[:,names.index(first['feature'])]).mean())
    assert tools.global_shap(3,7)['analyzed_count']==7
    with pytest.raises(DataError):tools.global_shap(3,501)
    with pytest.raises(DataError):tools.global_shap(3,True)


def test_temporal_drift_uses_elapsed_time_and_nonoverlapping_windows(fixture_service):
    s=fixture_service;days=np.array([0,1,3,5,8,13,21,34,55,89,144,233])
    frame=pd.DataFrame({'sample_id':[str(i) for i in range(len(days))],
        'timestamp':pd.Timestamp('2009-01-01')+pd.to_timedelta(days,unit='D'),
        'feature_1':days*.1,'feature_2':-days*.2})
    id=s.ingest('owner','trend.csv',frame.to_csv(index=False).encode())['dataset_id']
    t=s.tools('owner',id);d=t.sensor_drift('both')
    assert d['direction_counts']=={'upward':1,'downward':1,'flat':0}
    up=next(r for r in d['rows'] if r['sensor']=='feature_1')
    assert up['slope_per_day']==pytest.approx(.1)
    assert up['window_count']==6 and up['kendall_tau']==pytest.approx(1.)
    assert t.sensor_drift('downward')['rows'][0]['sensor']=='feature_2'
    t.frame=t.frame.sample(frac=1,random_state=42)
    assert t.sensor_drift('both')['rows']==d['rows']
    with pytest.raises(DataError):t.sensor_drift('invalid')


def test_drift_missing_time_and_tied_timestamps(fixture_service):
    s=fixture_service
    id=s.ingest('owner','no-time.csv',b'feature_1,feature_2\n1,2\n2,1\n')['dataset_id']
    assert s.tools('owner',id).sensor_drift()['status']=='unavailable'
    raw=CSV.replace(b'2009-01-02',b'2009-01-01').replace(b'2009-02-02',b'2009-02-01').replace(b'2009-02-03',b'2009-02-01')
    id=s.ingest('owner','tied.csv',raw)['dataset_id']
    assert s.tools('owner',id).sensor_drift()['status']=='unavailable'


def test_scoped_tool_and_sample_api(real):
    s,id=real;app=FastAPI()
    @app.middleware('http')
    async def owner(request:Request,call_next):request.state.owner='owner';return await call_next(request)
    app.include_router(create_dashboard_router(s))
    with TestClient(app) as c:
        d=c.post(f'/api/dashboard/{id}/tools/diagnose_sample',json={'period':'2008-12','ratio':.3,'arguments':{'sample_id':'2184'}}).json()
        assert d['scope_count']==100 and d['data']['review_ratio']==.3
        assert c.get(f'/api/dashboard/{id}/sample?sample_id=2184&period=2008-12').json()['recommendation']['rule_id']
