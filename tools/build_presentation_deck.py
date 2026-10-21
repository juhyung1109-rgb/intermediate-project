# -*- coding: utf-8 -*-
"""
Full Master 18-Slide Presentation Generator for SEMI-GUARD.
Aligned with the Project Planning Document (기획서 체계):
  - PART 1: 서비스 기획 및 추진 목적 (Purpose & Objectives)
  - PART 2: 모델링 및 단계별 비교 과정 (Modeling Process & Comparative Experiments)
  - PART 3: 관제 시스템 구축 과정 (Control System Architecture & Engineering)
  - PART 4: 검증 결과 및 향후 로드맵 (Verification & Roadmap)

Completely removes all "Day 1, Day 2, Day 3" references.
Deepens model comparison (6 models, failure analysis, feature engineering)
and control system engineering (dual UI/UX, PdM drift engine, XAI two-track, LLM wiki).
Embedded with 10-minute speech scripts in speaker notes.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color definitions - Modern High-Tech Semiconductor Theme
    DARK_BG = RGBColor(11, 19, 43)        # #0B132B Deep Space Navy
    LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC Slate 50
    CARD_BG = RGBColor(255, 255, 255)     # White
    CARD_BORDER = RGBColor(203, 213, 225) # #CBD5E1 Slate 300
    PRIMARY = RGBColor(30, 58, 138)       # #1E3A8A Dark Navy Blue
    PRIMARY_LIGHT = RGBColor(37, 99, 235) # #2563EB Blue 600
    PRIMARY_DARK = RGBColor(15, 23, 42)   # #0F172A Slate 900
    PRIMARY_SOFT = RGBColor(239, 246, 255)# #EFF6FF Blue 50
    SUCCESS = RGBColor(5, 150, 105)       # #059669 Emerald 600
    SUCCESS_SOFT = RGBColor(236, 253, 245)# Emerald 50
    DANGER = RGBColor(220, 38, 38)        # #DC2626 Red 600
    DANGER_SOFT = RGBColor(254, 242, 242) # Red 50
    WARNING = RGBColor(217, 119, 6)       # #D97706 Amber 600
    WARNING_SOFT = RGBColor(254, 243, 199)# Amber 50
    PURPLE = RGBColor(126, 34, 206)       # #7E22CE Purple 700
    PURPLE_SOFT = RGBColor(243, 232, 255) # Purple 50
    TEXT_MAIN = RGBColor(30, 41, 59)      # #1E293B Slate 800
    TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B Slate 500
    TEXT_LIGHT = RGBColor(241, 245, 249)  # #F1F5F9 Slate 100
    ACCENT_CYAN = RGBColor(14, 116, 144)  # #0E7490 Cyan 700

    def set_bg(slide, color):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, category, title, subtitle=None):
        tx = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.85))
        tf = tx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.text = category.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_LIGHT
        p.font.name = "Pretendard"

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(21)
        p2.font.bold = True
        p2.font.color.rgb = PRIMARY_DARK
        p2.font.name = "Pretendard"

        if subtitle:
            p3 = tf.add_paragraph()
            p3.text = subtitle
            p3.font.size = Pt(11)
            p3.font.color.rgb = TEXT_MUTED
            p3.font.name = "Pretendard"

    def add_footer(slide, current_idx, total=18):
        tx = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.35))
        tf = tx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = f"SEMI-GUARD: 반도체 공정 이상 탐지 & 설비 예지보전 AI 관제 시스템   |   Slide {current_idx:02d} / {total:02d}   |   10분 정규 발표"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = "Pretendard"

    def add_card(slide, l, t, w, h, bg=CARD_BG, border=CARD_BORDER):
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
        shp.fill.solid()
        shp.fill.fore_color.rgb = bg
        if border:
            shp.line.color.rgb = border
            shp.line.width = Pt(1.2)
        else:
            shp.line.fill.background()
        return shp

    def add_metric_box(slide, l, t, w, h, label, val, sub="", color=PRIMARY_LIGHT, bg=PRIMARY_SOFT):
        add_card(slide, l, t, w, h, bg=bg, border=color)
        tx = slide.shapes.add_textbox(l + Inches(0.12), t + Inches(0.1), w - Inches(0.24), h - Inches(0.2))
        tf = tx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p0 = tf.paragraphs[0]
        p0.text = label
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = color
        p0.font.name = "Pretendard"
        
        p1 = tf.add_paragraph()
        p1.text = val
        p1.font.size = Pt(19)
        p1.font.bold = True
        p1.font.color.rgb = color
        p1.font.name = "Pretendard"
        
        if sub:
            p2 = tf.add_paragraph()
            p2.text = sub
            p2.font.size = Pt(9)
            p2.font.color.rgb = TEXT_MUTED
            p2.font.name = "Pretendard"

    def set_notes(slide, txt):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = txt

    pic_dir = "web/picture"
    def find_pic(keyword):
        if not os.path.exists(pic_dir):
            return None
        for f in os.listdir(pic_dir):
            if keyword in f and f.endswith(".png"):
                return os.path.join(pic_dir, f)
        return None

    # =========================================================================
    # SLIDE 1: Title Slide (Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1, DARK_BG)

    badge1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(3.4), Inches(0.45))
    badge1.fill.solid()
    badge1.fill.fore_color.rgb = RGBColor(30, 58, 138)
    badge1.line.color.rgb = RGBColor(59, 130, 246)
    tf_b1 = badge1.text_frame
    p_b1 = tf_b1.paragraphs[0]
    p_b1.text = "SEMICONDUCTOR AI CONTROL PLATFORM"
    p_b1.font.size = Pt(10)
    p_b1.font.bold = True
    p_b1.font.color.rgb = RGBColor(147, 197, 253)
    p_b1.alignment = PP_ALIGN.CENTER

    t1_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(2.3))
    tf1 = t1_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "SEMI-GUARD"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.font.name = "Pretendard"

    p2 = tf1.add_paragraph()
    p2.text = "반도체 제조 공정 이상 탐지 및 설비 예지보전 AI 관제 시스템"
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = RGBColor(56, 189, 248)
    p2.font.name = "Pretendard"

    p3 = tf1.add_paragraph()
    p3.text = "기획서 기반 서비스 목적 · 모델링 비교 실험 · 관제 시스템 엔지니어링 · 10분 정규 발표"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(148, 163, 184)
    p3.font.name = "Pretendard"

    cards_meta = [
        ("01. 기획 목적", "6.64% 극단적 불균형 극복\nFN 손실 20배 방어 시스템", RGBColor(59, 130, 246)),
        ("02. 모델링 비교", "Enhanced LightGBM 챔피언\nRecall@20% 71.4%, PR-AUC 0.2831", RGBColor(16, 185, 129)),
        ("03. 관제 시스템", "8월 15.8% 스파이크 PdM 추적\n엔지니어/관리자 듀얼 관제 UI", RGBColor(245, 158, 11)),
        ("04. 지식 자산화", "Karpathy 3계층 공정 위키\n트러블슈팅 복리 축적 네트워크", RGBColor(168, 85, 247)),
    ]
    for i, (head, desc, col) in enumerate(cards_meta):
        cx = Inches(1.0 + i * 2.88)
        cy = Inches(4.5)
        cw = Inches(2.7)
        ch = Inches(1.9)
        c_shp = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, cw, ch)
        c_shp.fill.solid()
        c_shp.fill.fore_color.rgb = RGBColor(15, 23, 42)
        c_shp.line.color.rgb = col
        c_shp.line.width = Pt(1.5)

        tx = s1.shapes.add_textbox(cx + Inches(0.15), cy + Inches(0.15), cw - Inches(0.3), ch - Inches(0.3))
        tf = tx.text_frame
        tf.word_wrap = True
        p_h = tf.paragraphs[0]
        p_h.text = head
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = col
        p_h.font.name = "Pretendard"

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10.5)
        p_d.font.color.rgb = RGBColor(226, 232, 240)
        p_d.font.name = "Pretendard"

    set_notes(s1, """[슬라이드 01 | 표지 - 00:20 배정]
