# SEMI-GUARD 수정본 전체 패키지

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

Windows에서는 .venv\Scripts\Activate.ps1로 가상환경을 활성화한다.
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
