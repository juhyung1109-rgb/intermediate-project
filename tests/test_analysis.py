import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.data_analysis.agent import AnalysisAgent, AgentUnavailable
from src.data_analysis.inference import ModelService
from src.data_analysis.repository import SQLiteRepository
from src.data_analysis.service import DatasetService
from src.data_analysis.validation import DataError, parse_csv

ROOT = Path(__file__).resolve().parents[1]


class FakeModel:
    version = 'fixture-model'
    features = ['feature_1', 'feature_2']

    def predict(self, raw):
        missing = set(self.features) - set(raw)
        if missing:
            raise DataError('예측 필수 센서 열이 없습니다')
        out = raw[['row_id', 'sample_id']].copy()
        out['risk_score'] = raw.feature_1.fillna(0) / 100
        out = out.sort_values(['risk_score', 'row_id'], ascending=[False, True])
        out['risk_rank'] = np.arange(1, len(out)+1)
        out['is_top20_review'] = out.risk_rank <= math.ceil(len(out)*.2)
        out['abnormal_sensor_count'] = 0
        return out

    def reference(self):
        return pd.DataFrame({'feature_1':[10.,20.,30.], 'feature_2':[1.,2.,3.]})


@pytest.fixture
def svc(tmp_path):
    return DatasetService(SQLiteRepository(tmp_path/'store.sqlite3'), FakeModel())


CSV = b'sample_id,timestamp,actual_label,feature_1,feature_2\n001,2009-01-01,0,10,1\n002,2009-01-02,1,90,9\n003,2009-02-01,0,20,2\n004,2009-02-02,0,30,3\n005,2009-02-03,1,80,\n'


def test_join_preserves_measurements_and_full_results(svc):
    d = svc.ingest('a','test.csv',CSV)
    assert len(d['full_results']) == d['total_count'] == 5
    tools = svc.tools('a', d['dataset_id'])
    high = tools.execute('rank_samples', {'limit':1})['data']['rows'][0]
    assert high['sample_id'] == '002'
    assert high['row_id'] == 1 and high['feature_1'] == 90
    assert tools.frame.sample_id.tolist() == ['001','002','003','004','005']
    assert tools.execute('evaluate_predictions')['data']['TP'] == 1


def test_structured_query_and_aggregations(svc):
    d = svc.ingest('a','t.csv',CSV)
    t = svc.tools('a',d['dataset_id'])
    r = t.execute('query_data', {'filters':[{'column':'risk_score','op':'ge','value':.8}], 'aggregations':[{'column':'feature_1','op':'mean'}]})['data']
    assert r['filtered_rows'] == 2
    assert r['rows'] == [{'feature_1__mean':85.}]
    grouped = t.execute('query_data', {'group_by':['actual_label'], 'aggregations':[{'column':'sample_id','op':'count'}]})['data']['rows']
    assert grouped == [{'actual_label':0,'sample_id__count':3}, {'actual_label':1,'sample_id__count':2}]
    assert t.execute('time_summary')['data']['rows'][0]['count'] == 2
    assert t.execute('compare_groups')['data']['high_count'] == 1
    assert t.execute('correlate')['data']['rows'][0]['correlation'] == pytest.approx(1.)


@pytest.mark.parametrize('kwargs', [
    {'name':'__getattribute__','arguments':{}},
    {'name':'rank_samples','arguments':{'limit':51}},
    {'name':'rank_samples','arguments':{'limit':True}},
    {'name':'rank_samples','arguments':{'columns':['missing']}},
    {'name':'query_data','arguments':{'filters':[{'column':'risk_score','op':'eval','value':'evil'}]}},
    {'name':'query_data','arguments':{'columns':['feature_1; DROP TABLE datasets']}},
    {'name':'time_summary','arguments':{'frequency':'year'}},
    {'name':'evaluate_predictions','arguments':{'review_ratio':0}},
    {'name':'profile_dataset','arguments':[]},
])
def test_tools_reject_unsupported_input(svc,kwargs):
    d=svc.ingest('a','t.csv',CSV)
    with pytest.raises(DataError):
        svc.tools('a',d['dataset_id']).execute(**kwargs)


@pytest.mark.parametrize('csv', [
    b'sample_id,feature_1,feature_1\na,1,2\n',
    b'sample_id,feature_1\na,hi\n',
    b'sample_id,feature_1\na,inf\n',
    b'sample_id,feature_1\na,1\na,2\n',
    b'sample_id,feature_1\n,1\n',
    b'feature_591\n1\n',
    b'feature_1,actual_label\n1,-1\n',
    b'feature_1,actual_label,label\n1,0,0\n',
    b'feature_1,timestamp\n1,never\n',
    b'feature_1,risk_score\n1,1\n',
    b'feature_1,feature_2\n1,2,3\n',
    b'feature_bad\n1\n',
    b'',
])
def test_invalid_csv(csv):
    with pytest.raises(DataError):parse_csv(csv)