안녕하십니까. 반도체 제조 공정 센서 데이터를 기반으로 불량을 조기 탐지하고, 설비 고장을 사전에 예방하며, 현장 엔지니어와 공정 관리자를 위한 실시간 관제 시스템을 구현한 SEMI-GUARD의 발표를 시작하겠습니다.
본 프로젝트는 기획서의 요구사항에 맞춰, '만든 목적', '모델링 비교 과정', '관제 시스템 구축 과정', 그리고 '검증 및 향후 계획'의 4대 체계로 구성되어 있습니다. 10분 동안 체계적으로 말씀드리겠습니다.""")

    # =========================================================================
    # SLIDE 2: Agenda (Planning Doc Structure)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "Agenda", "기획서 기반 4대 보고 체계", "프로젝트 추진 목적부터 모델 비교, 관제 시스템 구축 및 검증까지의 논리적 흐름")
    add_footer(s2, 2)

    agenda_items = [
        ("PART 1", "서비스 기획 및 추진 목적", [
            "반도체 팹의 페인포인트 (6.64% 극단적 불균형, 20배 높은 FN 손실)",
            "590개 고차원 노이즈 센서 환경의 한계",
            "SEMI-GUARD 4대 핵심 개발 목표 및 전체 아키텍처"
        ], PRIMARY_LIGHT, PRIMARY_SOFT),
        ("PART 2", "모델링 및 단계별 비교 과정", [
            "데이터 정합성 검증 (오프바이원 버그 수정, Median Imputation, 232개 피처 정제)",
            "스케일러 및 L1 규제 실험 비교 (368개 노이즈 피처 0화)",
            "경제적 비용 행렬 및 결정론적 위험 순위화 (Top 20% 컷오프)",
            "6종 모델 벤치마크 비교 & Enhanced LightGBM 챔피언 선정 (Recall@20% 71.4%)",
            "LambdaMART 랭커의 실패 원인 분석 및 파생변수 승리 요인"
        ], SUCCESS, SUCCESS_SOFT),
        ("PART 3", "관제 시스템 구축 과정", [
            "관제 시스템 설계 철학 및 사용자 페르소나 (엔지니어 2x2 vs 관리자 5대 센터)",
            "시계열 분석 및 8월 34주차 불량 폭증(15.8%) 규명",
            "설비 예지보전(PdM) Tri-Criteria 센서 표류 감지 엔진",
            "설명 가능한 AI (XAI) 투트랙 엔진 (#1254 진양성 vs #242 위양성 안전마진)",
            "18개월 유니버설 타임라인 대시보드 & Karpathy 3계층 LLM 공정 위키"
        ], WARNING, WARNING_SOFT),
        ("PART 4", "검증 결과 및 향후 로드맵", [
            "기획서 C01~C08 8대 핵심 요구사항 100% PASS 검증 매트릭스",
            "정량적/정성적 기대 효과 (수율 손실 비용 절감)",
            "차기 고도화 로드맵 (Kafka 실시간 스트리밍, LLM 자율 인터록)"
        ], PURPLE, PURPLE_SOFT),
    ]

    for i, (part, title, bullets, col, bg_col) in enumerate(agenda_items):
        ax = Inches(0.8 + i * 2.98)
        ay = Inches(1.5)
        aw = Inches(2.8)
        ah = Inches(5.2)

        add_card(s2, ax, ay, aw, ah, bg=bg_col, border=col)
        tx = s2.shapes.add_textbox(ax + Inches(0.18), ay + Inches(0.18), aw - Inches(0.36), ah - Inches(0.36))
        tf = tx.text_frame
        tf.word_wrap = True

        p_pt = tf.paragraphs[0]
        p_pt.text = part
        p_pt.font.size = Pt(11)
        p_pt.font.bold = True
        p_pt.font.color.rgb = col
        p_pt.font.name = "Pretendard"

        p_ti = tf.add_paragraph()
        p_ti.text = title
        p_ti.font.size = Pt(14)
        p_ti.font.bold = True
        p_ti.font.color.rgb = PRIMARY_DARK
        p_ti.font.name = "Pretendard"

        p_sp = tf.add_paragraph()
        p_sp.text = ""
        p_sp.font.size = Pt(6)

        for b in bullets:
            p_b = tf.add_paragraph()
            p_b.text = f"•  {b}"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = TEXT_MAIN
            p_b.font.name = "Pretendard"
            p_b.space_after = Pt(6)

    set_notes(s2, """[슬라이드 02 | 목차 - 00:35 누적]
오늘 발표는 기획서의 체계에 따라 총 4개 파트로 진행됩니다.
첫째, 서비스 기획 및 추진 목적에서 반도체 공정의 고질적 불균형과 막대한 미검출 손실 문제를 정의합니다.
둘째, 모델링 과정에서 데이터 정제부터 스케일러 비교, 6종 모델 벤치마크, 그리고 실패 분석을 통한 챔피언 선정 과정을 상세히 공유합니다.
셋째, 모델 결과를 현장에 안착시키기 위한 관제 시스템 구축 과정으로, 시계열 표류 감지, 투트랙 XAI, 듀얼 웹 대시보드 및 지식 위키를 설명합니다.
넷째, 기획 요구사항 검증 결과와 향후 로드맵으로 마무리하겠습니다.""")

    # =========================================================================
    # PART 1: SERVICE PURPOSE & OBJECTIVES (Slide 3 & 4)
    # =========================================================================
    # SLIDE 3: 추진 배경 및 문제 정의
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "PART 1. 서비스 기획 및 추진 목적", "추진 배경 및 반도체 팹의 3대 핵심 난제", "SECOM 데이터셋 1,567장 계측 데이터에 내재된 극단적 불균형과 고차원 노이즈 극복")
    add_footer(s3, 3)

    add_metric_box(s3, Inches(0.8), Inches(1.5), Inches(2.7), Inches(1.1), "총 웨이퍼 수 (SECOM)", "1,567 장", "정상 1,463장 / 불량 104장", PRIMARY_LIGHT, PRIMARY_SOFT)
    add_metric_box(s3, Inches(3.8), Inches(1.5), Inches(2.7), Inches(1.1), "원천 불량률 (극단적 불균형)", "6.64 %", "불량 포획 극도로 난해", DANGER, DANGER_SOFT)
    add_metric_box(s3, Inches(6.8), Inches(1.5), Inches(2.7), Inches(1.1), "센서 차원수 (고차원 노이즈)", "590 개", "결측/중복/왜도 다수 존재", WARNING, WARNING_SOFT)
    add_metric_box(s3, Inches(9.8), Inches(1.5), Inches(2.7), Inches(1.1), "경제적 비용 비대칭성", "FN 손실 20배", "결함 유출 시 후공정 수십억 손실", PURPLE, PURPLE_SOFT)

    # 3 Pain Points Cards
    pains = [
        ("난제 1. 극단적 클래스 불균형 (6.64%)", [
            "불량 웨이퍼 비율이 6.64%에 불과하여 단순 정확도(Accuracy)는 93.4%가 나오더라도 무의미함.",
            "일반 분류기는 정상으로만 예측하는 다수 범주 편향에 빠지며, 재현율이 급락함.",
            "해결 방향: 상위 20% 집중 검사 지표(Recall@20%)와 PR-AUC 평가 체계 도입."
        ], DANGER, DANGER_SOFT),
        ("난제 2. 치명적인 경제적 비대칭 비용 (FN 손실)", [
            "정상을 불량으로 오판하는 False Positive는 재검사 비용(비용 1)에 그침.",
            "불량을 정상으로 오판하여 고객사로 유출되는 False Negative는 칩 파기, 배상금 등 20배 이상의 손실(비용 20) 초래.",
            "해결 방향: 도메인 특화 비대칭 Cost Matrix 설계 및 의사결정 임계값 최적화."
        ], WARNING, WARNING_SOFT),
        ("난제 3. 590개 고차원 센서의 노이즈 및 결측", [
            "전체 센서의 40% 이상이 2.0 이상의 극심한 왜도(Skewness)와 결측치를 보유함.",
            "공정 엔지니어가 590개 센서를 일일이 모니터링하는 것은 물리적으로 불가능함.",
            "해결 방향: 결측/분산/다중공선성 체계적 정제 및 L1 라쏘 규제를 통한 노이즈 자동 소거."
        ], PRIMARY_LIGHT, PRIMARY_SOFT)
    ]

    for i, (p_title, p_desc, col, bg_col) in enumerate(pains):
        px = Inches(0.8 + i * 3.98)
        py = Inches(2.8)
        pw = Inches(3.78)
        ph = Inches(4.0)

        add_card(s3, px, py, pw, ph, bg=bg_col, border=col)
        tx = s3.shapes.add_textbox(px + Inches(0.18), py + Inches(0.18), pw - Inches(0.36), ph - Inches(0.36))
        tf = tx.text_frame
        tf.word_wrap = True

        p_h = tf.paragraphs[0]
        p_h.text = p_title
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = col
        p_h.font.name = "Pretendard"

        p_sp = tf.add_paragraph()
        p_sp.text = ""
        p_sp.font.size = Pt(8)

        for b in p_desc:
            pb = tf.add_paragraph()
            pb.text = f"•  {b}"
            pb.font.size = Pt(10)
            pb.font.color.rgb = TEXT_MAIN
            pb.font.name = "Pretendard"
            pb.space_after = Pt(8)

    set_notes(s3, """[슬라이드 03 | 추진 배경 및 문제 정의 - 01:20 누적]
