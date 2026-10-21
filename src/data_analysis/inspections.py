"""Owner-scoped inspection workflow with atomic state transitions."""
import gzip
import json
import uuid
from datetime import datetime, timezone

from .validation import DataError


class InspectionStore:
    def __init__(self,repository):
        self.repo=repository
        if hasattr(repository,'connect'):
            with repository.connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS inspections (id TEXT PRIMARY KEY, owner TEXT NOT NULL, dataset TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)')

    def list(self,owner,dataset):
        if hasattr(self.repo,'connect'):
            with self.repo.connect() as db:
                rows=db.execute('SELECT payload FROM inspections WHERE owner=? AND dataset=? ORDER BY rowid DESC',(owner,dataset)).fetchall()
            return [json.loads(r[0]) for r in rows]
        blobs=self.repo.bucket.list_blobs(prefix=f'analysis/{owner}/inspections/')
        return sorted([v for b in blobs if (v:=self.repo._read(b))['dataset_id']==dataset],key=lambda r:r['created_at'],reverse=True)

    def get(self,owner,id):
        uuid.UUID(id)
        if hasattr(self.repo,'connect'):
            with self.repo.connect() as db:
                row=db.execute('SELECT payload FROM inspections WHERE owner=? AND id=?',(owner,id)).fetchone()
            if not row:raise KeyError('점검 지시를 찾을 수 없습니다.')
            return json.loads(row[0]),None
        blob=self.repo._blob(owner,'inspections',id)
        blob.reload()
        version=blob.generation
        return self.repo._read(blob),version

    def write(self,owner,data,previous=None,generation=None):
        if hasattr(self.repo,'connect'):
            with self.repo.connect() as db:
                if previous is None:
                    db.execute('INSERT INTO inspections VALUES (?,?,?,?,?)',(data['id'],owner,data['dataset_id'],data['status'],json.dumps(data,ensure_ascii=False)))
                else:
                    result=db.execute('UPDATE inspections SET status=?,payload=? WHERE id=? AND owner=? AND status=?',(data['status'],json.dumps(data,ensure_ascii=False),data['id'],owner,previous))
                    if result.rowcount!=1:raise DataError('다른 요청에서 점검 상태가 변경되었습니다. 새로고침해 주세요.')
        else:
            from google.api_core.exceptions import PreconditionFailed
            blob=self.repo._blob(owner,'inspections',data['id'])
            try:blob.upload_from_string(gzip.compress(json.dumps(data,ensure_ascii=False).encode()),content_type='application/gzip',if_generation_match=generation if previous else 0)
            except PreconditionFailed as exc:raise DataError('점검 상태가 변경되었습니다. 새로고침해 주세요.') from exc
        return data

    def create(self,owner,dataset,payload):
        items=payload['items']
        if not 1<=len(items)<=20 or any(not str(i).strip() or len(i)>300 for i in items):
            raise DataError('점검 항목은 비어 있지 않은 1~20개, 각 300자 이하여야 합니다.')
        now=datetime.now(timezone.utc).isoformat()
        data={'id':str(uuid.uuid4()),'dataset_id':dataset,'status':'open','created_at':now,'history':[{'status':'open','at':now}],**payload,'checked':[False]*len(items),'notes':''}
        return self.write(owner,data)

    def transition(self,owner,id,action,payload):
        data,generation=self.get(owner,id);previous=data['status']
        if action=='submit':
            if previous!='open':raise DataError('진행 중인 지시만 완료 보고할 수 있습니다.')
            checked=payload.get('checked',[]);notes=payload.get('notes','').strip()
            if len(checked)!=len(data['items']) or not all(v is True for v in checked) or not notes or len(notes)>3000:
                raise DataError('모든 항목을 확인하고 3000자 이내의 점검 결과를 작성해 주세요.')
            data.update(status='reported',checked=checked,notes=notes)
        elif action in ['approve','reopen']:
            if previous!='reported':raise DataError('보고서가 제출된 지시만 승인 또는 보완 요청할 수 있습니다.')
            data['status']='approved' if action=='approve' else 'open'
            data['review_note']=str(payload.get('review_note',''))[:1000]
            if action=='reopen':data['checked']=[False]*len(data['items'])
        else:raise DataError('지원하지 않는 점검 상태 변경입니다.')
        data['history'].append({'status':data['status'],'at':datetime.now(timezone.utc).isoformat()})
        return self.write(owner,data,previous,generation)
