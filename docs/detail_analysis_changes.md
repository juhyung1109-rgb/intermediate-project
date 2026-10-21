# 기존 상세 분석의 실계산 연결

기준일 2026-10-20. 기획안 v1.1 이후 추가 구현이며 저장 모델은 변경하지 않았다.

## 소스 검토 결과

`tools/`의 파일은 실행 가능한 분석 함수와 과거 정적 화면을 생성·수정하는 스크립트가 섞여 있다. 과거 화면 생성 스크립트를 현재 웹 파일에 재실행하지 않고 계산을 재사용 가능한 서비스 함수로 옮겼다.

|참고 소스|기존 동작과 문제|현재 구현|
|---|---|---|
|`build_all_cumulative_data.py`|추론 뒤 CSV 자체 평균으로 Z 계산. 평균을 `normal_median`에 기록. 일부 전처리 누락 시 업로드 중앙값으로 대체.|저장 전처리로만 추론. 학습 정상 1170행의 평균·중앙값·표준편차·5~95%를 구분.|
|`populate_all_wafer_details.py`|상세값이 없으면 라벨별 센서값과 Z를 생성하고 Z에서 임의 SHAP을 계산. 정상 안정 기여도 -0.18/-0.15 고정 추가.|원본 센서와 TreeExplainer만 사용. 실제 전체 SHAP 합과 나머지 피처를 포함하는 누적 워터폴.|
|`refine_app_js_v23.py`|일부 센서·SHAP의 대체 값과 물리 센서명 고정.|검증된 물리 매핑이 없으므로 feature 번호를 사용. 계산 실패는 오류로 표시.|
|`make_unified_data.py`|시험 표본 ID로 측정 날짜를 추정하고 정적 누적 지표 생성.|실제 CSV timestamp만 사용. 선택 데이터셋·기간에서 순위와 분류 재계산.|
|`src/analysis.py`의 `compare_reference`, `explain_sample_shap`|정상군 통계·기여도 분석. 표본 검색 실패 시 첫 행으로 대체하는 경로 존재.|ID 불일치는 오류. 실제 원본 행을 연결하고 결측을 0이나 가짜 Z로 만들지 않음.|
|`src/analysis.py`의 `detect_sensor_drift`|Pearson·Kendall·표준화 이동·기저 이동·종합 지수. 행 순서를 시간으로 사용하고 100행 창이 겹칠 수 있음.|실제 경과 일수, 동일 시각 평균, 결측 제외, 겹치지 않는 초기/후기 창으로 계산.|
|`src/analysis.py`의 `get_global_shap_importance`|시험셋 평균 절대 SHAP.|선택 CSV와 기간에 적용. 기본 최대 200행 균등 표본, 최대 500행. 실제 분석 수와 표본 선택 방법 표시.|

## 추가 Tool과 화면

- `diagnose_sample(sample_id, review_ratio=null)`: 위험 순위·정답 분류, Top 5 센서와 참고 구간·상태, 결측 수, 실제 SHAP 증가·감소, 누적 워터폴, D01~D05 검토 권고.
- `sensor_drift(direction, limit)`: Pearson r·Kendall tau·기간 표준화 이동·초기후기 기저 이동·종합 지수와 월별 원본 평균. 상승·하강·전체 필터.
- `global_shap(limit, max_samples)`: 평균 절대 SHAP 중요도와 실제 분석 범위.

현재 등록 Tool은 12개다. CSV 분석실에는 표본 ID 검색과 각 예측 행의 정밀분석 버튼, 전체 SHAP과 시간 드리프트 실행 버튼을 추가했다. 관제 서브페이지는 동일 분석 함수와 공통 렌더러를 사용한다. 분석 질문 버튼은 Gemini 질문을 준비하며, 점검 지시 초안 버튼은 근거와 체크 항목을 채운다. 등록 전에는 사람이 내용을 확인한다.

Z는 `(원본값 - 학습 정상 평균) / 표본 표준편차(ddof=1)`다. 중앙값은 대조값으로 별도 표시한다. 1.5σ·2σ와 5~95% 참고 구간은 탐색 기준이며 실제 장비 규격이 아니다. 정상 라벨 FP를 근거로 자동 통과시키거나 불량 라벨을 근거로 장비 정지·부품 교체를 명령하지 않는다. Wiki 연결은 추가하지 않았다.

## 검증

자동 검증 48개 통과. 실제 CSV의 표본 2184에서 위험 점수 1.76%, 현재 파일 500행 중 순위 1위, FP를 확인했다. 최대 편차는 feature_226의 약 +3.676σ이고 위험 증가 SHAP 상위는 feature_104 +0.815, feature_489 +0.707, feature_68 +0.493이다. 다른 센서가 최대 통계 편차와 최대 모델 기여를 갖는 점도 원본과 모델 계산으로 구분된다.

Gemini 3.8 Flash가 실제 `diagnose_sample` 1회 호출로 해당 수치와 결측 4개, FP의 예방 점검 후보 권고를 설명했다. 전체 중요도는 200/500행으로 계산한 사실을 화면에 표시했다. 시간 분석에서 엄격한 상승·하강 후보가 없으면 빈 결과를 정상적으로 표시한다.

```sh
python tools/analyze_wafer.py --sample-id 2184 --include-drift --include-global-shap --output artifacts/analysis_reports/detail_2184.json
```

CLI도 웹과 같은 공통 파이프라인을 사용하며, 임시 SQLite만 사용해 웹 세션 데이터에 추가하지 않는다. 결과의 dataset_id는 CLI 분석 식별자다. 모델 재학습과 Cloud Run 배포는 수행하지 않았다.