반도체 제조 현장은 3가지 거대한 데이터 난제에 직면해 있습니다.
첫째, SECOM 데이터 기준 1,567장 중 불량은 104장에 불과한 6.64%의 극단적 불균형입니다. 이 때문에 일반적인 정확도 모델은 아무런 의미를 갖지 못합니다.
둘째, 결함 웨이퍼가 고객사로 유출되는 False Negative는 단순 재검사 비용인 False Positive보다 최소 20배 이상의 막대한 후공정 손실을 야기합니다.
셋째, 590개의 센서는 결측치와 극심한 왜도로 오염되어 있어 인간 엔지니어가 육안으로 판별할 수 없습니다.
따라서 저희는 이 3대 난제를 해결하기 위해 본 프로젝트를 착수했습니다.""")

    # SLIDE 4: 서비스 목표 및 시스템 아키텍처
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "PART 1. 서비스 기획 및 추진 목적", "SEMI-GUARD 시스템 개발 목표 및 전체 아키텍처", "단순 모델링을 넘어 실시간 현장 관제 및 의사결정 지원까지 완성하는 4대 파이프라인")
    add_footer(s4, 4)

    # 4 Architecture Pillars
    arch_pillars = [
        ("01. 위험 순위화 엔진\n(Risk Ranking)", [
            "상위 20% 검사 자원 한정",
            "불량 70% 이상 집중 포획",
            "결정론적 Tie-Breaking 정렬",
            "정상 1,170장 기준선 대조"
        ], PRIMARY_LIGHT, PRIMARY_SOFT),
        ("02. 시계열 예지보전 엔진\n(PdM Drift Engine)", [
            "8월 15.8% 불량 급증 규명",
            "Tri-Criteria 표류 감지 알고리즘",
            "CVD 상승 / 에처 하강 조기 경보",
            "고장 2~3주 전 선제 PM 발령"
        ], SUCCESS, SUCCESS_SOFT),
        ("03. 설명 가능한 AI 엔진\n(Two-Track XAI)", [
            "SHAP 기반 원인 기여도 분해",
            "진양성 #1254: RF 서지 진단",
            "위양성 #242: 안전 마진 규명",
            "글로벌 Top 10 인터록 연계"
        ], WARNING, WARNING_SOFT),
        ("04. 현장 관제 & 위키\n(Dual Dashboard & Wiki)", [
            "엔지니어 2x2 위험 스캔 모드",
            "관리자 5대 관제 센터",
            "18개월 유니버설 타임라인",
            "Karpathy 3계층 LLM 공정 위키"
        ], PURPLE, PURPLE_SOFT),
    ]

    for i, (col_ti, bullets, col, bg_col) in enumerate(arch_pillars):
        ax = Inches(0.8 + i * 2.98)
        ay = Inches(1.5)
        aw = Inches(2.8)
        ah = Inches(3.6)

        add_card(s4, ax, ay, aw, ah, bg=bg_col, border=col)
        tx = s4.shapes.add_textbox(ax + Inches(0.15), ay + Inches(0.15), aw - Inches(0.3), ah - Inches(0.3))
        tf = tx.text_frame
        tf.word_wrap = True

        p_h = tf.paragraphs[0]
        p_h.text = col_ti
        p_h.font.size = Pt(13)
        p_h.font.bold = True
        p_h.font.color.rgb = col
        p_h.font.name = "Pretendard"

        p_sp = tf.add_paragraph()
        p_sp.text = ""
        p_sp.font.size = Pt(8)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = f"✔  {b}"
            pb.font.size = Pt(10)
            pb.font.color.rgb = TEXT_MAIN
            pb.font.name = "Pretendard"
            pb.space_after = Pt(6)

    # Lower pipeline flowchart card
    add_card(s4, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.5), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx_flow = s4.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(11.3), Inches(1.3))
    tf_flow = tx_flow.text_frame
    tf_flow.word_wrap = True

    p_f0 = tf_flow.paragraphs[0]
    p_f0.text = "🔄 SEMI-GUARD 엔드투엔드 서비스 데이터 파이프라인 흐름"
    p_f0.font.size = Pt(11.5)
    p_f0.font.bold = True
    p_f0.font.color.rgb = PRIMARY_DARK

    p_f1 = tf_flow.add_paragraph()
    p_f1.text = "[원천 590 센서 데이터] ➔ [정합성 검증 & Median 정제 232개] ➔ [Enhanced LightGBM 위험 예측] ➔ [Top 20% 순위화 & Tri-Criteria 표류 감지] ➔ [투트랙 SHAP 설명] ➔ [현장 엔지니어 조치 & Karpathy LLM 공정 위키 영구 축적]"
    p_f1.font.size = Pt(10)
    p_f1.font.bold = True
    p_f1.font.color.rgb = PRIMARY_LIGHT
    p_f1.space_before = Pt(4)

    p_f2 = tf_flow.add_paragraph()
    p_f2.text = "기획서 핵심 원칙: '분석 대시보드 없는 단순 스크립트는 완성된 프로젝트가 아니다.' 모델링부터 UI 관제 및 지식 자산화까지 전 과정을 완결함."
    p_f2.font.size = Pt(9.5)
    p_f2.font.color.rgb = TEXT_MUTED
    p_f2.space_before = Pt(4)

    set_notes(s4, """[슬라이드 04 | 시스템 목표 및 아키텍처 - 01:50 누적]
이를 해결하기 위한 SEMI-GUARD의 개발 목표는 명확합니다. 단순한 분류 모델 하나를 만드는 데 그치지 않고, 4대 핵심 축이 유기적으로 맞물리는 관제 플랫폼을 구축하는 것입니다.
첫째, 상위 20%의 검사 자원으로 불량의 70% 이상을 잡아내는 '위험 순위화 엔진'.
둘째, 설비 고장을 2~3주 전에 선제 경고하는 '시계열 PdM 표류 엔진'.
셋째, 판정 이유를 완벽히 투명하게 설명하는 '투트랙 XAI 엔진'.
넷째, 엔지니어와 관리자가 즉시 활용하고 지식을 복리로 축적하는 '듀얼 웹 관제 대시보드와 Karpathy LLM 위키'입니다.
이제 모델링 과정부터 차례로 설명드리겠습니다.""")

    # =========================================================================
    # PART 2: MODELING PROCESS & COMPARATIVE EXPERIMENTS (Slide 5 ~ 9)
    # =========================================================================
    # SLIDE 5: 데이터 정합성 검증 및 전처리 파이프라인
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "PART 2. 모델링 및 단계별 비교 과정", "1단계: 데이터 정합성 검증 및 전처리 파이프라인", "원천 데이터 버그 수정부터 극심한 왜도 극복을 위한 Median Imputation 및 피처 정제")
    add_footer(s5, 5)

    img_skew = find_pic("왜도_이상치")
    if img_skew:
        s5.shapes.add_picture(img_skew, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    else:
        add_card(s5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG)

    # Left content box
    add_card(s5, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx5 = s5.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf5 = tx5.text_frame
    tf5.word_wrap = True

    p = tf5.paragraphs[0]
    p.text = "🛠️ 전처리 파이프라인 4대 핵심 설계 결정"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    steps = [
        ("1. Off-by-one 인덱싱 버그 검증 및 수정", "기존 변환 스크립트에서 591번째 컬럼 누락 버그를 발견하여 590개 전체 센서의 정합성을 100% 확보함."),
        ("2. 층화 분할 (Stratified 8:2 Split)", "Train 1,253장 (불량 83장) / Test 314장 (불량 21장)으로 불량률(6.64%)을 엄밀히 보존하며 평가셋 격리."),
        ("3. 왜도 40% 이상에 따른 Median Imputation", "센서의 40% 이상이 왜도(Skewness) 2.0 이상의 극심한 비대칭 분포를 보임. 평균(Mean)은 이상치에 왜곡되므로 중앙값(Median) 대체 채택."),
        ("4. 3단계 피처 정제 (590개 ➔ 232개)", "• 결측률 50% 초과 센서 제거: 28개 제거\n• 분산 제로(단일값) 센서 제거: 116개 제거\n• 다중공선성(r > 0.95) 중복 센서 제거: 214개 제거\n최종 232개 고품질 유효 센서 정제 완료.")
    ]

    for title, desc in steps:
        pt = tf5.add_paragraph()
        pt.text = title
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_LIGHT
        pt.space_before = Pt(8)

        pd = tf5.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s5, """[슬라이드 05 | 데이터 정합성 검증 및 전처리 - 02:35 누적]
모델링의 첫 단계는 데이터의 물리적 정합성을 바로잡는 것이었습니다.
첫째, 기존 변환 스크립트의 591번째 컬럼 오프바이원 버그를 찾아내 수정했습니다.
둘째, 우측 차트에서 보시듯 센서의 40% 이상이 2.0 이상의 심각한 왜도를 가집니다. 평균(Mean)을 사용하면 이상치 하나에 중심값이 크게 왜곡되므로, 이상치에 강건한 중앙값(Median) 대체를 채택했습니다.
셋째, 결측률 50% 초과 28개, 분산이 0인 116개, 상관계수 0.95 초과의 다중공선성 센서 214개를 순차적으로 제거하여 590개의 노이즈 센서를 232개의 고품질 센서로 정제했습니다.""")

    # SLIDE 6: 스케일러 실험 및 L1 페널티 규제
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "PART 2. 모델링 및 단계별 비교 과정", "2단계: 4대 스케일러 비교 실험 및 L1 규제 효과", "이상치 저항성이 우수한 RobustScaler 채택 및 L1 LASSO를 통한 368개 노이즈 피처 자동 0화")
    add_footer(s6, 6)

    # 4 Scaler Table Card
    add_card(s6, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx6_t = s6.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(6.4), Inches(4.9))
    tf6_t = tx6_t.text_frame
    tf6_t.word_wrap = True

    p = tf6_t.paragraphs[0]
    p.text = "📊 4대 스케일러 성능 비교 실험 (Logistic Regression 기준)"
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    table_data = [
        ("스케일러", "이상치 처리", "F1-Score", "재현율(Recall)", "평가 및 채택"),
        ("StandardScaler", "이상치에 매우 취약 (평균 왜곡)", "0.2051", "19.0 %", "이상치로 인한 스케일 왜곡 발생"),
        ("MinMaxScaler", "극단값에 의해 전체 범위 압축", "0.1875", "14.3 %", "노이즈 센서에 극히 민감"),
        ("RobustScaler (채택)", "IQR(25~75%) 기반 완벽 방어", "0.2222", "23.8 %", "최고 재현율 달성 (챔피언 스케일러)"),
        ("QuantileTransformer", "정규분포 강제 변환", "0.2105", "19.0 %", "물리적 신호 특성 훼손")
    ]

    for row_idx, row in enumerate(table_data):
        pr = tf6_t.add_paragraph()
        if row_idx == 0:
            pr.text = f"{row[0]:<18} | {row[1]:<20} | {row[2]:<8} | {row[3]:<10}"
            pr.font.size = Pt(9.5)
            pr.font.bold = True
            pr.font.color.rgb = PRIMARY_DARK
            pr.space_before = Pt(8)
        else:
            is_best = "RobustScaler" in row[0]
            pr.text = f"• {row[0]}: F1 {row[2]} / Recall {row[3]} ➔ {row[4]}"
            pr.font.size = Pt(9.5)
            pr.font.bold = is_best
            pr.font.color.rgb = SUCCESS if is_best else TEXT_MAIN
            pr.space_before = Pt(6)

    pr_summary = tf6_t.add_paragraph()
    pr_summary.text = "💡 결론: 반도체 챔버 센서의 특성상 순간적인 스파이크 이상치가 다수 발생하므로, 중앙값과 사분위수(IQR)를 사용하는 RobustScaler가 가장 높은 일반화 성능을 입증함."
    pr_summary.font.size = Pt(9.5)
    pr_summary.font.color.rgb = PRIMARY_LIGHT
    pr_summary.space_before = Pt(14)

    # Right Card: L1 Penalty Sparsity Effect
    add_card(s6, Inches(7.8), Inches(1.5), Inches(4.733), Inches(5.2), bg=CARD_BG, border=SUCCESS)
    tx6_r = s6.shapes.add_textbox(Inches(8.0), Inches(1.65), Inches(4.333), Inches(4.9))
    tf6_r = tx6_r.text_frame
    tf6_r.word_wrap = True

    p_r0 = tf6_r.paragraphs[0]
    p_r0.text = "🎯 L1 LASSO 규제의 노이즈 소거 효과"
    p_r0.font.size = Pt(12.5)
    p_r0.font.bold = True
    p_r0.font.color.rgb = PRIMARY_DARK

    l1_points = [
        ("L1 규제(Lasso)의 Sparsity 유도", "L2(Ridge)와 달리 불필요한 피처 가중치를 정확히 '0.0'으로 수렴시켜 자동 피처 선택(Feature Selection)을 수행함."),
        ("유효 가중치 수축 결과", "초기 446개 유효 가중치 중 무려 368개(82.5%)의 노이즈 가중치를 0으로 완전히 제거함."),
        ("실제 잔여 핵심 피처", "단 78개의 핵심 센서 가중치만 생존시켜, 극단적 불균형에서의 과적합(Overfitting)을 원천 차단함."),
        ("현장 해석력 향상", "현장 엔지니어가 590개가 아닌, 78개 유효 센서의 가중치 부호만 집중 감시할 수 있도록 모델 단순화 달성.")
    ]

    for ti, de in l1_points:
        pt = tf6_r.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = SUCCESS
        pt.space_before = Pt(8)

        pd = tf6_r.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s6, """[슬라이드 06 | 스케일러 실험 및 L1 페널티 규제 - 03:05 누적]
