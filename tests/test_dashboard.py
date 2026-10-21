import math
import json
import pandas as pd
import pytest
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from src.data_analysis.dashboard import DashboardService,ScopedAgentService
from src.data_analysis.inspections import InspectionStore
from src.data_analysis.validation import DataError
from src.data_analysis.repository import SQLiteRepository
from src.data_analysis.service import DatasetService
from server.dashboard_api import create_dashboard_router
from test_analysis import FakeModel,CSV


@pytest.fixture
def sample(tmp_path):
    service=DatasetService(SQLiteRepository(tmp_path/'dashboard.sqlite3'),FakeModel())
    result=service.ingest('owner','fixture.csv',CSV)
    return service,result['dataset_id']


def test_period_ranking_categories_and_reports(sample):
    service,id=sample;dashboard=DashboardService(service)
    all=dashboard.overview('owner',id)
    assert all['profile']['row_count']==5 and all['metrics']['TP']==1
    feb=dashboard.overview('owner',id,'2009-02',.5)
    assert feb['profile']['row_count']==3 and feb['metadata']['row_count']==3
    assert feb['rows'][0]['sample_id']=='005' and feb['rows'][0]['risk_rank']==1
    assert feb['metrics']['selected_count']==2
    counts=pd.Series([r['category'] for r in feb['rows']]).value_counts()
    assert sum(counts)==3
    for name in ['TP','FP','FN','TN']:assert counts.get(name,0)==feb['metrics'][name]
    report=dashboard.report('owner',id,'2009-02',.5)
    assert '표본 3행' in report and '50%' in report
    assert dashboard.tools('owner',id,'2009').frame.shape[0]==5
    with pytest.raises(DataError):dashboard.tools('owner',id,'2008-01')
    with pytest.raises(DataError):dashboard.tools('owner',id,'__invalid')
    with pytest.raises(KeyError):dashboard.overview('stranger',id)


def test_recent_window_and_rolling(sample):
    service,id=sample;dashboard=DashboardService(service)
    r=dashboard.overview('owner',id,'recent7')
    assert r['profile']['row_count']==3
    assert r['rolling']['rows'][-1]['rolling_failure_rate']==pytest.approx(1/3)
    assert dashboard.overview('owner',id)['rolling']['rows'][1]['rolling_failure_rate']==.5


def test_agent_period_and_conversation_scope(sample):
    service,id=sample;dashboard=DashboardService(service)
    jan=ScopedAgentService(dashboard,'2009-01');feb=ScopedAgentService(dashboard,'2009-02')
    assert jan.tools('owner',id).profile_dataset()['row_count']==2
    assert feb.tools('owner',id).profile_dataset()['row_count']==3
    jan.repository.save_conversation('owner',id,'conversation',[{'role':'user','content':'January'}])
    with pytest.raises(KeyError):feb.repository.conversation('owner',id,'conversation')
    with pytest.raises(KeyError):ScopedAgentService(dashboard,'2009-01',.5).repository.conversation('owner',id,'conversation')


def test_inspection_lifecycle_restart_and_owner_scope(sample):
    service,id=sample;store=InspectionStore(service.repository)
    payload={'title':'분포 검토','chamber':'검토 범위','urgency':'주의','reason':'평균 이동 확인','items':['원본 확인','참고군 확인'],'period':'all'}
    task=store.create('owner',id,payload);tid=task['id']
    assert task['status']=='open'
    with pytest.raises(KeyError):store.get('stranger',tid)
    with pytest.raises(DataError):store.transition('owner',tid,'approve',{})
    with pytest.raises(DataError):store.transition('owner',tid,'submit',{'checked':[True,False],'notes':'미완료'})
    reported=store.transition('owner',tid,'submit',{'checked':[True,True],'notes':'로컬 점검 확인'})
    assert reported['status']=='reported'
    reopened=store.transition('owner',tid,'reopen',{'review_note':'다시 확인'})
    assert reopened['status']=='open' and not any(reopened['checked'])
    store.transition('owner',tid,'submit',{'checked':[True,True],'notes':'재확인 완료'})
    assert store.transition('owner',tid,'approve',{})['status']=='approved'
    fresh=InspectionStore(SQLiteRepository(service.repository.path))
    assert fresh.list('owner',id)[0]['status']=='approved'
    assert len(fresh.list('owner',id)[0]['history'])==5
    assert fresh.list('stranger',id)==[]


def test_dashboard_routes(sample):
    service,id=sample;app=FastAPI()
    @app.middleware('http')
    async def owner(request,call_next):request.state.owner=request.headers.get('x-test-owner','owner');return await call_next(request)
    @app.exception_handler(DataError)
    async def invalid(request,exc):return JSONResponse({'detail':str(exc)},status_code=422)
    @app.exception_handler(KeyError)
    async def missing(request,exc):return JSONResponse({'detail':str(exc)},status_code=404)
    app.include_router(create_dashboard_router(service))
    with TestClient(app) as c:
        assert c.get('/dashboard/').status_code==200
        url=f'/api/dashboard/{id}'
        data=c.get(url+'/overview?period=2009-02&ratio=0.5').json()
        assert data['profile']['row_count']==3 and data['metrics']['selected_count']==2
        assert c.get(url+'/overview',headers={'x-test-owner':'other'}).status_code==404
        assert '표본 5행' in c.get(url+'/report').text
        exported=pd.read_csv(__import__('io').StringIO(c.get(url+'/export?period=2009-02&ratio=0.5').content.decode('utf-8-sig')))
        assert len(exported)==3 and exported.category.eq('TP').sum()==1
        assert c.get('/api/dashboard-qr').headers['content-type']=='image/png'
        task=c.post(url+'/inspections',json={'title':'점검 확인','chamber':'테스트','urgency':'일반','reason':'로컬 확인','items':['확인'],'period':'all'}).json()
        assert c.post(f'/api/dashboard/inspections/{task["id"]}/submit',json={'checked':[True],'notes':'로컬 확인 완료'}).status_code==200
        assert c.post(f'/api/dashboard/inspections/{task["id"]}/approve',json={}).json()['status']=='approved'
