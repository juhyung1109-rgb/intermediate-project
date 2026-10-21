"""Create the revision comparison in Word and a self-contained HTML companion."""
from pathlib import Path
import base64
import html
import json

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
ASSETS = APP / 'docs/assets'
STEM = '반도체_공정_데이터분석_시각화_서비스_기획안_v1.1'
data = json.loads((APP / 'docs/revision_v1_1_content.json').read_text())
pages = data['pages'][:3]
pages[2]['paragraphs'] = ['웹 서비스는 기본 CSV 분석실과 공정 관제 서브페이지로 구성한다. 서브페이지는 기존 배포 화면의 버튼과 상세 페이지를 직접 확인한 뒤 구현했다. 두 화면은 같은 데이터셋 저장소와 추론 파이프라인을 사용한다. 기존 Streamlit과 학습 코드는 보존한다.']
rows = pages[2]['tables'][0]['rows']
rows[2][2] = '유지와 추가. 관제 서브페이지에 5~50% 슬라이더, AP와 비율별 성과를 구현. 선택 기간 안에서 다시 순위를 계산하고 혼동행렬과 목록을 동기화.'
rows[3][2] = '변경과 추가. SVG 차트의 마우스 수치와 PNG 저장, 표본 센서 편차, TP/FP 실제 SHAP 비교를 제공. 원안의 Plotly 확대, 히스토그램과 박스플롯 전체는 미연결.'
rows[4][2] = '유지와 변경. 관제 서브페이지는 현재 기간과 비율의 Markdown 보고서 및 원본과 예측 CSV를 제공. 기본 분석실은 JSON 보고서를 제공.'
dashboard_note = '추가된 관제 화면은 엔지니어와 관리자 데모, 월별 및 7일 추이, 전수 표본 필터, 학습 정상군 대비 분포 변화, 수동 점검 등록·보고·승인·보완 이력을 포함한다. 화면 역할 전환은 운영 계정의 권한 검증이 아닌 로컬 업무 흐름 시연이다.'
pages[2]['after'] = list(dict.fromkeys([*pages[2]['after'], dashboard_note]))


def table(title, headers, rows, widths):
    return {'title': title, 'headers': headers, 'rows': rows, 'widths': widths}