두 번째 모델링 단계에서는 4대 스케일러를 비교 실험했습니다.
좌측 표를 보시면, 이상치에 취약한 StandardScaler나 MinMaxScaler 대비, 사분위수(IQR)를 기준으로 정규화하는 RobustScaler가 재현율 23.8%로 가장 안정적인 성능을 보였습니다.
또한 우측의 L1 LASSO 규제 실험 결과, 446개 유효 가중치 중 무려 368개의 노이즈 센서 가중치를 자동으로 0으로 소거했습니다. 단 78개의 핵심 센서만 남김으로써 과적합을 방지하고 현장 해석력을 극대화했습니다.""")

    # SLIDE 7: 도메인 비용 행렬 및 위험 순위화 설계
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "PART 2. 모델링 및 단계별 비교 과정", "3단계: 도메인 특화 비용 행렬 및 결정론적 위험 순위화", "FN:FP = 20:1 경제적 비용 행렬 수립 및 상위 20%(63장) 전수 검사 정렬 알고리즘")
    add_footer(s7, 7)

    img_imb = find_pic("V01_클래스")
    if img_imb:
        s7.shapes.add_picture(img_imb, Inches(7.2), Inches(1.5), Inches(5.3), Inches(5.2))
    else:
        add_card(s7, Inches(7.2), Inches(1.5), Inches(5.3), Inches(5.2), bg=CARD_BG)

    # Left content box
    add_card(s7, Inches(0.8), Inches(1.5), Inches(6.2), Inches(5.2), bg=CARD_BG, border=WARNING)
    tx7 = s7.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.8), Inches(4.9))
    tf7 = tx7.text_frame
    tf7.word_wrap = True

    p = tf7.paragraphs[0]
    p.text = "💰 경제적 비용 행렬(Cost Matrix) 및 순위화 설계"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    cost_steps = [
        ("1. 비대칭 손실 함수 (Asymmetric Cost Matrix)", "• False Positive (오경보 재검사): 비용 = 1\n• False Negative (결함 유출 후공정 손실): 비용 = 20\nFN 비용을 20배 부여하여 임계값을 0.5에서 0.19로 하향 최적화."),
        ("2. 상위 20% 물리적 검사 컷오프", "현장 검사 장비의 물리적 일일 처리 용량을 감안하여, 테스트셋 314장 중 정확히 상위 20%인 math.ceil(314 * 0.2) = 63장을 추출하여 전수 검사 대상으로 지정."),
        ("3. 결정론적 Tie-Breaking 정렬", "위험 점수(Score) 내림차순 1순위, 동점 발생 시 Wafer ID 오름차순 2순위로 엄격 정렬. 실행 시마다 순위가 바뀌는 비결정론적 오류를 원천 차단."),
        ("4. 1,170장 정상 기준선 (Normal Baseline)", "정상 웨이퍼 1,170장의 5분위수~95분위수 분포를 구축하여, 의심 웨이퍼의 센서 이상 편차를 즉각 대조할 수 있는 기준선 마련.")
    ]

    for ti, de in cost_steps:
        pt = tf7.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = WARNING
        pt.space_before = Pt(8)

        pd = tf7.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s7, """[슬라이드 07 | 비용 행렬 및 위험 순위화 설계 - 03:40 누적]
세 번째 모델링 단계에서는 반도체 비즈니스 관점의 비용 행렬과 순위화 알고리즘을 설계했습니다.
우측 그래프에서 보듯 불량률은 6.64%에 불과합니다. 따라서 불량을 놓쳤을 때의 비용(FN)을 재검사 비용(FP) 대비 20배 높은 비용 행렬을 수립하고, 최적 분류 임계값을 0.19로 도출했습니다.
또한 현장 검사 라인의 하루 처리 한계를 반영하여, 테스트셋 314장 중 정확히 상위 20%인 63장을 집중 검사하도록 설계했습니다. 동점자 발생 시에는 Wafer ID 오름차순으로 Tie-Breaking을 적용하여 100% 동일한 검사 순위를 보장했습니다.""")

    # SLIDE 8: 모델 고도화 벤치마크 및 종합 비교
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "PART 2. 모델링 및 단계별 비교 과정", "4단계: 6종 모델 고도화 벤치마크 및 체계적 비교", "기준 모델 대비 트리 앙상블, 가중치 최적화, 도메인 파생변수 결합을 거치며 챔피언 모델 도출")
    add_footer(s8, 8)

    # Big Comparison Table Card
    add_card(s8, Inches(0.8), Inches(1.5), Inches(11.733), Inches(4.3), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx8_t = s8.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.333), Inches(4.0))
    tf8_t = tx8_t.text_frame
    tf8_t.word_wrap = True

    p = tf8_t.paragraphs[0]
    p.text = "🏆 6종 모델 체계적 벤치마크 비교 결과표 (Test Set N=314, 불량 21장 기준)"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    models_bench = [
        ("구분", "모델명 및 핵심 기법", "포획 불량수", "Recall@20%", "PR-AUC", "경제적 총비용", "평가 및 분석"),
        ("기준", "L1 Logistic Regression (기준 모델)", "12 / 21", "57.1 %", "0.1758", "198", "선형 경계의 한계, 중간 수준의 포획력"),
        ("앙상블", "Random Forest Classifier", "11 / 21", "52.4 %", "0.1642", "214", "불균형으로 인해 다수 클래스 편향 발생"),
        ("부스팅", "LightGBM (기본 설정)", "10 / 21", "47.6 %", "0.1580", "231", "클래스 가중치 미적용으로 불량 분기 실패"),
        ("가중치", "LightGBM (scale_pos_weight=5.0)", "13 / 21", "61.9 %", "0.2104", "176", "불량 가중치 학습으로 재현율 4.8%p 개선"),
        ("챔피언", "Enhanced LightGBM (+abnormal_count)", "15 / 21", "71.4 %", "0.2831", "137", "최고 성능! Recall 71.4% 돌파 & PR-AUC +61% 향상"),
        ("랭커", "LambdaMART (LightGBMRanker)", "9 / 21", "42.9 %", "0.1412", "249", "불량 희소성(6.6%)으로 Pairwise 그래디언트 실패")
    ]

    for idx, row in enumerate(models_bench):
        pr = tf8_t.add_paragraph()
        is_header = (idx == 0)
        is_champ = ("Enhanced" in row[1])
        is_ranker = ("LambdaMART" in row[1])

        if is_header:
            pr.text = f"{row[0]:<6} | {row[1]:<36} | {row[2]:<10} | {row[3]:<12} | {row[4]:<9} | {row[5]:<8} | {row[6]}"
            pr.font.size = Pt(9.5)
            pr.font.bold = True
            pr.font.color.rgb = PRIMARY_DARK
            pr.space_before = Pt(8)
        else:
            col_txt = SUCCESS if is_champ else (DANGER if is_ranker else TEXT_MAIN)
            pr.text = f"[{row[0]}] {row[1]:<35} : 불량 {row[2]} ({row[3]}) | PR-AUC {row[4]} | 비용 {row[5]} ➔ {row[6]}"
            pr.font.size = Pt(9.5)
            pr.font.bold = is_champ
            pr.font.color.rgb = col_txt
            pr.space_before = Pt(5)

    # 3 Summary Badge Cards below table
    add_metric_box(s8, Inches(0.8), Inches(5.9), Inches(3.7), Inches(1.0), "챔피언 불량 포획률 (Recall@20%)", "71.4 % (15/21개)", "기준 모델(57.1%) 대비 +14.3%p", SUCCESS, SUCCESS_SOFT)
    add_metric_box(s8, Inches(4.8), Inches(5.9), Inches(3.7), Inches(1.0), "챔피언 PR-AUC", "0.2831", "기준 모델(0.1758) 대비 +61.0% 향상", SUCCESS, SUCCESS_SOFT)
    add_metric_box(s8, Inches(8.8), Inches(5.9), Inches(3.733), Inches(1.0), "경제적 손실 비용 절감", "137 (최저 비용)", "기준 대비 61포인트 손실 방어", PRIMARY_LIGHT, PRIMARY_SOFT)

    set_notes(s8, """[슬라이드 08 | 모델 벤치마크 및 종합 비교 - 05:10 누적]
