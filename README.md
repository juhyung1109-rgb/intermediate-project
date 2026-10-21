# SEMI-GUARD v3.0

CSV 원본 센서와 저장 모델의 추론 결과를 결합해 분석하는 서비스다. LLM Wiki를 데이터셋 범위의 데이터 분석 에이전트와 Python Tool로 교체했다.

- `data/raw/SECOM` 데이터(실제 파일은 `data/raw/secom.data`, `secom_labels.data`)는 기존 학습·평가에서 사용한다. 학습 노트북, Streamlit `app.py`, 저장 모델은 유지한다.
- 업로드 및 `simulation/` CSV는 **저장된 전처리의 transform과 저장 모델 predict_proba**만 수행한다. 재학습하지 않는다.
- 원본 센서와 예측은 정렬 순서가 아닌 `row_id`로 연결한다. 파일 해시·모델 버전·데이터셋 ID로 결과를 추적한다.
- 기본 분석과 Tool 직접 실행은 LLM 키 없이 사용한다. 자연어 질문은 서버의 Gemini 3.8 Flash 함수 호출 루프로 처리한다.

[서비스 기획안](docs/반도체_공정_데이터분석_시각화_서비스_기획서.html) · [상세 설계](docs/SEMI_GUARD_반도체_공정_AI_통합관제_최종_기획서.md) · [simulation 분석 결과](artifacts/analysis_reports/README.md)

## 실행

Python 3.11 기준이다. 저장된 전처리의 scikit-learn 버전은 1.7.2이므로 해당 버전을 고정했다.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 127.0.0.1 --port 8080
```

`http://127.0.0.1:8080`에서 CSV 업로드 또는 simulation 파일 선택 → 기본 분석 → Tool 실행/질문 순서로 사용한다. 파일 전체를 페이지별로 조회하고 원본+예측 CSV를 내려받을 수 있다. `web/sample_secom_590.csv`는 590개 센서가 있는 3행 합성 예제다. 이전 7개 센서 예제는 저장 모델 입력 요건을 충족하지 않아 제거했다.

macOS에서 LightGBM이 `libomp.dylib`를 찾지 못하면 OpenMP 런타임을 설치하거나 기존 호환 라이브러리 디렉터리를 `DYLD_LIBRARY_PATH`로 지정한다. Linux 컨테이너는 Dockerfile이 `libgomp1`을 설치한다. 모델 로드 실패를 데모 예측으로 대체하지 않으며 `/api/health`와 화면에서 오류를 확인할 수 있다.

자연어 질문을 활성화하려면 서버 환경에 `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.8-flash`를 지정한 뒤 재시작한다. 모델 기본값도 `gemini-3.8-flash`다. `GEMINI_API_KEY`가 없으면 `GOOGLE_API_KEY`를 사용한다. `.env.example`은 변수 안내이며 `.env`를 자동 로드하지 않는다. 키는 프런트엔드에 두지 않는다. 질문과 필요한 계산 요약은 외부 LLM에 전송되며 화면에 이를 안내한다.

```sh
export GEMINI_MODEL='gemini-3.8-flash'
# GEMINI_API_KEY는 실행 환경의 비밀 관리 기능으로 공급
uvicorn server.app:app --host 127.0.0.1 --port 8080
```

## 데이터와 분석 계약

UTF-8 CSV, 최대 20 MiB·10,000행·650열을 지원한다. 센서는 `feature_1`~`feature_590`이고 모델에 저장된 232개 필수 피처 열이 모두 있어야 한다. 행 안의 결측은 집계한 뒤 학습 시 저장한 중앙값으로 대체한다. 센서 누락 열, 비수치·무한대, 중복·빈 sample_id, 중복 헤더는 오류로 반환한다. sample_id가 없으면 발급한다. 내부 row_id는 0부터 시작한 원본 행 순서이며 sample_id와 다르다.

`timestamp`는 선택이다. 없으면 시간 분석만 사용할 수 없다. `actual_label` 또는 `label`은 0/1/빈 값이며 선택이다. 라벨이 없으면 실제 불량률·성능은 미확인이다. 부분 라벨의 불량률은 확인 라벨만 분모로 삼고 그 수를 표시한다. 성능 평가는 전체 라벨을 요구한다. 원본 SECOM -1/1 라벨 변환은 초기 학습 로더의 책임이다.

