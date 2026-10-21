from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, html, shutil

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
ASSETS = APP / 'docs/assets'
ASSETS.mkdir(parents=True, exist_ok=True)
import os
FONT = os.getenv('WORKFLOW_FONT', '/System/Library/Fonts/AppleSDGothicNeo.ttc')
# Linux: WORKFLOW_FONT=/path/to/NotoSansCJK-Regular.ttc
def font(size): return ImageFont.truetype(FONT, size)
def make_canvas(title, subtitle):
    im = Image.new('RGB', (2048, 1260), '#f3f6fc')
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 2048, 155), fill='#132540')
    d.text((60, 30), title, font=font(49), fill='white')
    d.text((62, 97), subtitle, font=font(25), fill='#c6dbf6')
    return im, d
def box(d, x, y, title, lines, color='#ffffff', accent='#2467c8'):
    d.rounded_rectangle((x,y,x+440,y+180), radius=20, fill=color, outline='#cfdaea', width=2)
    d.rounded_rectangle((x+20,y+24,x+26,y+62), radius=3, fill=accent)
    d.text((x+42,y+23),title,font=font(31),fill='#142a48')
    for j,line in enumerate(lines): d.text((x+28,y+81+j*33),line,font=font(24),fill='#43546e')
def arrow(d, pts, label=None, xy=None, color='#52749f'):
    d.line(pts, fill=color, width=5, joint='curve')
    x,y=pts[-1]; px,py=pts[-2]
    if abs(x-px)>abs(y-py):
        sign=1 if x>px else -1;tri=[(x,y),(x-sign*16,y-10),(x-sign*16,y+10)]
    else:
        sign=1 if y>py else -1;tri=[(x,y),(x-10,y-sign*16),(x+10,y-sign*16)]
    d.polygon(tri,fill=color)
    if label: d.text(xy,label,font=font(24),fill=color)

im,d=make_canvas('SEMI-GUARD · 데이터 워크플로우', 'v3.0 설계 | SECOM 학습·평가와 사용자 CSV 추론을 분리하고, 분석 데이터로 연결')
d.text((60,182),'A. 학습·평가 경로 — 기존 SECOM 활용',font=font(30),fill='#216342')
box(d,60,245,'SECOM 원본',['data/raw/ · 1,567행 × 590센서','특징 + 라벨 + 측정 시각'], '#eaf6f0','#26986c')
box(d,550,245,'학습·시험 분리',['학습: 전처리·모델 fit','시험: transform · 지표 평가'], '#eaf6f0','#26986c')
box(d,1040,245,'버전이 고정된 모델',['전처리 + 필수 피처 목록','LightGBM · model_version'], '#eaf6f0','#26986c')
box(d,1530,245,'평가·정상 참고 분포',['시험 지표는 범위를 명시','학습 정상군 통계 버전 보관'], '#eaf6f0','#26986c')
for x in [500,990,1480]:arrow(d,[(x,335),(x+50,335)])
d.text((60,550),'B. 신규 데이터 경로 — 업로드별 독립 추론·탐색',font=font(30),fill='#1d55a4')
box(d,60,625,'CSV 업로드·검증',['simulation/*.csv 또는 사용자 파일','결측·ID·센서 열·라벨 검사'])
box(d,550,625,'저장된 모델로 추론',['전처리는 transform만 수행','업로드 시 재학습하지 않음'])
box(d,1040,625,'분석 데이터셋 보관',['dataset_id · 고유 행 ID','원본 센서 + 예측 + 모델 버전'])
box(d,1530,625,'Python 분석 Tool',['기본 EDA · 비교 · 상관 · 시계열','성능 평가 · 실제 SHAP'])
for x in [500,990,1480]:arrow(d,[(x,715),(x+50,715)])
arrow(d,[(1260,425),(1260,490),(770,490),(770,625)],'동일 전처리·모델 적용',(785,500),'#26986c')
d.rounded_rectangle((60,915,1970,1180),radius=22,fill='#e6ecf8')
for j,line in enumerate(['데이터 범위: simulation/ 4개 CSV · 총 1,400행 · 모든 파일 590개 센서',
                         '초기 분석: 품질 진단 → 위험군 특성 → 시간별 변화 → 정상 참고 분포 차이 → 다음 질문 제안',
                         '정답 라벨 미제공: 예측·탐색은 가능 / 실제 불량률·Recall·혼동행렬은 미산출',
                         '로컬: SQLite 저장 / Cloud Run: GCS 저장소 설정 · 데이터셋은 세션별로 접근 제한']):
    d.text((90,950+j*51),line,font=font(28),fill='#253e63')