네 번째 모델링 단계로, 총 6종의 모델을 동일한 테스트셋(314장, 불량 21장)에서 엄밀하게 비교 벤치마크했습니다.
기준 모델인 L1 로지스틱은 상위 20%에서 12개(57.1%)의 불량을 잡았습니다.
기본 LightGBM은 10개에 그쳤으나, 클래스 가중치 5.0을 부여하자 13개(61.9%)로 향상되었습니다.
여기에 정상 기준선을 벗어난 센서 개수인 'abnormal_sensor_count' 파생변수를 결합한 'Enhanced LightGBM'이 21개 중 15개의 불량을 포획하며 Recall@20% 71.4%, PR-AUC 0.2831로 압도적인 챔피언에 등극했습니다.
반면 기대했던 LambdaMART 랭커는 42.9%로 크게 실패했는데, 그 원인을 다음 슬라이드에서 분석하겠습니다.""")

    # SLIDE 9: 챔피언 모델 승리 요인 및 실패 분석
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "PART 2. 모델링 및 단계별 비교 과정", "5단계: 챔피언 승리 요인 및 랭킹 모델 실패 원인 분석", "도메인 파생변수의 복합 이상 포획 원리와 극단적 불균형에서의 페어와이즈 그래디언트 한계 규명")
    add_footer(s9, 9)

    # Left Box: Why Champion Won
    add_card(s9, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=SUCCESS)
    tx9_l = s9.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf9_l = tx9_l.text_frame
    tf9_l.word_wrap = True

    p = tf9_l.paragraphs[0]
    p.text = "🌟 Enhanced LightGBM이 승리한 3대 이유"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = SUCCESS

    reasons = [
        ("1. 도메인 파생변수 `abnormal_sensor_count` 결합", "반도체 챔버 내에서 물리적 이상이 발생하면 단일 센서가 아니라 압력, 온도, RF 반사율 등 복수 센서가 동시다발적으로 튐. 정상 기준선(5~95%)을 이탈한 센서의 총합을 피처로 주입하여 트리 모델의 최상위 분기 기준 제공."),
        ("2. 비대칭 손실 보정을 위한 `scale_pos_weight=5.0`", "6.64%의 불균형 속에서 양품 샘플 대비 불량 샘플의 오분류 손실 그래디언트를 5배 증폭하여 불량 탐지 감도를 극대화함."),
        ("3. 리프 중심 트리 분할 (Leaf-wise Tree Split)", "LightGBM의 고유한 리프 중심 분할이 비선형 다차원 이상치 상호작용을 깊이 파고들어, 복합 센서 결함 패턴을 정밀하게 분리해냄.")
    ]

    for ti, de in reasons:
        pt = tf9_l.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_DARK
        pt.space_before = Pt(8)

        pd = tf9_l.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    # Right Box: Why LambdaMART Failed
    add_card(s9, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2), bg=CARD_BG, border=DANGER)
    tx9_r = s9.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(4.9))
    tf9_r = tx9_r.text_frame
    tf9_r.word_wrap = True

    p_r = tf9_r.paragraphs[0]
    p_r.text = "⚠️ LambdaMART 랭커가 실패한 원인 (반직관적 발견)"
    p_r.font.size = Pt(13)
    p_r.font.bold = True
    p_r.font.color.rgb = DANGER

    fails = [
        ("1. 불량 데이터의 극단적 희소성 (6.64%의 벽)", "순위화 전용 모델(LambdaMART)은 쌍(Pair) 간의 상대적 우열을 학습하는 Pairwise 손실 함수를 사용함. 불량-정상 쌍(Pair) 중 불량 데이터가 너무 적어 그래디언트가 극도로 희소해짐."),
        ("2. 검색 엔진(IR)과 반도체 공정 데이터의 차이", "정보 검색(IR)은 문서 간의 세밀한 랭킹이 중요하지만, 반도체 팹에서는 '상위 20% 내에 불량을 모아 넣는 것'이 핵심임. 개별 페어 순위 조정에 에너지를 낭비하며 정작 상위 컷오프 포획력이 42.9%로 추락함."),
        ("3. 핵심 교훈", "'이론상 랭킹에 가장 적합해 보이는 모델'이더라도 극단적 불균형 도메인에서는 절대적 이상 시그널을 학습하는 분류기+파생변수 조합이 훨씬 우수하다는 귀중한 실증 인사이트 도출.")
    ]

    for ti, de in fails:
        pt = tf9_r.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_DARK
        pt.space_before = Pt(8)

        pd = tf9_r.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s9, """[슬라이드 09 | 챔피언 승리 요인 및 실패 분석 - 05:45 누적]
이 비교 실험에서 매우 흥미로운 데이터 과학적 통찰을 얻었습니다.
좌측의 챔피언 모델은 도메인 지식에 기반한 'abnormal_sensor_count'가 결정적인 역할을 했습니다. 반도체 챔버 이상은 단일 센서가 아니라 압력, 온도 등 여러 센서가 동시에 튀는 연쇄 반응을 일으키는데, 이 파생변수가 트리의 최상위 분기 기준이 되어 15개의 불량을 잡아냈습니다.
반면 우측의 LambdaMART 랭커는 42.9%로 실패했습니다. 6.6%라는 극단적 불균형 환경에서는 페어와이즈(Pairwise) 그래디언트가 너무 희소해져 학습이 붕괴된 것입니다.
이처럼 실패 원인을 규명함으로써, 이론보다 실증 데이터에 기반한 최적 모델을 확정할 수 있었습니다.""")

    # =========================================================================
    # PART 3: CONTROL SYSTEM ARCHITECTURE & ENGINEERING (Slide 10 ~ 16)
    # =========================================================================
    # SLIDE 10: 관제 시스템 기획 및 사용자 정의
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, LIGHT_BG)
    add_header(s10, "PART 3. 관제 시스템 구축 과정", "1단계: 관제 시스템 기획 및 역할별 사용자 페르소나 정의", "기획서 04·05장 반영: 현장 엔지니어의 신속 스캔과 공정 관리자의 팹 전체 관제를 분리한 듀얼 인터페이스")
    add_footer(s10, 10)

    # 2 Big Persona Cards
    # Persona 1: Field Engineer
    add_card(s10, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx10_e = s10.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf10_e = tx10_e.text_frame
    tf10_e.word_wrap = True

    p = tf10_e.paragraphs[0]
    p.text = "👷 현장 엔지니어 페르소나 (Field Engineer)"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_LIGHT

    e_specs = [
        ("사용자 요구사항", "라인 현장에서 1초 안에 상위 20% 의심 웨이퍼를 확인하고, 즉시 정밀 계측 여부를 결정해야 함."),
        ("UI 설계: 2x2 위험 스캔 모드", "복잡한 수치표 대신 상위 63장 웨이퍼를 위험도 순 카드 그리드로 표출. 위험도 1위부터 순차적 스캔."),
        ("정상 기준선(Baseline) 즉각 대조", "선택된 웨이퍼의 센서값이 1,170장 정상 기준선(5~95%) 대비 몇 시그마 벗어났는지 바 차트로 직관적 표출."),
        ("원클릭 현장 판정 피드백 액션", "정밀 검사(Defect Action) 발령 또는 양품 승인(Normal Pass)을 클릭 한 번으로 시스템에 피드백 등록.")
    ]

    for ti, de in e_specs:
        pt = tf10_e.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_DARK
        pt.space_before = Pt(8)

        pd = tf10_e.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    # Persona 2: Process Administrator
    add_card(s10, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2), bg=CARD_BG, border=PURPLE)
    tx10_a = s10.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(4.9))
    tf10_a = tx10_a.text_frame
    tf10_a.word_wrap = True

    p_a = tf10_a.paragraphs[0]
    p_a.text = "🧑‍💼 공정 관리자 페르소나 (Process Administrator)"
    p_a.font.size = Pt(13)
    p_a.font.bold = True
    p_a.font.color.rgb = PURPLE

    a_specs = [
        ("사용자 요구사항", "팹 전체의 월별 수율 추이, 설비 노후화 표류 경보, 결함 원인 분석 및 과거 조치 이력을 총괄 관제해야 함."),
        ("UI 설계: 5대 종합 관제 센터", "① 수율 관제 센터  ② 설비 예지보전(PdM) 센터\n③ XAI 원인 분석 센터  ④ LLM 공정 위키 센터  ⑤ 알림/인터록 센터"),
        ("18개월 유니버설 타임라인 연동", "2008년 7월부터 2009년 12월까지 월별 슬라이더를 드래그하면 전체 5대 센터의 통계가 실시간 동기화."),
        ("교대 인수인계 보고서 자동화", "당일 탐지된 이상 건수, 미조치 웨이퍼 목록, 챔버 표류 경보를 마크다운 보고서로 원클릭 내보내기.")
    ]

    for ti, de in a_specs:
        pt = tf10_a.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_DARK
        pt.space_before = Pt(8)

        pd = tf10_a.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s10, """[슬라이드 10 | 관제 시스템 기획 및 사용자 정의 - 06:15 누적]
이제 세 번째 파트인 '관제 시스템 구축 과정'입니다.
기획서 04장과 05장의 철학처럼, 아무리 뛰어난 모델이라도 현장 엔지니어가 쓰지 못하면 무용지물입니다.
따라서 저희는 사용자를 두 개의 페르소나로 분리하여 듀얼 관제 인터페이스를 설계했습니다.
좌측의 '현장 엔지니어'는 복잡한 수치 대신 2x2 위험 스캔 카드로 63장의 의심 웨이퍼만 확인하고 즉각 조치합니다.
우측의 '공정 관리자'는 팹 전체의 5대 관제 센터와 18개월 유니버설 타임라인을 통해 수율, 설비 예지보전, XAI, 위키 지식을 총괄 관제합니다.""")

    # SLIDE 11: 시계열 분석 및 8월 불량 폭증 규명
    s11 = prs.slides.add_slide(blank_layout)
    set_bg(s11, LIGHT_BG)
    add_header(s11, "PART 3. 관제 시스템 구축 과정", "2단계: 시계열 데이터 분석 및 8월 34주차 불량 폭증 규명", "2008년 8월 불량률 15.8% 스파이크 원인 추적 및 9월 예방보전(PM) 후 2.9% 정상화 트렌드 실증")
    add_footer(s11, 11)

    img_ts = find_pic("R05_월별")
    if img_ts:
        s11.shapes.add_picture(img_ts, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    else:
        add_card(s11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG)

    # Left content box
    add_card(s11, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=DANGER)
    tx11 = s11.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf11 = tx11.text_frame
    tf11.word_wrap = True

    p = tf11.paragraphs[0]
    p.text = "📈 8월 34주차 불량 폭증 사건의 데이터 추적"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    ts_points = [
        ("1. 8월 34주차 불량률 15.8% 폭증 포착", "평상시 5~6% 수준이던 불량률이 2008년 8월 34주차에 15.8%까지 수직 급증함. 전체 104개 불량 중 31장이 이 단일 기간에 집중 발생."),
        ("2. 이상 원인: CVD 증착 챔버의 누적 열화", "센서 계측 데이터를 시간 축으로 전수 역추적한 결과, CVD 증착 챔버의 전극 마모와 가열 히터 편차로 인한 복합 열화(Compound Degradation)로 판명."),
        ("3. 9월 긴급 예방보전(PM) 실시 및 효과", "9월 첫째 주 챔버 클리닝 및 전극 교체(PM) 단행 후, 9월 불량률이 2.9%로 즉시 수직 안정화됨."),
        ("4. 관제 시스템 시사점", "'설비 고장이 터진 후에 수리하는 사후 보전(BM)'의 한계를 절감하고, 센서 신호의 완만한 표류(Drift)를 고장 2~3주 전에 미리 감지하는 예지보전(PdM) 엔진 개발 착수.")
    ]

    for ti, de in ts_points:
        pt = tf11.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = DANGER
        pt.space_before = Pt(8)

        pd = tf11.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s11, """[슬라이드 11 | 시계열 분석 및 8월 불량 급증 규명 - 06:45 누적]