pages += [
    {'title': '04 데이터 워크플로우', 'image': 'data_workflow_v1_1.png',
     'paragraphs': ['학습과 추론은 저장된 전처리 계약을 공유한다. 사용자 파일을 초기 학습 데이터에 합치지 않는다. 시험 314행을 화면에 불러오는 기능도 저장 모델 추론 경로를 사용하며 별도 학습을 수행하지 않는다.'],
     'after': ['추론 후 원본 센서와 예측을 row_id로 결합한다. 표본 ID, 파일 해시, 모델 버전과 데이터셋 ID를 보관하므로 정렬과 필터 이후에도 원본을 추적할 수 있다.',
               '학습 정상 1170행은 분포 비교 참고군이다. 사용자가 선택한 기간과 검토 비율은 각 화면의 집계와 표본 범위에 함께 적용한다. 기간별 지표를 전체 파일 지표와 섞어 표시하지 않는다.',
               '로컬 저장은 SQLite다. 서버 세션 쿠키의 소유 범위로 데이터셋·대화·점검을 격리한다. 업로드 시 재학습, 파일 간 자동 누적, 운영 계정 간 공유는 구현 범위에 포함하지 않는다.']},
    {'title': '05 서비스 워크플로우', 'image': 'service_workflow_v1_1.png',
     'paragraphs': ['CSV 등록 뒤 기본 분석은 Python으로 계산한다. 질문이 들어오면 데이터셋 범위와 함께 Gemini에 전달하고, 에이전트가 필요한 Tool과 인자를 선택한다. 보라색 테두리가 데이터 분석 에이전트 영역이다.'],
     'after': ['분석실의 질의는 데이터셋에 고정하고, 관제 서브페이지의 질의는 데이터셋·선택 기간·검토 비율 문맥을 구분해 대화를 저장한다. 비율 변경을 직접 요청한 분석은 Tool 인자로 계산할 수 있으며 계산에 사용한 비율을 근거에 표시한다.',
               '데이터 분석 에이전트는 계획, 허용 Tool 실행과 결과 검토 루프를 포함한다. 업로드 검증·모델 추론·기본 EDA·결과 화면·점검 승인은 서비스 계층의 책임이다.',
               '점검 지시는 사람이 통계 결과를 보고 등록한다. 실무자의 항목 확인과 보고 뒤 관리자가 승인 또는 보완 요청한다. 에이전트가 장비를 조작하거나 점검을 자동 발령하지 않는다.']},
    {'title': '06 분석 도구와 에이전트 계약',
     'paragraphs': ['분석 주제가 아직 정해지지 않은 상황을 지원하기 위해 기본 분석과 질문 후보를 제공한다. 새로운 질문은 아래 9개 함수의 조합으로 처리한다. 임의 Python 코드, SQL, 쉘을 생성해 실행하는 에이전트는 사용하지 않는다.'],
     'tables': [table('등록된 Python Tool', ['Tool', '계산 내용과 사용 조건'], [
         ['profile_dataset', '행과 센서 수, 결측, 상수열, 라벨 확인과 위험 점수 분포'],
         ['rank_samples', '위험 순위와 원본 센서값을 함께 조회'],
         ['query_data', '허용 컬럼과 연산으로 필터·정렬·선택·그룹 집계'],
         ['compare_groups', '상위 검토군과 나머지의 평균과 표준화 차이'],
         ['correlate', '센서와 위험 점수 또는 센서 간 상관과 유효 표본 수'],
         ['time_summary', '실제 측정 시각의 일·주·월별 표본 수와 확인 라벨 불량률'],
         ['compare_reference', '학습 정상군의 원본 센서 분포와 비교'],
         ['evaluate_predictions', '전체 라벨이 있을 때 검토 비율별 TP·FP·FN·TN과 Recall·Precision·Lift'],
         ['explain_sample', '저장 모델의 실제 Tree SHAP 기여도와 기저값 및 log-odds']
     ], [5.2, 11.4])],
     'after': ['기본 분석 6종은 품질, 위험군 차이, 상관, 월별 변화, 정상 참고 분포, 라벨 성능이다. 별도의 LLM 호출 없이 계산한다. 미라벨 데이터에서도 예측과 탐색은 가능하지만 실제 성능은 미확인으로 표시한다.',
               'Gemini 3.8 Flash의 기본 모델 ID는 gemini-3.8-flash다. 서버 환경의 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 사용하고 GEMINI_MODEL로 변경할 수 있다. 키를 프런트엔드에 넣지 않는다.',
               '최대 6회 응답 루프와 12회 Tool 호출로 제한하고 조회 결과는 50행과 선택 20열까지 반환한다. 계산 성공 근거 없이 최종 답변을 성공으로 처리하지 않는다. 질문과 필요한 계산 요약은 Google Gemini에 전송한다.']},
    {'title': '07 로컬 검증 결과와 해석 범위',
     'paragraphs': ['실제 파일을 읽어 4개 simulation CSV 총 1400행을 저장 모델로 추론했다. 합성 데이터의 수치를 운영 설비 성능으로 일반화하지 않는다. 이번 변경으로 모델과 전처리를 재학습하거나 교체하지 않았다.'],
     'tables': [table('시뮬레이션 실측', ['파일 구분', '행 수', '정답 불량', '센서 결측 셀', '상위 20% Recall'], [
         ['2008년 11월~2009년 3월', '500', '31', '13253', '35.48%'],
         ['2009년 4~5월', '200', '9', '5280', '22.22%'],
         ['2009년 6~8월', '300', '22', '8064', '22.73%'],
         ['2009년 9~12월', '400', '12', '10367', '16.67%']
     ], [5.4, 1.7, 2.2, 3.1, 4.2]),
         table('화면에서 직접 확인한 동작', ['검증', '관측 결과'], [
             ['기간과 검토 비율', '여름 CSV의 8월 101행, 25% 검토 시 26행 선정. TP 6, FP 20, FN 8, TN 67.'],
             ['표본 상세 연결', 'FN 필터에서 표본 2990을 진단해 같은 기간의 순위 55와 실제 SHAP 표시.'],
             ['Gemini 실제 질의', '선택한 8월만 분석해 101행, 확인 불량 14건, 불량률 13.86%를 Tool 1회로 계산.'],
             ['점검 업무', '로컬 시연 지시 등록, 항목 확인, 완료 보고, 관리자 승인과 승인 이력 표시.'],
             ['자동 검증', '원본 연결, 스키마, 소유 범위, 기간 재집계, 대화 격리, 점검 전이 등 40개 통과.']
         ], [3.8, 12.8])],
     'after': ['보관된 SECOM 시험 314행의 상위 20% 결과는 63행 중 불량 15건을 발견해 15/21=71.43%다. 이는 simulation 지표와 다른 평가 범위다. 기존 학습의 시험셋 활용 문제 때문에 독립 성능 보장 수치로 사용하지 않는다.',
               '중간 v2.5의 비용 절감 13.5억, 원인 분석 시간 95% 단축과 검증되지 않은 물리 원인 단정은 현재 성과에서 제외한다. 최초 Word 기획의 보수적인 해석 원칙을 유지한다.']},
    {'title': '08 보완 과제와 실행 순서',
     'paragraphs': ['현재 결과는 로컬에서 검증한 서비스다. 원안의 분석 지원 목적과 실제 관제 화면을 연결했으며, 운영 전에는 아래 항목을 순서대로 확인한다.'],
     'tables': [table('후속 작업과 완료 기준', ['순서', '보완 항목', '완료 기준'], [
         ['1', '독립 평가 절차', '전처리를 fold 안에서 fit하고 시험셋을 모델 선정에서 분리. 이후 모델 버전별 재평가.'],
         ['2', '운영 계정과 권한', 'Firebase 토큰을 서버에서 검증하고 계정별 데이터 소유와 엔지니어·관리자 권한을 연결. 현재 역할 버튼은 시연용.'],
         ['3', '원안의 분석 지원', 'R01~R06의 판정값·이유·실행 이력 연결과 센서 분포 탐색 기능을 우선순위에 따라 확장.'],
         ['4', '영속 저장 검증', 'GCS의 원본·예측·대화·점검 저장과 동시 갱신을 실제 비공개 버킷에서 검증. 현재 로컬 SQLite만 실증.'],
         ['5', '로컬 컨테이너', 'Docker 기동, 모델 로드, CSV 추론, Tool 질의와 데이터 보존을 먼저 검증.'],
         ['6', 'Cloud Run', '저장 버킷·서비스 계정 IAM·모델 비밀 설정 후 배포. 현재 변경본은 배포하지 않음.']
     ], [1.3, 4.1, 11.2]),
         table('구현 근거와 문서 위치', ['구분', '대상'], [
             ['최초 기획', 'docs/반도체_분석시각화_지원서비스_중간프로젝트_기획서.docx 내부 버전 1.4'],
             ['중간 확장 근거', 'archive/pre-agent-v2.5 보관 문서와 pre-agent-code-v3 소스'],
             ['공통 파이프라인', 'src/data_analysis의 validation, inference, repository, service, tools, agent'],
             ['관제 서브페이지', 'src/data_analysis/dashboard.py, inspections.py, server/dashboard_api.py, web/dashboard/'],
             ['검증과 시연', 'tests/test_analysis.py, tests/test_dashboard.py, docs/dashboard_reference_review.md, docs/demo/']
         ], [3.8, 12.8])],
     'after': ['로컬 접속은 http://127.0.0.1:61140/ 의 CSV 분석실과 /dashboard/ 의 공정 관제 서브페이지다. QR도 현재 서버 주소를 사용하며, 127.0.0.1은 같은 PC에서만 접근할 수 있다.']}
]


FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
def font(size): return ImageFont.truetype(FONT, size)
def diagram(name, service=False):
    im = Image.new('RGB', (1500, 1040), '#ffffff'); d = ImageDraw.Draw(im)
    def txt(x,y,s,size=30,color='#243953'): d.text((x,y),s,font=font(size),fill=color)
    def box(x,y,title,lines,color='#eef4fc',w=430):
        d.rounded_rectangle((x,y,x+w,y+150),radius=14,fill=color,outline='#bccbde',width=2)
        txt(x+22,y+18,title,34)
        for i,line in enumerate(lines): txt(x+22,y+72+33*i,line,27)
    def arrow(points,color='#5c7696'):
        d.line(points,fill=color,width=5,joint='curve'); x,y=points[-1]; a,b=points[-2]
        if abs(x-a)>abs(y-b): s=1 if x>a else -1; t=[(x,y),(x-16*s,y-9),(x-16*s,y+9)]
        else: s=1 if y>b else -1; t=[(x,y),(x-9,y-16*s),(x+9,y-16*s)]
        d.polygon(t,fill=color)
    if not service:
        txt(20,15,'학습과 시험 평가',38,'#23664a')
        for x,title,lines in [(20,'SECOM 원본',['1567행 · 590센서','라벨과 시간 정렬']), (535,'별도 학습과 평가',['학습에서 전처리와 모델 fit','시험 314행 지표 보관']), (1050,'고정된 산출물',['저장 전처리와 LightGBM','학습 정상군 1170행'])]: box(x,80,title,lines,'#edf6f0')
        arrow([(450,155),(535,155)]);arrow([(965,155),(1050,155)])
        txt(20,315,'업로드와 simulation의 공통 추론',38,'#285c9d')
        box(20,380,'CSV 등록과 검증',['필수 센서와 ID 검사','라벨과 시간은 선택'])
        box(535,380,'저장 모델 추론',['transform과 predict만','업로드로 fit하지 않음'])
        box(1050,380,'데이터셋 보관',['원본과 예측을 row_id 결합','파일 해시와 모델 버전'])
        arrow([(450,455),(535,455)]);arrow([(965,455),(1050,455)])
        arrow([(1265,230),(1265,285),(750,285),(750,380)],'#378063')
        txt(800,294,'동일 모델 적용',26,'#23664a')
        arrow([(1265,530),(1265,610),(750,610),(750,680)])
        box(535,680,'범위 지정과 Python 분석',['데이터셋과 기간으로 필터','순위 재계산과 기본 EDA'])
        arrow([(535,755),(450,755)])
        box(20,680,'화면과 에이전트',['통계와 실제 SHAP','결과 다운로드와 후속 질문'])
        txt(20,900,'SQLite에 데이터셋 보관 · 소유 세션별 격리',32)
        txt(20,952,'라벨이 없으면 실제 성능 미확인 · 시간이 없으면 시계열만 제한',29)
    else:
        for x,title,lines in [(20,'CSV 선택과 업로드',['공통 검증과 모델 추론','원본과 예측 저장']), (535,'기본 분석과 관제',['표와 차트 · 위험 순위','기간과 검토 비율 선택']), (1050,'분석 질문',['선택 데이터셋과 기간','대화 문맥을 함께 전달'])]:box(x,30,title,lines)
        arrow([(450,105),(535,105)]);arrow([(965,105),(1050,105)])
        d.rounded_rectangle((10,270,1490,650),radius=18,fill='#f1edfb',outline='#7653ac',width=5)
        txt(35,285,'데이터 분석 에이전트',38,'#614091')
        for x,title,lines in [(1050,'Gemini 분석 계획',['Tool과 인자 선택','추가 계산 필요성 판단']), (535,'Python Tool 실행',['허용 함수 9개만 실행','원본과 예측을 직접 계산']), (20,'계산 결과 검토',['수치와 조건을 확인','근거를 포함해 답변 생성'])]:box(x,420,title,lines,'#ffffff')
        arrow([(1265,180),(1265,420)],'#7653ac');arrow([(1050,495),(965,495)],'#7653ac');arrow([(535,495),(450,495)],'#7653ac')
        arrow([(235,420),(235,365),(1265,365),(1265,420)],'#7653ac');txt(460,322,'필요 시 추가 Tool 호출 · 최대 6회 루프와 12회 호출',28,'#614091')
        arrow([(235,570),(235,740)])
        box(20,740,'답변과 근거 표시',['표본 수와 분석 방법 명시','보고서와 CSV 다운로드'])
        box(760,740,'사람의 점검 업무',['지시 등록 → 확인과 보고','관리자 승인 또는 보완'])
        txt(20,955,'점검은 사용자가 직접 등록 · 통계와 SHAP으로 고장 원인을 단정하지 않음',29)
    im.save(ASSETS / name)