im.save(ASSETS/'data_workflow_v3.png')

im,d=make_canvas('SEMI-GUARD · 서비스 워크플로우', 'v3.0 설계 | 실제 계산 결과를 근거로 분석 후보를 제안하고, 후속 질문에 따라 Tool을 선택')
top=[('CSV 선택·업로드',['파일 규격·필수 센서 확인','오류는 행·컬럼과 함께 안내']),
     ('추론·기본 분석',['모델 위험 점수 산출','품질·시간·위험군 통계 계산']),
     ('분석 주제 살펴보기',['계산된 사실과 표·차트 제공','가능한 후속 질문을 제안']),
     ('질문·데이터셋 선택',['질문 + dataset_id + 대화 ID','현재 업로드 범위를 명시'])]
for i,(t,ls) in enumerate(top):box(d,60+490*i,235,t,ls)
for x in [500,990,1480]:arrow(d,[(x,325),(x+50,325)])
d.rounded_rectangle((520,465,1995,915),radius=26,fill='#e8e4fb',outline='#7350bd',width=5)
d.text((550,480),'데이터 분석 에이전트',font=font(32),fill='#563397')
bottom=[('답변·다운로드',['표·차트·분석 방법·표본 수','후속 질문은 같은 데이터로 연결']),
        ('계산 근거 검토',['Tool 실행 결과를 LLM에 반환','불확실성·누락 조건을 명시']),
        ('Python Tool 실행',['필터·비교·상관·시계열·SHAP','허용된 분석 요청만 실행']),
        ('분석 에이전트 계획',['필요한 Tool·파라미터 선택','결과에 따라 추가 분석 선택'])]
for i,(t,ls) in enumerate(bottom):box(d,60+490*i,680,t,ls,'#eef1ff','#6a56c9')
arrow(d,[(1750,415),(1750,680)])
for x in [1530,1040,550]:arrow(d,[(x,770),(x-50,770)])
arrow(d,[(770,680),(770,535),(1750,535),(1750,680)],'필요 시 추가 Tool 호출 · 횟수와 실행 범위 제한',(870,552),'#7156bc')
d.rounded_rectangle((60,970,1970,1175),radius=22,fill='#e6ecf8')
for j,line in enumerate(['핵심 연결: 원본과 예측 결과는 고유 행 ID로 결합 · 원본값을 설명문에서 복원하지 않음',
                         'LLM 설정 전에도 기본 분석 Tool 사용 가능 · 미설정 상태를 가짜 챗봇 답변으로 대체하지 않음',
                         '정답 없는 성능 평가, 통계적 연관을 고장 원인으로 단정, 장비 자동 조작은 수행하지 않음']):
    d.text((90,1007+j*52),line,font=font(27),fill='#253e63')
im.save(ASSETS/'service_workflow_v3.png')