우측 그래프를 보시면 시계열 관제에서 매우 중대한 패턴이 드러납니다.
2008년 8월 34주차에 불량률이 평소의 3배에 달하는 15.8%까지 폭증했습니다.
데이터를 역추적한 결과, 특정 CVD 챔버의 전극 마모와 히터 온도 편차가 누적되면서 발생한 설비 고장이었습니다. 9월 초 긴급 예방보전(PM)을 실시한 직후 불량률은 2.9%로 즉시 정상화되었습니다.
이 실증 데이터는 "사후 수리로는 늦는다. 설비 고장이 터지기 2~3주 전에 센서의 미세한 표류를 미리 감지해야 한다"는 예지보전(PdM) 엔진 개발의 결정적 계기가 되었습니다.""")

    # SLIDE 12: 설비 예지보전(PdM) 센서 표류 엔진 개발
    s12 = prs.slides.add_slide(blank_layout)
    set_bg(s12, LIGHT_BG)
    add_header(s12, "PART 3. 관제 시스템 구축 과정", "3단계: 설비 예지보전(PdM) Tri-Criteria 센서 표류 감지 엔진", "상관계수, Z-score 편차, 이상치 비율의 3대 통계 조건으로 CVD 상승 및 에처 하강 표류 조기 감지")
    add_footer(s12, 12)

    img_drift = find_pic("Day3_상승")
    if img_drift:
        s12.shapes.add_picture(img_drift, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    else:
        add_card(s12, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG)

    # Left content box
    add_card(s12, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=WARNING)
    tx12 = s12.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf12 = tx12.text_frame
    tf12.word_wrap = True

    p = tf12.paragraphs[0]
    p.text = "⚙️ Tri-Criteria 표류 감지 알고리즘"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    drift_criteria = [
        ("조건 1. 시간 상관계수 (|r| ≥ 0.25)", "시간 경과에 따른 센서값의 뚜렷한 단조 증가 또는 단조 감소 선형 트렌드 확인."),
        ("조건 2. Z-Score 편차 (|ΔZ| ≥ 1.0σ)", "기준 기간 대비 평균이 1.0 표준편차(σ) 이상 중심선에서 이탈하여 영구적 구조 변화를 보임."),
        ("조건 3. 이상치 비율 변화 (ΔOutlier ≥ 5%p)", "관리 한계선(3σ)을 벗어나는 불량 징후 빈도가 5%p 이상 급증."),
        ("실증 결과: 2대 표류 센서 포획 성공", "• CVD 증착 챔버 압력(feature_29, 30): 지속 우상향 상승 표류 (전극 마모)\n• 드라이 에처 RF 파워(feature_104, 105): 지속 우하향 하강 표류 (가스 노즐 막힘)\n➔ 설비 사고 2~3주 전 선제 PM 발령 가능.")
    ]

    for ti, de in drift_criteria:
        pt = tf12.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = WARNING
        pt.space_before = Pt(8)

        pd = tf12.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s12, """[슬라이드 12 | 설비 예지보전 센서 표류 엔진 개발 - 07:20 누적]
이를 자동화하기 위해 개발한 알고리즘이 바로 Tri-Criteria 센서 표류 감지 엔진입니다.
상관계수 0.25 이상, Z-score 편차 1.0 시그마 이상, 이상치 비율 5%p 이상 변화라는 3대 통계 조건을 동시에 만족해야만 '설비 노후화 표류'로 판정합니다.
우측 그래프를 보시면, CVD 챔버 압력 센서(feature_29)는 시간이 흐를수록 꾸준히 상승 표류했고, 드라이 에처 RF 센서(feature_104)는 하강 표류하고 있었습니다.
이 엔진을 통해 설비가 완전히 멈추기 2~3주 전에 선제적 예방보전(PM)을 발령할 수 있게 되었습니다.""")

    # SLIDE 13: 설명 가능한 AI (XAI) 투트랙 엔진 구축
    s13 = prs.slides.add_slide(blank_layout)
    set_bg(s13, LIGHT_BG)
    add_header(s13, "PART 3. 관제 시스템 구축 과정", "4단계: 설명 가능한 AI (XAI) 투트랙 의사결정 지원 엔진", "불량 판정의 투명한 원인 진단(진양성)과 정상임에도 알람이 울린 사유(위양성 안전마진)의 투트랙 해석")
    add_footer(s13, 13)

    img_xai = find_pic("Day3_고도화_SHAP_투트랙")
    if img_xai:
        s13.shapes.add_picture(img_xai, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    else:
        add_card(s13, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG)

    # Left content box
    add_card(s13, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx13 = s13.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf13 = tx13.text_frame
    tf13.word_wrap = True

    p = tf13.paragraphs[0]
    p.text = "🔬 투트랙 SHAP 원인 분석 의사결정 지원"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    xai_cases = [
        ("트랙 1. Wafer #1254 (진양성 True Positive 진단)", "• AI 예측 확률 94.2% 불량 판정\n• SHAP 분해 결과: 800V RF 플라즈마 전압 스파이크 서지 발생 및 와이어 본딩 단선 결함.\n• 조치: 해당 로트 즉각 격리 및 전수 검사 발령."),
        ("트랙 2. Wafer #242 (위양성 False Positive 규명)", "• AI 예측 확률 78.4% 불량 경보 (실제로는 정상)\n• SHAP 분해 결과: 챔버 전극 마모 한계에 근접하여 관리 기준선 경계에 도달.\n• 현장 해석: 단순 오작동이 아닌 '설비 사고 방지를 위한 안전 여유분(Safety Margin)'에 의한 의도적 선제 경보임이 입증됨."),
        ("현장 도입 가치", "엔지니어가 AI의 알람을 불신하여 무시하거나 불필요하게 전체 라인을 셧다운하는 혼란을 원천 차단함.")
    ]

    for ti, de in xai_cases:
        pt = tf13.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_LIGHT
        pt.space_before = Pt(8)

        pd = tf13.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s13, """[슬라이드 13 | XAI 투트랙 의사결정 지원 엔진 - 08:00 누적]
다음으로 현장 엔지니어가 가장 신뢰하는 '투트랙 XAI 엔진'입니다.
AI가 '불량이다'라고 알람을 울렸을 때, 엔지니어는 '왜 불량인가?'를 알아야 조치할 수 있습니다.
우측 그래프를 보시면 두 가지 대표 샘플이 있습니다.
첫째, 진양성인 Wafer #1254는 800V RF 플라즈마 전압 서지와 단선이 핵심 원인임을 SHAP 기여도로 즉시 진단했습니다.
둘째, 정상임에도 알람이 울린 위양성 Wafer #242는 챔버 전극 마모가 관리 기준선에 근접하여 발생한 '안전 여유분(Safety Margin)'에 의한 선제 경보였음을 규명했습니다.
이를 통해 엔지니어는 불필요한 라인 중단 없이 챔버 사전 점검을 수행할 수 있습니다.""")

    # SLIDE 14: 글로벌 센서 영향도 및 챔버 인터록 연계
    s14 = prs.slides.add_slide(blank_layout)
    set_bg(s14, LIGHT_BG)
    add_header(s14, "PART 3. 관제 시스템 구축 과정", "5단계: 글로벌 센서 영향도 도출 및 챔버 인터록 시스템 연계", "공정 전체를 지배하는 Top 센서 규명 및 임계치 초과 시 0.1초 내 밸브 자동 차단 인터록 설계")
    add_footer(s14, 14)

    img_glob = find_pic("Day3_고도화_SHAP_글로벌")
    if img_glob:
        s14.shapes.add_picture(img_glob, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    else:
        add_card(s14, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG)

    # Left content box
    add_card(s14, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=PURPLE)
    tx14 = s14.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf14 = tx14.text_frame
    tf14.word_wrap = True

    p = tf14.paragraphs[0]
    p.text = "⚡ 글로벌 중요 센서 Top 10 및 인터록 매핑"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    interlock_points = [
        ("1. 공정 전체를 지배하는 Top 3 센서 계통", "• 1위 (압력 안정성): feature_59 (CVD 챔버 진공도)\n• 2위 (RF 전력): feature_103 (플라즈마 반사 전력)\n• 3위 (가스 유량): feature_210 (공정 가스 반응비)"),
        ("2. 챔버 하드웨어 인터록(Interlock) 연동", "위 3대 센서의 급격한 서지가 동시 발생할 경우, 모델의 추론 결과를 기다리지 않고 0.1초 내에 챔버 메인 밸브를 자동 차단하는 하드웨어 인터록 룰셋 수립."),
        ("3. 장비 제조사 매뉴얼 연계", "각 센서의 이상 범위 발생 시, 장비 매뉴얼(OEM Spec) 기준 허용 오차를 대조하여 2차 웨이퍼 파손 방지."),
        ("4. 관제 시스템 알림 자동 발송", "설비 이상 감지 즉시 라인 책임자 모바일 PWA 푸시 알림 및 사내 메신저 웹훅으로 10초 내 비상 전파.")
    ]

    for ti, de in interlock_points:
        pt = tf14.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PURPLE
        pt.space_before = Pt(8)

        pd = tf14.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s14, """[슬라이드 14 | 글로벌 센서 영향도 및 인터록 연계 - 08:30 누적]
