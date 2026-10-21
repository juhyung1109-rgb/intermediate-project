"""Build and verify a complete source/data/model ZIP without local runtime state."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unicodedata
from zipfile import ZipFile, ZIP_DEFLATED
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED_DIRS={'.git','.venv','venv','env','ENV','node_modules','__pycache__',
    '.pytest_cache','.mypy_cache','.ruff_cache','.ipynb_checkpoints',
    'runtime','archive','.aws','.codex','.agents','.idea','.vscode'}
EXCLUDED_SUFFIXES={'.pyc','.pyo','.zip','.sqlite','.sqlite3','.db','.pem','.key','.p12','.pfx'}


def excluded(path):
    if any(p in EXCLUDED_DIRS or p=='.env' for p in path.parts):return True
    name=path.name.lower()
    if name=='.ds_store' or name.startswith('._'):return True
    if name.startswith('.env') and name!='.env.example':return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:return True
    if any(name.endswith(s) for s in ['.sqlite3-wal','.sqlite3-shm','.db-wal','.db-shm']):return True
    if name in ['credentials.json','service-account.json','service_account.json','token.json']:return True
    return False


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    top='SEMI-GUARD_updated_20261020'
    now=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds')
    records=[];names=set()
    guide='''# SEMI-GUARD 수정본 전체 패키지

2026-10-20 수정 기준. LLM Wiki 제거, 공통 CSV 추론과 분석 Tool, Gemini 3.8 Flash,
관제 서브페이지와 월별 표본 선택 오류 수정까지 포함한다.

## 포함 파일
- server, src, web, tools, tests의 전체 소스와 실행 설정
- artifacts의 저장 모델·전처리, data의 SECOM 원본·처리 데이터
- simulation의 4개 CSV, 노트북과 기존 참고 자료
- 기획안 v1.1 Word·HTML, 워크플로우 이미지와 상세 변경 기록
- FILE_MANIFEST.json의 파일별 SHA-256과 크기

가상환경, Git 정보, 캐시, runtime 세션 DB, 실제 .env와 인증서 파일은 포함하지 않는다.
.env.example은 변수 안내용이며 키 값이 비어 있다. frontend Firebase 설정은 기존 공개 클라이언트 설정이다.

## 로컬 실행
Python 3.11에서 압축을 푼 폴더로 이동한다.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 127.0.0.1 --port 8080
```

Windows에서는 .venv\\Scripts\\Activate.ps1로 가상환경을 활성화한다.
CSV 분석실은 http://127.0.0.1:8080/ 이고 관제 화면은 /dashboard/ 이다.
압축 해제 후에는 세션 DB가 새로 생성되므로 simulation 파일을 선택하거나 CSV를 업로드한다.
관제 화면은 엔지니어 또는 관리자 데모로 사용할 수 있다.
macOS의 LightGBM/OpenMP 설정은 README.md의 실행 안내를 따른다.

기본 분석·SHAP·드리프트·표본 진단은 API 키 없이 실행한다.
자연어 질의는 서버 환경에 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 공급해야 한다.
기본 모델은 gemini-3.8-flash이며 GEMINI_MODEL로 지정할 수 있다.
.env는 자동 로드하지 않는다. 운영 계정의 권한 검증과 Cloud Run/GCS 실증은 별도 과제다.

## 검증과 재현
```sh
pip install -r requirements-dev.txt
python -m pytest -q tests
python tools/analyze_wafer.py --sample-id 2184 --include-drift --include-global-shap --output artifacts/analysis_reports/detail_2184.json
```

자동 검증 48개 통과. Gemini의 실제 표본 분석 Tool 호출을 확인했다.
관제 기간의 2009년 9~12월 전환 시 각각 3046/3178/3295/3377 표본이 자동 선택되는지,
전체 기간에서는 유효한 기존 표본이 유지되는지와 혼동행렬 FN 표본의 진단 연결을 확인했다.

새 서비스의 진입점은 server.app:app이다. 루트 app.py는 보존한 기존 Streamlit 평가 앱이다.
tools와 scratch의 과거 정적 화면 생성·치환 스크립트는 참고용이며 현재 웹 파일에 일괄 재실행하지 않는다.
저장 모델을 재학습하거나 Cloud Run에 배포한 패키지가 아니다.
'''
    def write(archive,name,content):
        name=unicodedata.normalize('NFC',name)
        if name in names:raise ValueError('중복 압축 경로: '+name)
        names.add(name);archive.writestr(top+'/'+name,content)
        records.append({'path':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    temporary=args.output.with_suffix('.zip.tmp')
    try:
        with ZipFile(temporary,'x',compression=ZIP_DEFLATED,compresslevel=6) as archive:
            for path in sorted(ROOT.rglob('*')):
                rel=path.relative_to(ROOT)
                if path.is_file() and not path.is_symlink() and not excluded(rel):
                    write(archive,rel.as_posix(),path.read_bytes())
            proposal=ROOT.parent/'반도체_공정_데이터분석_시각화_서비스_기획안_v1.1.docx'
            if proposal.exists():write(archive,'docs/'+proposal.name,proposal.read_bytes())
            write(archive,'PACKAGE_README_KO.md',guide.encode())
            manifest={'created_at':now,'files':records,'file_count':len(records),
                'excluded':'가상환경, 캐시, runtime 세션 DB, 실제 비밀 설정, 기존 ZIP과 백업'}
            archive.writestr(top+'/FILE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode())
        with ZipFile(temporary) as archive:
            bad=archive.testzip()
            if bad:raise ValueError('압축 무결성 오류: '+bad)
            for record in records:
                content=archive.read(top+'/'+record['path'])
                if hashlib.sha256(content).hexdigest()!=record['sha256']:raise ValueError('해시 불일치: '+record['path'])
            required=['server/app.py','server/dashboard_api.py','src/data_analysis/diagnostics.py',
                'web/dashboard/app.js','web/diagnostics.js','requirements.txt','artifacts/baseline_model.joblib',
                'artifacts/preprocessor.joblib','data/raw/secom.data','simulation/sim_batch_400_200909_200912.csv']
            assert all(top+'/'+p in archive.namelist() for p in required)
            script=archive.read(top+'/web/dashboard/app.js').decode()
            assert 'async function renderTriage()' in script and 'await renderTriage()' in script
        temporary.replace(args.output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    checksum=hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix('.zip.sha256').write_text(checksum+'  '+args.output.name+'\n')
    print(json.dumps({'archive':str(args.output.resolve()),'files':len(records)+1,
        'size_mib':round(args.output.stat().st_size/1024**2,2),'sha256':checksum,'verified':True},ensure_ascii=False))


if __name__=='__main__':main()