profile=json.loads((APP/'docs/simulation_inventory.json').read_text())
(APP/'docs/simulation_inventory.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2))
rows='\n'.join(f"| `{p['file']}` | {p['rows']} | {p['failures']} | {p['failures']/p['rows']*100:.2f}% | {p['missing_cells']:,} |" for p in profile)
md=f'''# SEMI-GUARD v3.0 — CSV 추론·탐색 데이터 분석 에이전트 기획안

기준일: 2026-10-20 · 수행: 박주형 · 상태: 구현 및 로컬 검증 완료 · Gemini 3.8 Flash 실제 질의 검증 완료 · GCS 연결은 별도 검증

## 1. 목적과 범위
SECOM 원본은 모델 학습·시험 평가에 사용한다. 사용자가 업로드한 CSV는 저장된 전처리·모델로 추론한다. 원본 센서와 예측 결과를 고유 행 ID로 결합해 데이터셋별로 보관하고, 탐색적 분석 에이전트가 Python Tool을 선택·실행하여 질문에 답한다. LLM Wiki, 문서 키워드 답변, 설명문 기반 수치 생성, 벡터 RAG는 서비스 실행 경로에서 제거한다.

업로드는 학습 데이터 자동 추가나 재학습을 의미하지 않는다. 기존 SECOM 학습·평가 노트북과 모델을 유지하되, 시험 데이터를 이용한 모델 선정 문제는 별도 재평가 과제로 기록한다. 시뮬레이션은 합성 검증 데이터이며 실제 설비 이력으로 소개하지 않는다. 물리 센서 의미·고장 원인·정비 조치는 검증된 메타데이터 없이 단정하지 않는다.

## 2. 데이터 워크플로우
![데이터 워크플로우](assets/data_workflow_v3.png)

학습과 추론은 저장된 전처리 계약을 공유한다. 학습에서만 fit하고 신규 데이터는 transform만 수행한다. 데이터 추가로 기존 모델을 덮어쓰지 않는다. 기본 590개 센서 템플릿을 제공하며 실제 추론에는 모델의 valid_features 열을 모두 요구한다. 행 내부 결측은 허용·집계하고 학습 중앙값으로 대체한다. 누락 열, 비수치, 무한대, 중복 표본 ID는 명확한 검증 오류로 처리한다. 측정 시각은 추론의 필수 특성이 아니며 없을 때 시계열 분석만 사용할 수 없다. actual_label은 선택값이며 0/1만 허용한다. 원본 SECOM의 -1/1 변환은 초기 데이터 로더에서만 수행한다.

## 3. 서비스 워크플로우
![서비스 워크플로우](assets/service_workflow_v3.png)

보라색 테두리의 데이터 분석 에이전트 영역은 LLM 분석 계획, Python Tool 실행, 계산 근거 검토와 추가 Tool 호출 루프를 포함한다. CSV 업로드·기본 분석·분석 주제 표시·질문 입력·최종 결과 표시와 다운로드는 서비스 UI 및 데이터 처리 계층으로 구분한다.

CSV 업로드 → 검증 → 모델 추론 → 원본·예측 저장 → 기본 EDA와 질문 후보 → 질문과 dataset_id 전달 → LLM 계획 → Python Tool 계산 → 추가 분석 또는 답변. 서버가 발급한 세션으로 데이터셋을 격리하고 대화도 해당 데이터셋에 고정한다. 기본 통계는 API 키 없이 계산되며 자연어 에이전트는 Gemini 3.8 Flash(gemini-3.8-flash)를 사용하며, GEMINI_API_KEY 또는 GOOGLE_API_KEY 설정 후 작동한다. GEMINI_MODEL로 모델 ID를 명시할 수 있다. 설정이 없거나 추론이 실패하면 명시적 상태·오류를 반환하며 준비된 데모 예측으로 대체하지 않는다.

## 4. simulation CSV 실측 현황
다음 수치는 파일을 직접 읽어 집계했다. 기존 문서의 ‘매월 100건’ 가정을 사용하지 않는다.

| 파일 | 행 수 | 라벨 1 | 불량률 | 결측 센서 셀 |
|---|---:|---:|---:|---:|
{rows}

총 1,400행·590개 센서, 파일 내부 sample_id 중복 0건. 여름 배치의 월별 건수는 98/101/101이고 2009-08 라벨 불량률은 14/101=13.86%다. 가을 배치는 98/102/99/101건이다. 시간별 수율과 원인·회복 가설은 구분한다. 상세 집계는 simulation_inventory.json에 보관한다.

## 5. 기본 분석 Tool과 선택 근거
| Tool | 분석 내용·선택 이유 | 데이터 조건 |
|---|---|---|
| profile_dataset | 행·센서 수, 결측률, 상수열, 라벨·예측 분포: 모든 CSV의 첫 진단 | 센서값 |
| rank_samples | 위험 점수 상위/하위 표본과 센서값 조회 | 예측 결과 |
| query_data | 컬럼 선택·조건 필터·정렬·그룹 집계: 미리 정하지 않은 질문에 조합 가능 | 허용된 컬럼·연산 |
| compare_groups | 고위험 20%와 나머지의 센서 평균·표준화 차이 | 같은 모델의 예측 |
| correlate | 센서-위험 점수 또는 센서 간 상관과 유효 표본 수 | 숫자·최소 표본 수 |
| time_summary | 실제 월/일/주별 표본 수·위험 점수·확인된 라벨 불량률 | 측정 시각 |
| compare_reference | 고정된 SECOM 학습 정상군 대비 평균 이동·기준 표준편차 차이 | 버전 고정 참고 분포 |
| evaluate_predictions | 상위 검토 비율별 TP/FP/FN/TN·Recall·Precision·Lift | 전체 평가 표본 정답 필요 |
| explain_sample | 실제 TreeExplainer로 해당 표본의 기여도·기저값·모델 점수 제공 | 모델·전처리·SHAP |

기본 리포트는 품질 진단, 월별 변화, 위험군 차이, 위험 점수 관련 센서, 정상 참고 비교, 조건이 맞는 성능 평가를 계산한다. 에이전트가 결과를 보며 도구를 반복 선택할 수 있다. 1차 구현은 임의 Python 코드 실행 대신 등록 Tool의 구조화된 인자를 사용하고, 일반 질의·집계 Tool로 범위를 확장한다. 호출 횟수·반환 행·컬럼을 제한하며 Tool 실패를 계산된 사실처럼 설명하지 않는다. SHAP 누락 시 가짜 기여도를 생성하지 않는다.

## 6. 데이터 계약·저장·추적성
- dataset_id: 서버 생성 UUID. 원본 행별 내부 row_id를 발급하고 sample_id는 원천 식별자로 보관한다.
- metadata: 파일명·해시, 소유 세션, 등록·측정 시각, source_type, model_version, schema_version, 표본 수와 결측 요약.
- 원본 센서값과 모델 입력 대체값을 구분한다. 순위는 데이터셋·조건·검토 비율별로 계산한다.
- 로컬 SQLite는 프로세스 재시작 후 데이터셋·대화를 보존한다. Cloud Run에서는 DATASET_STORAGE=gcs와 DATASET_BUCKET을 명시한다. 임시 로컬 디스크를 영속 저장으로 소개하지 않는다.
- LLM에는 질문과 필요한 계산 요약을 전송한다. 원본 전체 CSV를 매번 프롬프트에 삽입하지 않는다. 외부 LLM 사용 사실을 화면에 알린다.

## 7. API·화면 변경
- POST /api/predict-batch: 파일 검증·공통 추론·dataset_id와 결과 반환. 이전 results/full_results 응답 호환.
- GET /api/datasets 및 /api/datasets/{{id}}: 접근 가능한 데이터셋 목록·요약·원본/예측 결합 조회.
- POST /api/datasets/{{id}}/tools/{{tool_name}}: 분석 Tool 직접 실행.
- GET /api/datasets/{{id}}/report: 기본 EDA·분석 후보와 근거 반환.
- POST /api/chat: query, dataset_id, conversation_id를 받아 실제 Tool 호출 루프 실행.
- GET /api/simulation: 프로젝트 simulation/의 허용된 CSV 목록. 선택 파일을 동일 업로드 경로로 처리.
- 웹 분석실: CSV 업로드/시뮬레이션 선택, 현재 데이터셋, 기본 분석, Tool 실행 결과와 차트, 질문·후속 대화, 원본·예측/리포트 다운로드.

## 8. Wiki 제거와 기존 기능 유지
활성 API의 wiki/list·add·tree·doc 및 키워드 챗봇, Wiki→드리프트·점검 연결을 제거한다. Wiki 문서와 전용 동기화 스크립트는 실행 경로에서 제거하고 전환 전 사본을 별도 보관한다. AGENTS.md의 Wiki-First 규약은 본 설계와 일치하게 갱신한다. Dockerfile의 Wiki COPY도 제거한다. 기존 학습·평가 기능은 유지하며 정적 데이터 기반 대시보드는 과거 평가/데모 범위로 표시하고 새 업로드 분석실과 구분한다. 기존 위키와 합성 데이터의 물리 원인 문구를 새 분석 근거로 사용하지 않는다.

## 9. 구현 순서와 검증 기준
1. 본 기획안과 PNG 데이터·서비스 워크플로우를 먼저 갱신한다.
2. simulation 파일 기반 기본 분석 모듈·공통 추론·저장소를 구현한다.
3. 자연어 에이전트의 Tool 스키마·실행 루프·API를 연결한다.
4. Wiki UI를 분석실로 교체하고 기존 CSV 업로드도 같은 데이터셋 경로로 연결한다.
5. 4개 CSV 전수 집계·추론, 행 ID 결합, 재시작 보존, 세션 격리, 미라벨·결측·오류 처리, Tool 호출 루프, 웹 화면을 검증한다.

## 10. 완료 기준·제약
파일 통계와 Tool 계산이 일치하고, 사용자가 선택한 파일의 전체 행을 질의할 수 있어야 한다. 정답 미제공 시 실제 불량 지표는 null/미확인으로 제공한다. 모델·전처리/필수 피처가 없으면 추론 실패를 반환한다. 외부 LLM 라이브 호출은 유효한 서버 환경 설정이 있어야 검증할 수 있으며, 모의 Tool 호출 검증과 구분해 기록한다. 기획안의 ‘설계’와 검증 후 ‘구현’ 상태를 구분한다. 현재 작업에는 라이브 Cloud Run 배포와 자동 모델 재학습·장비 인터락 실행이 포함되지 않는다.

## 11. 구현·검증 결과
실제 저장 모델(버전 777d4a5683437110b7ec)로 simulation 4개 파일 1,400행의 전수 추론과 기본 분석을 완료했다. 입력·행 결합·저장·접근 범위·미라벨·실제 SHAP 가산성·API·모의 LLM Tool 루프에 대한 자동 검증을 통과했다. 웹에서 simulation 선택 후 300행과 590센서, 조건 집계, 전체 결과 페이지 이동을 확인했다. Gemini 3.8 Flash 실제 API로 월별 분석과 후속 성능 평가의 Tool 호출·답변을 확인했다. 자동 검증 35개가 통과했다. 2009-08 불량률 14/101=13.86%, 상위 20% 검토 TP=5·FN=17·Recall=22.73%를 실제 질의로 확인했고 docs/demo/에 화면과 기록을 보관했다. GCS 영속 저장은 자격 증명이 있는 환경에서 추가 검증해야 한다.

| 파일 | 표본 | 상위 20% 검토 Recall |
|---|---:|---:|
| 2008-11~2009-03 | 500 | 35.48% |
| 2009-04~05 | 200 | 22.22% |
| 2009-06~08 | 300 | 22.73% |
| 2009-09~12 | 400 | 16.67% |

합성 데이터에서 계산한 파일별 평가이며 기존 SECOM 시험셋 성능·실제 설비 성능과 구분한다. 코드·실행법은 기존코드/README.md, 재현 실행은 tools/analyze_simulation.py, 분석 근거는 artifacts/analysis_reports/에 보관했다.

## 12. 참고
- Gemini Function Calling: https://ai.google.dev/gemini-api/docs/function-calling
- Cloud Run 파일 시스템 계약: https://docs.cloud.google.com/run/docs/container-contract
'''
(APP/'docs/SEMI_GUARD_반도체_공정_AI_통합관제_최종_기획서.md').write_text(md)

# Render a self-contained readable HTML proposal; images are local project assets.
import re
parts=[]; table=[]; in_code=False
def flush():
 global table
 if table:
  data=[r for r in table if not re.match(r'^\|[ :|\-]+\|$',r)]
  parts.append('<div class="table-wrap"><table>'+''.join('<tr>'+''.join(f'<{"th" if i==0 else "td"}>{inline(c.strip())}</{"th" if i==0 else "td"}>' for c in r.strip('|').split('|'))+'</tr>' for i,r in enumerate(data))+'</table></div>');table=[]
def inline(s):
 s=html.escape(s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 return s
for line in md.splitlines():
 if line.startswith('|'):table.append(line);continue
 flush()
 if not line:continue
 if line.startswith('# '):continue
 if line.startswith('## '):parts.append('<h2>'+inline(line[3:])+'</h2>');continue
 m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
 if m:parts.append(f'<figure><a href="{m[2]}"><img src="{m[2]}" alt="{m[1]}"></a><figcaption>{m[1]} · 클릭하면 원본 이미지</figcaption></figure>');continue
 if line.startswith('- '):parts.append('<p class="item">'+inline(line[2:])+'</p>');continue
 parts.append('<p>'+inline(line)+'</p>')
flush()
css='''*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#1e304b;font:16px/1.85 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}.hero{background:#132540;color:#fff;padding:55px max(5vw,24px)}.hero span{color:#9fc9ff;font-size:14px;letter-spacing:2px}.hero h1{font-size:clamp(28px,4vw,46px);line-height:1.35;margin:14px 0}.hero p{color:#c6d6ee;max-width:950px}main{max-width:1320px;margin:auto;padding:30px 28px 90px}h2{margin-top:55px;border-top:2px solid #d7e1ef;padding-top:24px;font-size:25px}p{overflow-wrap:anywhere}.item{padding-left:20px;border-left:3px solid #d2dfef}figure{margin:25px 0;background:white;padding:12px;border:1px solid #d7e1ef;border-radius:14px}img{width:100%;height:auto;display:block}figcaption{color:#60718b;text-align:center;font-size:14px}.table-wrap{overflow:auto;background:white;border:1px solid #d6e0ee;border-radius:10px}table{border-collapse:collapse;width:100%;min-width:760px;font-size:14px}th,td{border-bottom:1px solid #e5ebf3;padding:13px 16px;text-align:left;vertical-align:top}th{background:#eaf0fa}code{background:#e7edf6;padding:2px 5px;border-radius:4px;color:#23477c}a{color:#2467c8}.pill{background:#315a91;color:#fff;border-radius:20px;padding:5px 15px;font-size:14px}@media print{.hero{padding:20px}main{padding:0}h2{break-after:avoid}figure{break-inside:avoid}}'''
out=f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SEMI-GUARD v3.0 데이터 분석 에이전트 기획안</title><style>{css}</style><header class="hero"><span>SEMI-GUARD · PRODUCT & DATA DESIGN</span><h1>CSV 추론과 탐색적 데이터 분석<br>에이전트 서비스 기획안</h1><p>SECOM 학습·평가 흐름을 유지하고, 업로드한 원본 센서와 모델 예측에 근거해 분석 주제를 제안하고 질문에 답합니다.</p><b class="pill">v3.0 · 2026.10.20 · 구현·로컬 검증 반영</b></header><main>'+''.join(parts)+'</main></html>'
doc=APP/'docs/반도체_공정_데이터분석_시각화_서비스_기획서.html'
doc.write_text(out)
rootout=out.replace('src="assets/','src="기존코드/docs/assets/').replace('href="assets/','href="기존코드/docs/assets/')
(ROOT/'반도체_공정_데이터분석_시각화_서비스_기획서.html').write_text(rootout)
print('기획안 HTML 2개·Markdown 1개, PNG 2개, CSV 실측 목록 생성 완료')
