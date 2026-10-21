# SEMI-GUARD 실시간 현장 관제 및 진단 시연 캡처

배포된 SEMI-GUARD 통합 플랫폼([Cloud Run](https://semiguard-app-ahftuulaqq-uc.a.run.app/))의 실제 화면 캡처 및 진단 결과 기록입니다.

## 🖼️ 실시간 화면 캡처 목록
1. `01_live_hub_engineer.png`: **현장 엔지니어 전용 관제 센터 (Field Engineer Hub)**
   - 실시간 웨이퍼 불량 진단, 챔버 노후화 점검표, SHAP 1:1 비교, SEMI-AI 분석 챗봇 빠른 진입 카드 뷰
2. `02_live_wafer_triage.png`: **초고속 불량 센서 정밀 진단실 (Wafer Triage)**
   - 웨이퍼 표본 #3295 검색 결과: 위험도 게이지 1.97%, TreeExplainer SHAP 워터폴 원인 분해, 정상 대비 5대 이탈 센서 목록 및 현장 조치 가이드
3. `03_live_shap_comparison.png`: **SHAP 원인 분석 요약 (1:1 비교)**
   - 진짜 불량(TP #3215) vs 가양성(FP #3295) 기여 요인 1:1 대조 분석 및 설비 예지보전 조치 권고
4. `04_live_model_performance.png`: **AI 모델 종합 성과 (우선검토 시뮬레이션)**
   - 5% ~ 50% 검토 비율별 혼동행렬(Confusion Matrix), Recall(적발률), Precision(정밀도), Lift(검출 배수) 시뮬레이션 성과표
5. `05_live_chamber_pdm.png`: **챔버 노후화 일상 점검표 (현장 실무자 모드)**
   - 4단계 실시간 설비 노후화 점검 스케줄 파이프라인, Dry Etch 건식 식각 챔버 하부 전극/포커스링 마모 진단 지침 체크리스트 및 실무자 조치 소견 제출
6. `06_live_ai_agent.png`: **SEMI-AI 공정 분석 챗봇 (Gemini 3.8 Flash)**
   - 12개 Python Tool 실시간 연동, 월별 불량률/검토 성능/드리프트 센서 프리셋 및 자유 자연어 대화 질의 인터페이스