diagram('data_workflow_v1_1.png')
diagram('service_workflow_v1_1.png', True)

doc = Document(); sec = doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(1.65);sec.bottom_margin=Cm(1.65);sec.left_margin=Cm(2.2);sec.right_margin=Cm(2.2)
for name,size in [('Normal',10),('Title',21),('Subtitle',12),('Heading 1',17),('Heading 2',11)]:
    s=doc.styles[name];s.font.name='Apple SD Gothic Neo';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
    s.element.rPr.rFonts.set(qn('w:eastAsia'),'Apple SD Gothic Neo')
    for attr in ['asciiTheme','eastAsiaTheme','hAnsiTheme','cstheme']:
        s.element.rPr.rFonts.attrib.pop(qn('w:'+attr),None)
    for border in s.element.findall('.//'+qn('w:pBdr')):
        border.getparent().remove(border)
    s.paragraph_format.space_after=Pt(7);s.paragraph_format.line_spacing=1.16
doc.styles['Normal'].paragraph_format.widow_control=True
doc.core_properties.title=data['title'];doc.core_properties.author=data['author'];doc.core_properties.subject=data['subtitle']

def paragraph(text,style=None):
    p=doc.add_paragraph(text,style);return p


def add_table(t):
    paragraph(t['title'],'Heading 2')
    tb=doc.add_table(rows=1,cols=len(t['headers']));tb.autofit=False
    for i,w in enumerate(t['widths']):tb.columns[i].width=Cm(w)
    for i,h in enumerate(t['headers']):tb.rows[0].cells[i].text=h
    for row in t['rows']:
        cells=tb.add_row().cells
        for i,value in enumerate(row):cells[i].text=value
    for ri,row in enumerate(tb.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if ri==0:pr.append(OxmlElement('w:tblHeader'))
        for i,c in enumerate(row.cells):
            c.width=Cm(t['widths'][i]);cp=c._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
            cp.append(borders);m=OxmlElement('w:tcMar')
            for edge,v in [('top','70'),('bottom','70'),('left','100'),('right','100')]:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),v);e.set(qn('w:type'),'dxa');m.append(e)
            cp.append(m)
            if ri==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EAF0F7');cp.append(shade)
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.1
                for r in p.runs:r.font.size=Pt(9.3);r.bold=ri==0
    p=paragraph('');p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=0.4;p.runs