개별 웨이퍼를 넘어 공정 전체를 지배하는 글로벌 센서 중요도를 우측 그래프와 같이 도출했습니다.
CVD 챔버의 진공 압력, 플라즈마 RF 반사율, 그리고 공정 가스 유량 센서가 불량 발생에 가장 결정적인 영향을 미쳤습니다.
저희는 이 핵심 센서들을 챔버 인터록 시스템과 직접 연계했습니다.
만약 이 3대 센서가 동시에 임계 한계를 이탈하면 0.1초 내에 챔버 밸브를 자동 차단하여 후속 웨이퍼의 연쇄 파손을 방지하도록 안전망을 구축했습니다.""")

    # SLIDE 15: 실시간 웹 관제 대시보드 구현
    s15 = prs.slides.add_slide(blank_layout)
    set_bg(s15, LIGHT_BG)
    add_header(s15, "PART 3. 관제 시스템 구축 과정", "6단계: 현장 맞춤형 듀얼 웹 관제 대시보드 구현", "기획서 05장 화면 설계 100% 반영: 2x2 위험 스캔, 18개월 유니버설 타임라인, PWA 반응형 웹")
    add_footer(s15, 15)

    # Left: Engineer View details
    add_card(s15, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx15_e = s15.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(4.9))
    tf15_e = tx15_e.text_frame
    tf15_e.word_wrap = True

    p = tf15_e.paragraphs[0]
    p.text = "🖥️ [현장 엔지니어 화면] 2x2 위험 스캔 UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_LIGHT

    e_feats = [
        ("상위 20% 의심 웨이퍼 카드 뷰", "테스트셋 314장 중 63장의 위험 웨이퍼를 카드 형태로 시각화. 위험도 1위부터 정렬되어 터치/클릭 즉시 상세 분석."),
        ("정상 기준선(Baseline) 오버레이 차트", "선택된 웨이퍼의 센서 측정치와 1,170장 정상 기준선(5~95%)을 한 화면에 오버레이하여 이상 폭을 직관적으로 확인."),
        ("실시간 현장 판정 피드백 등록", "'정밀 계측 발령(Defect Action)' 또는 '양품 판정(Normal Pass)' 버튼 클릭 시 현장 로그에 실시간 기록."),
        ("모바일 PWA 완벽 지원", "라인 방진복 착용 상태에서도 태블릿/스마트폰으로 신속 조작 가능.")
    ]

    for ti, de in e_feats:
        pt = tf15_e.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_DARK
        pt.space_before = Pt(8)

        pd = tf15_e.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    # Right: Admin View details
    add_card(s15, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2), bg=CARD_BG, border=SUCCESS)
    tx15_a = s15.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(4.9))
    tf15_a = tx15_a.text_frame
    tf15_a.word_wrap = True

    p_a = tf15_a.paragraphs[0]
    p_a.text = "📊 [공정 관리자 화면] 5대 관제 센터 & 타임라인"
    p_a.font.size = Pt(13)
    p_a.font.bold = True
    p_a.font.color.rgb = SUCCESS

    a_feats = [
        ("18개월 유니버설 타임라인 슬라이더", "2008.07 ~ 2009.12 구간의 월별 데이터를 슬라이더로 조작하면 5대 센터 전체가 해당 월로 즉시 재집계."),
        ("5대 전문 관제 센터 탭 전환", "• 수율 관제 센터: 월별 생산량 및 불량률 추이\n• 센서 표류 센터: CVD 상승/에처 하강 Z-Score 추이\n• XAI 원인 센터: #1254 vs #242 인터랙티브 대조\n• LLM 위키 센터: 공정 지식 검색\n• 알림 관리 센터: 실시간 인터록 및 경보 내역"),
        ("인수인계 교대 리포트 자동 생성", "일일 점검 내역과 챔버 표류 경보를 마크다운 리포트로 자동 빌드하여 교대 근무자에게 즉시 인계.")
    ]

    for ti, de in a_feats:
        pt = tf15_a.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_DARK
        pt.space_before = Pt(8)

        pd = tf15_a.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s15, """[슬라이드 15 | 실시간 웹 관제 대시보드 구현 - 09:10 누적]
이 모든 알고리즘을 현장에서 실제로 사용하는 웹 관제 대시보드로 완벽히 구현했습니다.
좌측은 '현장 엔지니어 화면'입니다. 2x2 위험 스캔 카드를 통해 상위 63장의 웨이퍼를 신속하게 확인하고 원클릭으로 조치를 발령합니다.
우측은 '공정 관리자 화면'입니다. 18개월 유니버설 타임라인을 슬라이더로 움직이면 수율 관제, 센서 표류, XAI 원인 규명, LLM 위키 검색까지 5대 센터의 통계가 즉시 동기화됩니다.
현재 로컬 서버에서 100% 완벽하게 동작 중입니다.""")

    # SLIDE 16: 지식 자산화: Karpathy 3계층 LLM 공정 위키
    s16 = prs.slides.add_slide(blank_layout)
    set_bg(s16, LIGHT_BG)
    add_header(s16, "PART 3. 관제 시스템 구축 과정", "7단계: 지식 자산화 - Andrej Karpathy 3계층 LLM 공정 위키", "단순 일회성 채팅을 넘어 마크다운과 양방향 링크([[...]])로 공정 지식을 복리 축적하는 지식 네트워크")
    add_footer(s16, 16)

    # 4 Layer Horizontal Flow Cards
    wiki_layers = [
        ("1. raw/ (원천 데이터)", "불변 보존 계층", "센서 계측 원본 CSV, 설비 매뉴얼 원문, 팹 작업 일지 (Read-Only)", PRIMARY_DARK, CARD_BG),
        ("2. sources/ (배치 요약)", "일일 계측 요약", "source_2008_08.md, 일일 배치 측정치 1:1 요약 및 이상치 추출", PRIMARY_LIGHT, PRIMARY_SOFT),
        ("3. concepts/ & entities/", "정제된 지식 계층", "Chamber_CVD_01.md, Sensor_Drift.md, 설비·센서별 양방향 위키링크", SUCCESS, SUCCESS_SOFT),
        ("4. synthesis/ (종합 리포트)", "복리 축적 지식", "August_Spike_vs_September.md, 다월간 교차 비교 및 재발 방지책", PURPLE, PURPLE_SOFT),
    ]

    for i, (ti, sub, de, col, bg_col) in enumerate(wiki_layers):
        wx = Inches(0.8 + i * 2.98)
        wy = Inches(1.5)
        ww = Inches(2.8)
        wh = Inches(3.6)

        add_card(s16, wx, wy, ww, wh, bg=bg_col, border=col)
        tx = s16.shapes.add_textbox(wx + Inches(0.15), wy + Inches(0.15), ww - Inches(0.3), wh - Inches(0.3))
        tf = tx.text_frame
        tf.word_wrap = True

        p_h = tf.paragraphs[0]
        p_h.text = ti
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = col
        p_h.font.name = "Pretendard"

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(10)
        p_s.font.bold = True
        p_s.font.color.rgb = PRIMARY_DARK
        p_s.font.name = "Pretendard"
        p_s.space_before = Pt(4)

        p_d = tf.add_paragraph()
        p_d.text = de
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = TEXT_MAIN
        p_d.font.name = "Pretendard"
        p_d.space_before = Pt(8)

    # Bottom Callout Card: Karpathy Philosophy
    add_card(s16, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.5), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx_kp = s16.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(11.3), Inches(1.3))
    tf_kp = tx_kp.text_frame
    tf_kp.word_wrap = True

    p0 = tf_kp.paragraphs[0]
    p0.text = "💡 Andrej Karpathy LLM Wiki 철학: '일회성 채팅 프롬프트에서 마크다운 지식 네트워크로'"
    p0.font.size = Pt(11.5)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY_DARK

    p1 = tf_kp.add_paragraph()
    p1.text = "기존 챗봇은 대화가 끝나면 지식이 사라지지만, SEMI-GUARD의 LLM 공정 위키는 챔버 트러블슈팅과 센서 드리프트 내역을 영구 마크다운 문서로 기록하고 양방향 링크([[...]])로 연결합니다. 새로운 엔지니어가 부임해도 1초 만에 과거 유사 고장 사례를 학습할 수 있어 팹의 지식이 복리로 성장합니다."
    p1.font.size = Pt(9.5)
    p1.font.color.rgb = TEXT_MAIN
    p1.space_before = Pt(4)

    set_notes(s16, """[슬라이드 16 | 지식 자산화 Karpathy LLM 공정 위키 - 09:40 누적]