def test_missing_required_features(svc):
    with pytest.raises(DataError,match='필수'):
        svc.ingest('a','small.csv',b'feature_1\n2\n')


def test_unknown_labels_and_missing_timestamps(svc):
    d=svc.ingest('a','unknown.csv',b'feature_1,feature_2\n10,1\n90,\n')
    t=svc.tools('a',d['dataset_id'])
    p=t.execute('profile_dataset')['data']
    assert p['confirmed_failures'] is None
    assert p['confirmed_failure_rate'] is None
    assert p['unknown_label_count']==2 and p['missing_cells']==1
    assert t.execute('evaluate_predictions')['data']['status']=='unavailable'
    assert t.execute('time_summary')['data']['status']=='unavailable'
    json.dumps(d,allow_nan=False)


def test_restart_dedup_and_owner_scope(svc):
    d=svc.ingest('a','t.csv',CSV)
    id=d['dataset_id']
    assert svc.ingest('a','renamed.csv',CSV)['dataset_id']==id
    fresh=SQLiteRepository(svc.repository.path)
    assert fresh.get('a',id)[0]['row_count']==5
    assert fresh.list('b')==[]
    with pytest.raises(KeyError):fresh.get('b',id)
    other=svc.ingest('b','t.csv',CSV)
    assert other['dataset_id']!=id
    fresh.save_conversation('a',id,'conv', [{'role':'user','content':'hello'}])
    with pytest.raises(KeyError):fresh.conversation('b',id,'conv')
    with pytest.raises(KeyError):fresh.conversation('a',other['dataset_id'],'conv')
    fresh.save_conversation('b',other['dataset_id'],'conv', [])
    assert fresh.conversation('a',id,'conv')[0]['content']=='hello'


class FakeModels:
    def __init__(self, outputs):self.outputs=iter(outputs);self.calls=[]
    def generate_content(self, **kwargs):
        self.calls.append({**kwargs,'contents':list(kwargs['contents'])})
        return next(self.outputs)


def call(name,args,id='call1'):
    from google.genai import types
    part=types.Part(function_call=types.FunctionCall(name=name,args=args,id=id),thought_signature=b'keep-this-signature')
    return SimpleNamespace(candidates=[SimpleNamespace(content=types.Content(role='model',parts=[part]),finish_reason='STOP')])


def answer(text='계산 근거에 따른 답변'):
    from google.genai import types
    return SimpleNamespace(candidates=[SimpleNamespace(content=types.Content(role='model',parts=[types.Part.from_text(text=text)]),finish_reason='STOP')])


def test_agent_tool_loop_history_and_scope(svc):
    d=svc.ingest('a','t.csv',CSV);id=d['dataset_id']
    responses=FakeModels([call('profile_dataset',{}),call('query_data',{'columns':['sample_id','feature_1'],'limit':2.0},'call2'),answer(),call('rank_samples',{'limit':1}),answer('후속 계산')])
    agent=AnalysisAgent(svc,SimpleNamespace(models=responses),'gemini-3.8-flash')
    result=agent.answer('a',id,'상위 표본을 분석해줘')
    assert len(result['tool_results'])==2 and all(t['ok'] for t in result['tool_results'])
    assert responses.calls[0]['config'].tool_config.function_calling_config.mode=='ANY'
    assert responses.calls[1]['contents'][-1].role=='user'
    assert responses.calls[1]['contents'][-1].parts[0].function_response.id=='call1'
    assert responses.calls[1]['contents'][-2].parts[0].thought_signature==b'keep-this-signature'
    assert result['agent_model']=='gemini-3.8-flash'
    result2=agent.answer('a',id,'이어서 보여줘',result['conversation_id'])
    assert result2['answer']=='후속 계산'
    assert responses.calls[3]['contents'][1].role=='model'
    with pytest.raises(KeyError):agent.answer('b',id,'남의 데이터')


def test_agent_failure_recovery_and_limits(svc,monkeypatch):
    d=svc.ingest('a','t.csv',CSV);id=d['dataset_id']
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY',raising=False)
    with pytest.raises(AgentUnavailable):AnalysisAgent(svc).answer('a',id,'질문')
    responses=FakeModels([call('shell',{}),call('profile_dataset',{}),answer()])
    result=AnalysisAgent(svc,SimpleNamespace(models=responses)).answer('a',id,'품질')
    assert [t['ok'] for t in result['tool_results']]==[False,True]
    with pytest.raises(RuntimeError,match='근거'):
        AnalysisAgent(svc,SimpleNamespace(models=FakeModels([answer()]))).answer('a',id,'질문')
    with pytest.raises(RuntimeError,match='반복'):
        AnalysisAgent(svc,SimpleNamespace(models=FakeModels([call('profile_dataset',{})])),max_rounds=1).answer('a',id,'질문')