for index,page in enumerate(pages):
    if index:doc.add_page_break()
    else:
        paragraph('반도체 공정 데이터분석\n시각화 서비스 기획안 v1.1','Title')
        paragraph(data['subtitle'],'Subtitle')
        paragraph(f"{data['date']}   작성 {data['author']}")
    paragraph(page['title'],'Heading 1')
    for p in page.get('paragraphs',[]):paragraph(p)
    if page.get('image'):
        p=doc.add_paragraph();r=p.add_run();shape=r.add_picture(str(ASSETS/page['image']),width=Cm(16.6));shape._inline.docPr.set('descr',page['title'])
    for t in page.get('tables',[]):add_table(t)
    for p in page.get('after',[]):paragraph(p)
doc.save(ROOT/(STEM+'.docx'))

escape=html.escape
chunks=[]
for page in pages:
    parts=[f'<section><h2>{escape(page["title"])}</h2>']
    parts += [f'<p>{escape(p)}</p>' for p in page.get('paragraphs',[])]
    if page.get('image'):
        encoded=base64.b64encode((ASSETS/page['image']).read_bytes()).decode()
        parts.append(f'<img alt="{escape(page["title"])}" src="data:image/png;base64,{encoded}">')
    for t in page.get('tables',[]):
        parts.append(f'<h3>{escape(t["title"])}</h3><div class="scroll"><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in t['headers'])+'</tr></thead><tbody>')
        for row in t['rows']:
            parts.append('<tr>'+''.join('<td>'+escape(v).replace('\n','<br>')+'</td>' for v in row)+'</tr>')
        parts.append('</tbody></table></div>')
    parts += [f'<p>{escape(p)}</p>' for p in page.get('after',[])]
    parts.append('</section>');chunks.append('\n'.join(parts))
output='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(data['title'])+'</title><style>body{font:16px/1.8 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;background:#f6f8fb;color:#202d3f;margin:0}main{max-width:1100px;margin:auto;padding:45px 28px}h1{font-size:32px;line-height:1.45}h2{font-size:25px}h3{font-size:18px}section{padding:25px 32px;margin:30px 0;background:white;border:1px solid #e0e5ed;border-radius:12px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;vertical-align:top;border:1px solid #d9d9d9;text-align:left}th{background:#eaf0f7}td:first-child{min-width:100px}img{width:100%;height:auto}.scroll{overflow:auto}p{margin:12px 0}header p{color:#516176}@media print{body{background:#fff}main{padding:0}section{break-before:page;border:0;padding:0}section:first-of-type{break-before:auto}}</style><main><header><h1>'+escape(data['title'])+'</h1><p>'+escape(data['subtitle'])+'<br>'+escape(data['date'])+' · 작성 '+escape(data['author'])+'</p></header>'+'\n'.join(chunks)+'</main></html>'
(ROOT/(STEM+'.html')).write_text(output)
(APP/'docs'/ (STEM+'.html')).write_text(output)
(APP/'docs/revision_v1_1_content.json').write_text(json.dumps({**data,'pages':pages},ensure_ascii=False,indent=2))
print(json.dumps({'docx':str(ROOT/(STEM+'.docx')),'html':str(ROOT/(STEM+'.html')),'sections':len(pages)},ensure_ascii=False))