|Tool|계산|
|---|---|
|profile_dataset|행·센서 수, 결측·상수열, 확인 라벨, 위험도 분포|
|rank_samples|위험 순위 및 원본 센서값|
|query_data|조건 필터·컬럼 선택·정렬·그룹 집계|
|compare_groups|상위 검토군과 나머지 센서 평균·표준화 차이|
|correlate|센서와 위험 점수 또는 센서 간 상관·유효 표본 수|
|time_summary|실제 일/주/월별 건수·평균 위험 점수·확인 라벨 불량률|
|compare_reference|SECOM 학습 정상군 1,170행의 원본 센서 분포 대비 이동|
|evaluate_predictions|배치 상위 검토 비율별 혼동행렬·Recall·Precision·Lift|
|explain_sample|실제 저장 모델의 SHAP 기여도·기저값·로그오즈|
|diagnose_sample|표본 ID의 Top 5 센서 상태·정상 참고 구간·실제 누적 SHAP·분류별 검토 권고|
|sensor_drift|실제 시간의 Pearson·Kendall·표준화 기울기·초기후기 이동·상승과 하강|
|global_shap|선택 데이터셋 평균 절대 SHAP·균등 표본 선택과 실제 분석 수|

기본 리포트는 품질·그룹 차이·상관·월별·참고 분포·라벨 성능을 계산하고 질문 후보를 제시한다. Tool의 JSON 인자를 바꾸면 미리 정하지 않은 분석을 조합할 수 있다. 에이전트는 등록 Tool만 호출한다. 임의 Python/SQL/쉘 실행은 지원하지 않는다. 최대 6회 응답 루프·12회 Tool 호출·반환 50행·선택 20열로 제한한다. 계산 근거 없는 LLM 응답은 성공으로 반환하지 않는다. 상관·SHAP은 실제 고장 원인 확정 근거가 아니다.

`src/data_analysis/`: `validation.py` 입력 계약, `inference.py` 저장 모델, `repository.py` 영속 저장, `tools.py` 계산, `service.py` 공통 파이프라인, `agent.py` LLM Tool 루프다. `server/app.py`는 API, `web/`은 분석 UI다.

## API

- `GET /api/health`: 모델·에이전트 설정 상태, Tool 목록
- `POST /api/predict-batch`: multipart CSV → dataset_id·전수 예측·기본 리포트
- `GET /api/simulation`, `POST /api/simulation/{filename}/analyze`: 허용된 파일을 공통 경로로 분석
- `GET /api/datasets`, `GET /api/datasets/{id}?offset=0&limit=50`: 세션별 목록·페이지 조회
- `GET /api/datasets/{id}/report`, `GET /api/datasets/{id}/export`: 리포트·원본+예측 다운로드
- `POST /api/datasets/{id}/tools/{name}`: `{"arguments":{...}}`
- `POST /api/chat`: `{"query":"...","dataset_id":"UUID","conversation_id":null}` → 답변·대화 ID·Tool 근거
- `GET /api/evaluation`: 보관된 SECOM 시험 예측 314행 평가

Wiki API·Wiki 챗봇은 제거했다. 전환 전 파일은 상위 폴더의 archive 사본에서 복구할 수 있다. 기존 학습·평가 노트북은 유지하며 이전 화면 재생성용 tools/scratch 스크립트는 v3 실행 경로에 사용하지 않는다.

## 저장과 실행 환경

로컬 기본값은 `runtime/analysis.sqlite3`다. `DATASET_DB`로 경로를 바꿀 수 있다. 원본·예측을 한 트랜잭션에 저장하고 같은 파일·모델·세션은 중복 등록하지 않는다. 서버가 발급한 HttpOnly 세션 쿠키의 소유 범위로 데이터셋·대화를 격리한다. 현재 방식은 브라우저 세션 기반이므로 쿠키 만료/삭제 후 기존 데이터를 복구하는 계정 연동은 별도 과제다.

