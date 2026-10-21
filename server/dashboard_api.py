import io
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter,Request
from fastapi.responses import FileResponse,Response
from pydantic import BaseModel,Field

from src.data_analysis.agent import AnalysisAgent
from src.data_analysis.dashboard import DashboardService,ScopedAgentService
from src.data_analysis.inspections import InspectionStore
from src.data_analysis.validation import DataError


def create_dashboard_router(service):
    router=APIRouter()
    dashboard=DashboardService(service)
    inspections=InspectionStore(service.repository)
    root=Path(__file__).resolve().parents[1]

    @router.get('/dashboard',include_in_schema=False)
    @router.get('/dashboard/',include_in_schema=False)
    def dashboard_page():return FileResponse(root/'web/dashboard/index.html')

    @router.post('/api/dashboard/initial')
    def initial(request:Request):return dashboard.initial(request.state.owner)

    @router.get('/api/dashboard/{dataset_id}/overview')
    def overview(dataset_id:UUID,request:Request,period:str='all',ratio:float=.2):
        return dashboard.overview(request.state.owner,str(dataset_id),period,ratio)

    @router.get('/api/dashboard/{dataset_id}/sample')
    def sample(dataset_id:UUID,request:Request,sample_id:str,period:str='all',ratio:float=.2):
        return dashboard.sample(request.state.owner,str(dataset_id),sample_id,period,ratio)

    @router.get('/api/dashboard/{dataset_id}/drift')
    def drift(dataset_id:UUID,request:Request,period:str='all'):
        return dashboard.drift(request.state.owner,str(dataset_id),period)

    class ScopedTool(BaseModel):
        period:str='all'
        ratio:float=.2
        arguments:dict=Field(default_factory=dict)

    @router.post('/api/dashboard/{dataset_id}/tools/{tool_name}')
    def scoped_tool(dataset_id:UUID,tool_name:str,req:ScopedTool,request:Request):
        return dashboard.tools(request.state.owner,str(dataset_id),req.period,req.ratio).execute(tool_name,req.arguments)

    @router.get('/api/dashboard/{dataset_id}/report')
    def report(dataset_id:UUID,request:Request,period:str='all',ratio:float=.2):
        text=dashboard.report(request.state.owner,str(dataset_id),period,ratio)
        return Response(text,media_type='text/markdown; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="dashboard_{dataset_id}.md"'})

    @router.get('/api/dashboard/{dataset_id}/export')
    def export(dataset_id:UUID,request:Request,period:str='all',ratio:float=.2):
        frame=dashboard.tools(request.state.owner,str(dataset_id),period,ratio).frame.sort_values('row_id')
        return Response(frame.to_csv(index=False).encode('utf-8-sig'),media_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition':f'attachment; filename="dashboard_{dataset_id}.csv"'})

    class Chat(BaseModel):
        query:str=Field(min_length=1,max_length=3000)
        period:str='all'
        ratio:float=.2
        conversation_id:UUID|None=None

    @router.post('/api/dashboard/{dataset_id}/chat')
    def chat(dataset_id:UUID,req:Chat,request:Request):
        scoped=ScopedAgentService(dashboard,req.period,req.ratio)
        instance=AnalysisAgent(scoped)
        try:return instance.answer(request.state.owner,str(dataset_id),req.query,str(req.conversation_id) if req.conversation_id else None)
        finally:
            if instance.client is not None:instance.client.close()

    @router.get('/api/dashboard/{dataset_id}/inspections')
    def list_tasks(dataset_id:UUID,request:Request):
        service.tools(request.state.owner,str(dataset_id))
        return {'tasks':inspections.list(request.state.owner,str(dataset_id))}

    class Task(BaseModel):
        title:str=Field(min_length=1,max_length=200)
        chamber:str=Field(min_length=1,max_length=100)
        urgency:str=Field(pattern='^(일반|주의|긴급)$')
        reason:str=Field(min_length=1,max_length=1000)
        items:list[str]=Field(min_length=1,max_length=20)
        period:str='all'

    @router.post('/api/dashboard/{dataset_id}/inspections')
    def create_task(dataset_id:UUID,req:Task,request:Request):
        service.tools(request.state.owner,str(dataset_id))
        return inspections.create(request.state.owner,str(dataset_id),req.model_dump())

    class Transition(BaseModel):
        checked:list[bool]=Field(default_factory=list)
        notes:str=Field(default='',max_length=3000)
        review_note:str=Field(default='',max_length=1000)

    @router.post('/api/dashboard/inspections/{task_id}/{action}')
    def transition(task_id:UUID,action:str,req:Transition,request:Request):
        return inspections.transition(request.state.owner,str(task_id),action,req.model_dump())

    @router.get('/api/dashboard-qr')
    def qr(request:Request):
        import qrcode
        result=io.BytesIO();qrcode.make(str(request.base_url)+'dashboard/').save(result,format='PNG')
        return Response(result.getvalue(),media_type='image/png')

    return router