def test_gemini_provider_error(svc):
    from google.genai.errors import ClientError
    d=svc.ingest('a','t.csv',CSV)
    class FailingModels:
        def generate_content(self,**kwargs):raise ClientError(429,{'error':{'message':'quota'}})
    with pytest.raises(AgentUnavailable,match='429'):
        AnalysisAgent(svc,SimpleNamespace(models=FailingModels())).answer('a',d['dataset_id'],'질문')


@pytest.fixture(scope='module')
def real_model():
    model=ModelService(ROOT)
    assert model.error is None, model.error
    return model


@pytest.mark.parametrize('filename,n,fail,missing,months',[
    ('secom_test_batch_200811_200903.csv',500,31,13253,[100]*5),
    ('sim_batch_200_200904_200905.csv',200,9,5280,[99,101]),
    ('sim_batch_300_200906_200908.csv',300,22,8064,[98,101,101]),
    ('sim_batch_400_200909_200912.csv',400,12,10367,[98,102,99,101]),
])
def test_real_simulation_pipeline(tmp_path,real_model,filename,n,fail,missing,months):
    service=DatasetService(SQLiteRepository(tmp_path/'actual.sqlite3'),real_model)
    d=service.ingest('test',filename,(ROOT/'simulation'/filename).read_bytes(),'simulation')
    assert d['total_count']==len(d['full_results'])==n
    assert d['top20_count']==math.ceil(n*.2)
    tools=service.tools('test',d['dataset_id'])
    p=tools.execute('profile_dataset')['data']
    assert p['missing_cells']==missing and p['confirmed_failures']==fail
    assert [r['count'] for r in tools.execute('time_summary')['data']['rows']]==months
    assert np.isfinite(tools.frame.risk_score).all()
    assert tools.execute('compare_reference')['data']['reference_rows']==1170
    json.dumps(d,allow_nan=False)
    if n==300:
        assert tools.execute('time_summary')['data']['rows'][-1]['confirmed_failure_rate']==pytest.approx(14/101)
    if n==200:
        shap=tools.execute('explain_sample',{'row_id':0})['data']
        reconstructed=1/(1+math.exp(-shap['model_raw_output']))
        assert reconstructed==pytest.approx(shap['risk_score'],abs=1e-7)
        assert len(shap['rows'])==15
        # A model upgrade must not explain an older result with a different model.
        tools.metadata['model_version']='another-version'
        with pytest.raises(DataError):tools.execute('explain_sample',{'row_id':0})


def test_api_session_and_dataset_flow(tmp_path,monkeypatch):
    monkeypatch.setenv('DATASET_DB',str(tmp_path/'api.sqlite3'))
    import server.app as backend
    service=DatasetService(SQLiteRepository(tmp_path/'api-isolated.sqlite3'),FakeModel())
    monkeypatch.setattr(backend,'repository',service.repository)
    monkeypatch.setattr(backend,'service',service)
    monkeypatch.setattr(backend,'agent',AnalysisAgent(service,model=None))
    with TestClient(backend.app) as client, TestClient(backend.app) as stranger:
        r=client.post('/api/predict-batch',files={'file':('t.csv',CSV,'text/csv')})
        assert r.status_code==200,r.text
        id=r.json()['dataset_id']
        assert client.cookies.get('semiguard_analysis_session')
        assert len(client.get('/api/datasets').json()['datasets'])==1
        assert client.get(f'/api/datasets/{id}?limit=2').json()['rows'][0]['sample_id']=='002'
        assert client.get(f'/api/datasets/{id}/report').status_code==200
        assert stranger.get(f'/api/datasets/{id}').status_code==404
        r=client.post(f'/api/datasets/{id}/tools/query_data',json={'arguments':{'columns':['sample_id','feature_1'],'limit':2}})
        assert r.status_code==200 and len(r.json()['data']['rows'])==2
        exported=pd.read_csv(__import__('io').StringIO(client.get(f'/api/datasets/{id}/export').content.decode('utf-8-sig')),dtype={'sample_id':'string'})
        assert exported.sample_id.tolist()==['001','002','003','004','005']
        assert exported.iloc[1].risk_score==.9 and exported.iloc[1].feature_1==90
        assert client.post('/api/predict-batch',files={'file':('t.csv',b'feature_1\naaa\n','text/csv')}).status_code==422
        assert client.get('/api/wiki/list').status_code==404
        assert client.get('/api/evaluation').json()['test_count']==314
        assert client.get('/').status_code==200