Cloud Run의 로컬 디스크는 영속 저장이 아니므로 `DATASET_STORAGE=gcs`, `DATASET_BUCKET=<비공개 버킷>`을 명시해야 시작할 수 있다. 서비스 계정에 해당 버킷만 접근하는 IAM을 설정한다. GCS 구현은 원본·예측을 하나의 압축 객체로 저장하고, 새 데이터셋 생성은 generation 조건으로 중복을 방지한다. 이번 작업에서 실제 GCS와 Cloud Run 배포는 실행하지 않았다.

```sh
docker build -t semiguard:v3 .
# 로컬 컨테이너의 SQLite 보존 예시
mkdir -p runtime
docker run --rm -p 8080:8080 -v "$PWD/runtime:/app/runtime" semiguard:v3
```

## 일괄 분석과 검증

```sh
python tools/analyze_simulation.py
python tools/analyze_simulation.py --file simulation/sim_batch_300_200906_200908.csv --output artifacts/custom_analysis
pip install -r requirements-dev.txt
python -m pytest -q tests
```

4개 simulation 파일 1,400행을 실제 모델로 추론했다. `artifacts/analysis_reports/`의 파일별 JSON과 README에 결과를 기록했다. 상위 20% Recall은 파일별 약 17~35%로, 보관된 SECOM 시험 Recall과 다르다. 시뮬레이션은 합성 데이터이므로 실제 운영 성능으로 해석하지 않는다.

테스트는 원본-예측 행 연결, 입력 오류·미라벨 처리, 실제 CSV 통계와 추론, SHAP 가산성, SQLite 재시작·세션 격리, API·Tool 호출 루프를 확인한다. Gemini 3.8 Flash 실제 API로 월별 분석(time_summary)과 후속 성능 평가(evaluate_predictions)의 Tool 호출·답변을 확인했다. 자동 검증은 총 40개를 통과했으며, GCS 실제 연결은 별도 환경이 필요하다. 시험셋을 모델 선정에 사용한 기존 학습 절차는 독립 평가가 필요하고 이번에 모델을 재학습하지 않았다.

## 실제 화면 시연

`simulation/sim_batch_300_200906_200908.csv`를 웹에서 업로드했다. 기본 분석은 300행·590센서·8,064개 결측 셀을 계산했다. Gemini는 2009-08 불량률 14/101=13.86%를 계산하고, 후속 질의에서 상위 20% 검토 TP=5·FN=17·Recall=22.73%를 답했다.

[기본 분석 화면](docs/demo/01_basic_analysis.jpg) · [Gemini 실제 답변과 Tool 근거](docs/demo/02_gemini_agent.jpg) · [시연 기록](docs/demo/live_demo.json)

## 공정 관제 서브페이지와 기획안 v1.1

같은 서버의 `/dashboard/`에서 엔지니어 또는 관리자 데모를 연다. 기존 Cloud Run 화면의 메뉴와 상세 페이지를 컴퓨터 사용 기능으로 직접 눌러 검토한 뒤 구현했다. [직접 조작 검토 기록](docs/dashboard_reference_review.md)에 원격 기능과 로컬 구현의 대응을 기록했다. CSV 분석실과 데이터셋을 공유한다.

- 표본 검색과 실제 SHAP 진단, TP/FP 비교 및 단독 표시
- 선택 기간의 월별·실제 7일 이동 불량률, 차트 PNG 다운로드
- 5~50% 검토 비율별 성능, AP·혼동행렬과 전체 표본 TP/FP/FN/TN 탐색
- 학습 정상군 1170행 대비 232센서 평균 이동·표준편차 비·KS 거리
- 수동 점검 발령 → 체크리스트·완료 보고 → 승인 또는 보완 요청과 이력 저장
- CSV 업로드, simulation 선택, SECOM 시험 314행 불러오기, 기간별 Markdown·예측 CSV 다운로드
- 선택 데이터셋과 기간에 제한된 Gemini Tool 질의와 현재 서버 주소 QR