SEMI-GUARD의 마지막 독창적 차별점은 Andrej Karpathy 아키텍처에 기반한 '3계층 LLM 공정 위키'입니다.
일반적인 AI 시스템은 질문하고 답변을 받으면 지식이 휘발됩니다.
저희는 원천 데이터(raw)에서 출발하여, 일일 요약(sources), 설비와 센서의 독립 엔티티(entities), 그리고 다월간 종합 분석(synthesis)으로 지식이 단계별로 마크다운 문서로 영구 축적됩니다.
모든 문서가 옵시디언 양방향 링크로 연결되어 있어, 신입 엔지니어가 들어와도 챔버 명칭 하나만 검색하면 과거 유사 고장 이력과 조치 가이드를 즉시 전수받을 수 있습니다.""")

    # =========================================================================
    # PART 4: VERIFICATION, IMPACT & ROADMAP (Slide 17 & 18)
    # =========================================================================
    # SLIDE 17: 기획 요구사항 검증 및 경제적 기대효과
    s17 = prs.slides.add_slide(blank_layout)
    set_bg(s17, LIGHT_BG)
    add_header(s17, "PART 4. 검증 결과 및 향후 로드맵", "기획서 핵심 요구사항(C01~C08) 100% PASS 검증 및 기대 효과", "초기 기획서의 가설 검증 기준을 완벽하게 충족하며 실증된 데이터 분석 및 시스템 완성도")
    add_footer(s17, 17)

    # Left: C01~C08 Verification Checklist
    add_card(s17, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2), bg=CARD_BG, border=SUCCESS)
    tx17_c = s17.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(6.4), Inches(4.9))
    tf17_c = tx17_c.text_frame
    tf17_c.word_wrap = True

    p = tf17_c.paragraphs[0]
    p.text = "✅ 기획서 요구사항(C01~C08) 100% PASS 검증 결과표"
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK

    checks = [
        ("C01. 전수 검사 용량 한정", "테스트셋 314장 중 정확히 상위 20%(63장) 전수 검사 준수", "PASS"),
        ("C02. 불량 재현율 목표 달성", "목표(60%)를 크게 상회하는 Recall@20% 71.4% (15/21개) 달성", "PASS"),
        ("C03. 결정론적 재현성 보장", "Score DESC + Wafer ID ASC Tie-Breaking 규칙으로 100% 재현", "PASS"),
        ("C04. 정상 참조 분포 구축", "정상 웨이퍼 1,170장 대상 5~95 백분위수 정상 기준선 완성", "PASS"),
        ("C05. 시계열 설비 표류 감지", "Tri-Criteria 엔진으로 8월 34주차 CVD/에처 표류 조기 경보", "PASS"),
        ("C06. 투트랙 XAI 원인 설명", "진양성 #1254(RF 서지) vs 위양성 #242(안전 마진) SHAP 입증", "PASS"),
        ("C07. 실시간 웹 관제 시스템", "현장 엔지니어 2x2 그리드 + 관리자 5대 관제 센터 실동작", "PASS"),
        ("C08. LLM 공정 지식 위키", "Karpathy 3계층 마크다운 지식 네트워크 및 양방향 링크 가동", "PASS"),
    ]

    for code, desc, status in checks:
        pr = tf17_c.add_paragraph()
        pr.text = f"• [{status}] {code}: {desc}"
        pr.font.size = Pt(9.5)
        pr.font.color.rgb = SUCCESS if status == "PASS" else TEXT_MAIN
        pr.space_before = Pt(4)

    # Right: Economic & Operational Impact
    add_card(s17, Inches(7.8), Inches(1.5), Inches(4.733), Inches(5.2), bg=CARD_BG, border=PRIMARY_LIGHT)
    tx17_e = s17.shapes.add_textbox(Inches(8.0), Inches(1.65), Inches(4.333), Inches(4.9))
    tf17_e = tx17_e.text_frame
    tf17_e.word_wrap = True

    p_e = tf17_e.paragraphs[0]
    p_e.text = "💰 정량적 및 정성적 기대 효과"
    p_e.font.size = Pt(12.5)
    p_e.font.bold = True
    p_e.font.color.rgb = PRIMARY_DARK

    impacts = [
        ("수율 손실 비용 대폭 절감", "기준 모델 대비 불량 3장을 추가 포획(12장➔15장)하여, 팹 라인당 연간 수십억 원 상당의 결함 유출 배상 손실을 사전 차단."),
        ("설비 돌발 셧다운 방어", "Tri-Criteria 표류 감지를 통해 챔버 돌발 고장을 2~3주 전에 사전 감지하여 예방보전(PM) 스케줄링 최적화."),
        ("검사 리소스 80% 절감", "590개 전체 센서를 전수 검사하지 않고, 상위 20% 의심 웨이퍼와 78개 유효 센서에만 계측 장비를 집중 투입."),
        ("팹 지식 자산화 및 인수인계", "엔지니어 퇴사나 교대 시에도 공정 트러블슈팅 지식이 LLM 위키에 영구 보존되어 인수인계 시간 70% 단축.")
    ]

    for ti, de in impacts:
        pt = tf17_e.add_paragraph()
        pt.text = ti
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = PRIMARY_LIGHT
        pt.space_before = Pt(8)

        pd = tf17_e.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MAIN
        pd.space_before = Pt(2)

    set_notes(s17, """[슬라이드 17 | 기획 요구사항 검증 및 경제적 기대효과 - 10:00 누적]
마지막 파트로 검증 결과와 기대 효과입니다.
초기 기획서에서 수립했던 C01부터 C08까지 8대 핵심 가설 및 기능 요구사항을 100% PASS 검증 완료했습니다.
상위 20% 이내 전수 검사, 재현율 70% 돌파, 결정론적 재현성, 투트랙 XAI, 그리고 웹 관제 시스템과 지식 위키까지 전 항목을 완벽히 입증했습니다.
이를 통해 결함 유출 손실을 사전에 차단하고, 돌발 셧다운을 방어하며, 팹의 공정 지식을 영구 자산화하는 막대한 경제적 효과를 창출합니다.""")

    # SLIDE 18: 향후 로드맵 및 결론 & Q&A
    s18 = prs.slides.add_slide(blank_layout)
    set_bg(s18, DARK_BG)

    # Title box
    t18_box = s18.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.3), Inches(1.8))
    tf18 = t18_box.text_frame
    tf18.word_wrap = True

    p = tf18.paragraphs[0]
    p.text = "CONCLUSION & FUTURE ROADMAP"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(56, 189, 248)

    p1 = tf18.add_paragraph()
    p1.text = "향후 고도화 로드맵 및 질의응답 (Q&A)"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_before = Pt(4)

    p2 = tf18.add_paragraph()
    p2.text = "데이터 과학적 모델링 비교부터 실시간 관제 시스템 엔지니어링까지 완결된 SEMI-GUARD"
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(4)

    # 3 Future Roadmap Cards
    roadmaps = [
        ("Phase 1. 초당 스트리밍 연동", "Apache Kafka & MQTT 기반", "초당 수천 개 센서 데이터가 유입되는 양산 팹 실시간 스트리밍 파이프라인 연계 및 분산 처리", RGBColor(59, 130, 246)),
        ("Phase 2. 자율 인터록 Tool Calling", "LLM Agent 함수 호출 제어", "위키 에이전트가 챔버 드리프트 감지 시 안전 프로토콜에 따라 설비 밸브를 자율 차단하는 액션 함수 호출", RGBColor(16, 185, 129)),
        ("Phase 3. 디지털 트윈 시뮬레이터", "공정 물리 모델 융합", "센서 데이터와 챔버 유체역학(CFD) 물리 모델을 결합하여 가상 웨이퍼 불량을 사전에 시뮬레이션", RGBColor(245, 158, 11)),
    ]

    for i, (ti, sub, de, col) in enumerate(roadmaps):
        rx = Inches(1.0 + i * 3.84)
        ry = Inches(2.8)
        rw = Inches(3.6)
        rh = Inches(2.6)

        r_shp = s18.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, rx, ry, rw, rh)
        r_shp.fill.solid()
        r_shp.fill.fore_color.rgb = RGBColor(15, 23, 42)
        r_shp.line.color.rgb = col
        r_shp.line.width = Pt(1.5)

        tx = s18.shapes.add_textbox(rx + Inches(0.18), ry + Inches(0.18), rw - Inches(0.36), rh - Inches(0.36))
        tf = tx.text_frame
        tf.word_wrap = True

        ph = tf.paragraphs[0]
        ph.text = ti
        ph.font.size = Pt(12.5)
        ph.font.bold = True
        ph.font.color.rgb = col

        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(10)
        ps.font.bold = True
        ps.font.color.rgb = RGBColor(241, 245, 249)
        ps.space_before = Pt(4)

        pd = tf.add_paragraph()
        pd.text = de
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = RGBColor(203, 213, 225)
        pd.space_before = Pt(8)

    # Bottom Contact & Thanks
    c_box = s18.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.3), Inches(1.1))
    tfc = c_box.text_frame
    tfc.word_wrap = True
    p_thx = tfc.paragraphs[0]
    p_thx.text = "경청해 주셔서 대단히 감사합니다. 질문을 주시면 상세히 답변드리겠습니다."
    p_thx.font.size = Pt(15)
    p_thx.font.bold = True
    p_thx.font.color.rgb = RGBColor(56, 189, 248)
    p_thx.alignment = PP_ALIGN.CENTER

    p_subthx = tfc.add_paragraph()
    p_subthx.text = "SEMI-GUARD 개발팀   |   웹 대시보드 라이브 시연 가능 (http://localhost:8000)"
    p_subthx.font.size = Pt(11)
    p_subthx.font.color.rgb = RGBColor(148, 163, 184)
    p_subthx.alignment = PP_ALIGN.CENTER
    p_subthx.space_before = Pt(4)

    set_notes(s18, """[슬라이드 18 | 향후 로드맵 및 결론 - 10:10 누적]
결론을 말씀드리겠습니다.
SEMI-GUARD는 단순한 결과 나열형 머신러닝 프로젝트가 아닙니다.
기획서의 목적에 입각하여 문제 정의부터 시작해, 정합성 높은 데이터 전처리, 6종 모델 체계적 비교와 실패 분석을 통한 챔피언 모델 선정, 그리고 8월 불량 스파이크를 규명한 시계열 PdM 엔진, 투트랙 XAI, 현장 맞춤형 듀얼 웹 관제 대시보드와 Karpathy LLM 공정 위키까지 유기적으로 완성된 종합 플랫폼입니다.
향후에는 Kafka 실시간 스트리밍과 LLM 에이전트의 자율 인터록 함수 호출로 더욱 발전시켜 나갈 계획입니다.
지금 즉시 웹 애플리케이션을 통한 6단계 라이브 시연이 가능합니다.
경청해 주셔서 대단히 감사합니다. 질문을 주시면 상세히 답변드리겠습니다.""")

    output_path = "SEMI_GUARD_발표자료.pptx"
    prs.save(output_path)
    print(f"[SUCCESS] Successfully generated presentation deck: {output_path} (18 slides, 16:9 widescreen, planning doc aligned)")

if __name__ == "__main__":
    create_deck()
