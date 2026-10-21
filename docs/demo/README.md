# Gemini 3.8 Flash 실제 시연

2026-10-20 · 로컬 서비스에서 실제 CSV 업로드와 Gemini API 질의를 실행했다.

- 파일: simulation/sim_batch_300_200906_200908.csv (합성 검증 CSV)
- 기본 분석: 300행, 590센서, 결측 8,064셀 (4.555932%)
- 첫 질문: 월별 표본 수·불량률 비교 → time_summary → 2009-08, 101건 중 14건, 13.86%
- 후속 질문: 상위 20% 검토 성능 → evaluate_predictions → 검토 60건, TP 5, FN 17, Recall 22.73%
- 모델: gemini-3.8-flash (실제 API 응답)
- 자동 검증: 35개 통과

![기본 분석](01_basic_analysis.jpg)

![Gemini 답변과 실제 Tool 근거](02_gemini_agent.jpg)

live_demo.json에는 화면에서 읽은 대화와 Tool 계산 JSON을 보관했다. 인증 정보는 포함하지 않는다.


공정 관제 서브페이지 직접 검증: `03_dashboard_hub.jpg`, `04_dashboard_agent.jpg`, `05_dashboard_performance.jpg`. 여름 CSV의 8월 101행을 선택하고 25% 검토 시 26행 선정, TP 6·FP 20·FN 8·TN 67을 표시했다. 같은 범위의 Gemini 실제 질의는 101행·불량 14건·13.86%를 Tool로 계산했다.


`06_wafer_detail.jpg`: 500행 CSV의 표본 2184 센서 상태·누적 SHAP·FP 검토 권고. `detail_agent_answer.txt`: Gemini의 diagnose_sample 실제 호출 답변.