기간과 비율이 달라지면 순위와 표본 분류를 다시 계산한다. 대화도 데이터셋·기간·비율 문맥을 구분한다. 여름 CSV의 8월 101행을 25% 검토할 때 26행을 선정하고 TP 6·FP 20·FN 8·TN 67을 표시했다. 같은 기간의 실제 Gemini 질의는 Python Tool로 확인 불량 14건, 13.86%를 계산했다.

로컬에서 점검 지시를 등록하고 완료 보고·승인까지 직접 눌렀고, SECOM 불러오기·CSV 업로드·보고서와 CSV 다운로드를 확인했다. 자동 검증은 총 **40개 통과**다. `/proposal/v1.1`에는 최초 Word 기획과 중간 v2.5, 현재 코드를 구분한 변경표와 에이전트 영역을 표시한 워크플로우 이미지를 제공한다. Word 파일과 HTML은 상위 프로젝트 폴더에 별도로 보관한다.

Firebase 로그인·회원가입 폼은 기존 SDK 설정을 사용하지만 실제 계정 생성은 검증하지 않았다. API의 데이터 소유 범위는 브라우저 세션이다. 엔지니어·관리자 버튼과 점검 승인은 로컬 시연 기능이며 서버의 운영 계정 권한 검증은 후속 작업이다. Cloud Run과 GCS 실제 배포·연결은 수행하지 않았다.

## 상세 분석 기능 확장

기존 `tools/`의 정적 상세 생성 스크립트와 `src/analysis.py`를 검토하고, CSV 분석실과 관제 화면에 실제 계산 함수를 연결했다. 현재 등록 Tool은 12개다. [소스 대조와 계산 기준](docs/detail_analysis_changes.md)에 고정 센서값·임의 SHAP·추정 날짜를 사용하는 과거 경로와 현재 구현의 차이를 기록했다.

CSV 분석실의 **표본 정밀분석과 점검 권고**에서 sample_id를 검색하거나 전체 예측 표의 **정밀분석** 버튼을 누른다. Top 5 센서와 학습 정상군 중앙값·평균·표준편차·5~95% 참고 구간, 결측과 상태를 표시한다. Z는 평균 기준이며 중앙값을 평균으로 표기하지 않는다. SHAP은 상위 8개와 나머지 전체 피처를 합산해 최종 모델 출력과 일치하는 워터폴로 그린다. TP/FP/FN/TN/미라벨에 따른 권고와 계산 근거를 함께 제공한다.

**전체 SHAP 중요도 분석**과 **시간 드리프트 분석**은 LLM 없이 실행한다. 전체 SHAP은 기본 최대 200행을 원본 순서의 균등 간격으로 선택하고 200/500처럼 실제 분석 수를 표시한다. 시간 드리프트는 실제 경과 일수와 결측 제외 원본값으로 계산하고 상승·하강·전체 방향 필터를 제공한다. 엄격한 조건에 맞는 센서가 없으면 빈 결과를 표시한다.

관제 서브페이지도 같은 분석과 공통 렌더러를 사용한다. SHAP 비교 화면에 전체 중요도 버튼, 분포 변화 화면에 시간 드리프트 통계·월별 센서 추이, 표본 상세에 에이전트 질문과 점검 지시 초안 버튼을 추가했다. 초안은 사람이 검토한 뒤 등록하며 실제 설비 정지나 제품 통과·폐기를 자동 결정하지 않는다.

```sh
python tools/analyze_wafer.py --sample-id 2184 --include-drift --include-global-shap --output artifacts/analysis_reports/detail_2184.json
```

표본 2184의 실제 센서·SHAP·권고, Gemini의 신규 Tool 호출과 200/500행 전체 중요도 계산을 화면에서 확인했다. 자동 검증 **48개 통과**. [표본 상세 화면](docs/demo/06_wafer_detail.jpg) · [CLI 분석 결과](artifacts/analysis_reports/detail_2184.json).


월별 관제 기간 변경 시 이전 표본이 해당 월에 없으면 월 내 위험 순위 1위로 자동 변경해 진단한다. 해당 월에 포함되는 기존 선택은 유지한다. 기간 갱신 중 이전 요청의 결과와 오류는 현재 화면에 반영하지 않는다. 2009년 9~12월 전환과 혼동행렬의 FN 표본 진단 연결을 직접 검증했다.
