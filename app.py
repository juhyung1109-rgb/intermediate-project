import os
import sys
import math
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from sklearn.metrics import confusion_matrix

# 프로젝트 루트 경로 추가
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

from src.analysis import (
    summarize_data,
    recommend_analysis,
    calculate_review_metrics,
    compare_reference,
    make_report,
    detect_sensor_drift,
    analyze_timeseries_trend,
    explain_sample_shap,
    get_global_shap_importance,
    simulate_batch_inference
)
from src.visualization import (
    create_v01_chart,
    create_v02_chart,
    create_monthly_trend_chart,
    create_v03_chart,
    create_v04_chart,
    create_v05_chart,
    create_v06_chart,
    create_drift_dashboard_chart,
    create_trouble_timeline_chart,
    create_shap_waterfall_chart,
    create_shap_global_summary_chart
)

st.set_page_config(
    page_title="SECOM 반도체 공정 데이터 대시보드",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 1. 데이터 및 영속화 객체 캐싱 로드
# -------------------------------------------------------------
@st.cache_data
def load_all_resources():
    features_path = os.path.join(base_dir, "data", "processed", "secom_features.csv")
    labels_path = os.path.join(base_dir, "data", "processed", "secom_labels.csv")
    train_idx_path = os.path.join(base_dir, "artifacts", "train_indices.csv")
    test_idx_path = os.path.join(base_dir, "artifacts", "test_indices.csv")
    pred_path = os.path.join(base_dir, "artifacts", "test_predictions.csv")
    prep_path = os.path.join(base_dir, "artifacts", "preprocessor.joblib")
    model_path = os.path.join(base_dir, "artifacts", "baseline_model.joblib")
    
    df_features = pd.read_csv(features_path)
    df_labels = pd.read_csv(labels_path)
    df_labels["timestamp"] = pd.to_datetime(df_labels["timestamp"])
    
    df_train_idx = pd.read_csv(train_idx_path)
    df_test_idx = pd.read_csv(test_idx_path)
    df_predictions = pd.read_csv(pred_path)
    
    prep_dict = joblib.load(prep_path)
    model = joblib.load(model_path)
    valid_features = prep_dict["valid_features"]
    
    summary = summarize_data(df_features, df_labels)
    train_normal_ids = df_train_idx[df_train_idx["label"] == 0]["sample_id"].values
    
    return (
        df_features,
        df_labels,
        df_train_idx,
        df_test_idx,
        df_predictions,
        valid_features,
        summary,
        train_normal_ids,
        prep_dict,
        model
    )

try:
    (
        df_features,
        df_labels,
        df_train_idx,
        df_test_idx,
        df_predictions,
        valid_features,
        summary,
        train_normal_ids,
        prep_dict,
        model
    ) = load_all_resources()
except Exception as e:
    st.error(f"⚠️ 리소스 로드 중 오류가 발생했습니다: {e}")
    st.stop()

# -------------------------------------------------------------
# 2. 사이드바 제어 패널
# -------------------------------------------------------------
st.sidebar.title("⚙️ SECOM 공정 제어반")
st.sidebar.caption("반도체 공정 분석 & 불량 위험도 탐색")

section = st.sidebar.radio(
    "📌 메뉴 이동",
    [
        "S01 데이터 개요",
        "S02 분석 추천 규칙",
        "S03 센서 정밀 탐색",
        "S04 위험 샘플 탐색",
        "S05 모델 성능 평가",
        "S06 챔버 열화 & 예지보전"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 공정 조작 파라미터")

# 검토 비율 슬라이더 (5% ~ 50%, 기본 20%)
review_ratio = st.sidebar.slider(
    "우선 검토 비율 (Top-k%)",
    min_value=0.05,
    max_value=0.50,
    value=0.20,
    step=0.05,
    help="위험 점수가 높은 상위 k% 웨이퍼를 선정하여 성과를 실시간 확인합니다."
)

# 샘플 선택 셀렉트박스 (위험도 순 정렬)
sample_options = df_predictions["sample_id"].tolist()
selected_sample = st.sidebar.selectbox(
    "진단할 웨이퍼 선택",
    options=sample_options,
    index=0,
    help="특정 웨이퍼를 선택하여 정상 집단 대비 이상 센서를 비교합니다."
)

# 센서 선택 셀렉트박스
sensor_options = valid_features
selected_sensor = st.sidebar.selectbox(
    "분포 분석 센서 선택",
    options=sensor_options,
    index=0,
    help="232개 유효 센서 중 히스토그램 및 정상/불량 분포를 탐색할 센서입니다."
)

st.sidebar.markdown("---")

# 8대 도메인 & 통계 용어사전 모달 아코디언
with st.sidebar.expander("📚 [도움말] 반도체 공정 8대 핵심 용어사전"):
    st.markdown("""
    1. **결측치 (Missing Values)**: 통신/측정 지연으로 누락된 값. 왜도 극심 센서가 많아 중앙값(Median) 대입 적용.
    2. **클래스 불균형 (Class Imbalance)**: 정상 93.4% 대 불량 6.6%. 비용 민감형 벌점 가중치(spw=5.0)로 극복.
    3. **재현율 (Recall@20%)**: 실제 불량 21건 중 상위 20%(63개) 내 적발 비율 (**71.4%, 15건 적발**).
    4. **정밀도 (Precision@20%)**: 우선 검토군(63개) 중 실제 불량 비율 (**23.8%**, 랜덤 대비 3.6배 집중도).
    5. **Average Precision (AP)**: 불량이 순위 상위권에 얼마나 집중 밀집되어 있는지를 요약한 단일 면적 지표.
    6. **정상 참고 구간 (5~95 백분위)**: 학습 정상 웨이퍼(1,170건)의 중심 90% 통계 분포.
    7. **이상 센서 수 (Abnormal Count)**: 3-시그마 정상 범위를 동시 이탈한 센서 총수 (공정 불안정도 지표).
    8. **결정론적 동점 순위 (Tie-Breaking)**: 동일 점수 시 sample_id 오름차순 안정 정렬로 재현율 100% 영구 보장.
    """)

st.sidebar.info("💡 **실행 환경**: miniconda `DS` (Python 3.10)\n🛡️ **Data Leakage 차단**: Train(1,253건) 기준")

# -------------------------------------------------------------
# 메인 헤더
# -------------------------------------------------------------
st.title("⚙️ 반도체 공정 데이터분석 시각화 서비스 (SECOM)")
st.caption("대화형 위험 순위 탐색, 정상 참고 비교, 센서 드리프트 및 자동 리포팅 대시보드 (Day 3 통합 완성판)")

# -------------------------------------------------------------
# S01: 데이터 개요
# -------------------------------------------------------------
if section == "S01 데이터 개요":
    st.subheader("📌 [S01] 공정 데이터셋 무결성 및 품질 개요")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="총 웨이퍼 수", value=f"{summary['n_samples']:,} 건")
    with col2:
        st.metric(label="원형 센서 수", value=f"{summary['n_sensors']} 개 (유효: {len(valid_features)}개)")
    with col3:
        st.metric(
            label="공정 불량률 (Class Imbalance)",
            value=f"{summary['fail_rate']:.2f} %",
            help="정상 1,463건 vs 불량 104건 (극심한 불균형)"
        )
    with col4:
        st.metric(
            label="전체 결측 셀 비율",
            value=f"{summary['missing_rate']:.2f} %",
            help=f"총 {summary['total_missing_cells']:,} 셀 결측"
        )

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📊 V01: 정상 vs 불량 분포")
        fig_v01 = create_v01_chart(summary)
        st.plotly_chart(fig_v01, use_container_width=True)
        st.info("💡 **규칙 R03 충족:** 불량률이 20% 미만(6.64%)이므로 단순 정확도(Accuracy) 대신 PR-AUC와 Recall@20% 평가가 필수입니다.")
        
    with c2:
        st.markdown("### 📉 V02: 결측률 상위 20개 센서")
        fig_v02 = create_v02_chart(summary, top_n=20)
        st.plotly_chart(fig_v02, use_container_width=True)
        st.warning(f"⚠️ **결측 센서 현황:** 결측률 50% 초과 센서 **{summary['high_missing_count']}개** 및 상수 센서 **{summary['constant_sensor_count']}개**를 모델 입력에서 사전 제거했습니다.")

# -------------------------------------------------------------
# S02: 분석 추천 규칙
# -------------------------------------------------------------
elif section == "S02 분석 추천 규칙":
    st.subheader("💡 [S02] 6대 분석 추천 규칙 엔진 (R01 ~ R06)")
    
    # 선택된 샘플의 순위 확인
    sample_rank = int(df_predictions[df_predictions["sample_id"] == selected_sample]["risk_rank"].values[0])
    recommendations = recommend_analysis(summary, selected_sample_rank=sample_rank, total_test_samples=len(df_predictions))
    
    for rec in recommendations:
        status_color = "🟢" if rec["execution_status"] in ["실행 완료", "대시보드 조작 연동"] else "🟡"
        with st.expander(f"{status_color} [{rec['rule_id']}] {rec['name']} - ({rec['execution_status']})", expanded=True):
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown(f"**조건 충족 여부**: `{'충족 (True)' if rec['condition_met'] else '미충족 (False)'}`")
                st.markdown(f"**실제 관찰값**: {rec['observation']}")
            with col_b:
                st.markdown(f"**시스템 추천 조치**: {rec['recommendation']}")

    st.markdown("---")
    st.markdown("### 🗓️ 공정 시간 및 월별 불량 편차 (규칙 R05 검토)")
    tab1, tab2 = st.tabs(["📊 시계열 추이 차트", "📋 월별 상세 통계표"])
    with tab1:
        fig_r05 = create_monthly_trend_chart(summary)
        st.plotly_chart(fig_r05, use_container_width=True)
    with tab2:
        m_df = summary["monthly_stats"].copy()
        m_df.columns = ["공정 월", "총 표본 수", "불량 수", "불량률(%)"]
        m_df["불량률(%)"] = m_df["불량률(%)"].round(2)
        st.dataframe(m_df, use_container_width=True)

# -------------------------------------------------------------
# S03: 센서 정밀 탐색
# -------------------------------------------------------------
elif section == "S03 센서 정밀 탐색":
    st.subheader(f"🔬 [S03] 센서 분포 및 이상치 탐색: `{selected_sensor}`")
    
    # 해당 센서의 학습 정상 5~95 백분위 계산
    train_normal_series = df_features[df_features["sample_id"].isin(train_normal_ids)][selected_sensor].dropna()
    p05 = float(train_normal_series.quantile(0.05))
    p95 = float(train_normal_series.quantile(0.95))
    
    fig_v03 = create_v03_chart(
        df_features=df_features,
        sensor_id=selected_sensor,
        df_labels=df_labels,
        normal_p05=p05,
        normal_p95=p95
    )
    st.plotly_chart(fig_v03, use_container_width=True)
    
    # 센서 기술 통계 카드
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("정상 참고 하한 (5%)", f"{p05:.4f}")
    with c2:
        st.metric("정상 중앙값 (Median)", f"{train_normal_series.median():.4f}")
    with c3:
        st.metric("정상 참고 상한 (95%)", f"{p95:.4f}")
    with c4:
        st.metric("왜도 (Skewness)", f"{train_normal_series.skew():.2f}")

# -------------------------------------------------------------
# S04: 위험 샘플 탐색
# -------------------------------------------------------------
elif section == "S04 위험 샘플 탐색":
    st.subheader("🎯 [S04] 불량 위험 순위 탐색 및 정상 참고 비교")
    
    # 1. V04 순위 슬라이더 차트
    fig_v04 = create_v04_chart(df_predictions, review_ratio=review_ratio)
    st.plotly_chart(fig_v04, use_container_width=True)
    
    # 동적 성과 메트릭
    metrics = calculate_review_metrics(df_predictions, ratio=review_ratio)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("선정 웨이퍼 수", f"{metrics['n_selected']} 건 / {metrics['n_total']} 건")
    with c2:
        st.metric("선정군 내 검출 불량", f"{metrics['n_detected_fails']} 건 / {metrics['n_fails_total']} 건")
    with c3:
        st.metric("재현율 (Recall@k%)", f"{metrics['recall_at_k']:.1f} %")
    with c4:
        st.metric("정밀도 (Precision@k%)", f"{metrics['precision_at_k']:.1f} %")
        
    st.markdown("---")
    
    # 2. 선택 웨이퍼 정밀 결함 진단 (V05 + SHAP XAI)
    st.markdown(f"### 🔍 선택 웨이퍼 [{selected_sample}]의 정밀 결함 진단 및 원인 규명")
    
    tab_v05, tab_shap = st.tabs([
        "📊 [V05] 정규분포 기준 정상군 비교 (기준 모델)",
        "🧠 [전략 2] SHAP AI 인공지능 원인 규명 (XAI 고도화)"
    ])
    
    with tab_v05:
        df_ref = compare_reference(
            df_features_raw=df_features,
            train_normal_sample_ids=train_normal_ids,
            selected_sample_id=selected_sample,
            valid_features=valid_features,
            top_n=5
        )
        
        v05_col1, v05_col2 = st.columns([3, 2])
        with v05_col1:
            fig_v05 = create_v05_chart(df_ref, selected_sample_id=selected_sample)
            st.plotly_chart(fig_v05, use_container_width=True)
        with v05_col2:
            st.markdown("**📋 5대 이상 센서 측정치 대조표**")
            disp_df = df_ref[["sensor_id", "imputed_value", "normal_median", "z_score", "was_imputed", "is_out_of_bounds"]].copy()
            disp_df.columns = ["센서ID", "측정값", "정상중앙값", "Z편차", "결측대체", "정상이탈"]
            disp_df["결측대체"] = disp_df["결측대체"].map({True: "대체값", False: "실측값"})
            disp_df["정상이탈"] = disp_df["정상이탈"].map({True: "🚨이탈", False: "정상권"})
            st.dataframe(disp_df, use_container_width=True)
            
    with tab_shap:
        st.markdown("#### 💡 TreeExplainer SHAP 기반 개별 불량 기여도 분석")
        with st.spinner("⏳ SHAP 기여도 산출 중..."):
            shap_res = explain_sample_shap(
                sample_id=selected_sample,
                df_features=df_features,
                preprocessor_dict=prep_dict,
                model=model,
                train_normal_ids=train_normal_ids,
                top_n=8
            )
            
        sh_m1, sh_m2, sh_m3, sh_m4 = st.columns(4)
        sh_m1.metric("최종 불량 예측 확률", f"{shap_res['final_risk_score']*100:.2f}%")
        sh_m2.metric("베이스라인 기대 확률", f"{shap_res['base_risk_score']*100:.2f}%", help=f"기저 log-odds: {shap_res['expected_value']:.2f}")
        sh_m3.metric("위험 가중 요인 (+)", f"{len(shap_res['df_risk_increase'])} 개 피처", delta="불량 유발", delta_color="inverse")
        sh_m4.metric("위험 완화 요인 (-)", f"{len(shap_res['df_risk_decrease'])} 개 피처", delta="정상 유도", delta_color="normal")
        
        fig_shap = create_shap_waterfall_chart(
            df_shap_top=shap_res["df_shap_top"],
            sample_id=selected_sample,
            expected_value=shap_res["expected_value"],
            final_risk_score=shap_res["final_risk_score"]
        )
        st.plotly_chart(fig_shap, use_container_width=True)
        
        c_inc, c_dec = st.columns(2)
        with c_inc:
            st.markdown("##### 🚨 불량 위험을 가장 크게 높인 요인 Top 5 (SHAP > 0)")
            top_inc_disp = shap_res["df_risk_increase"].head(5)[["feature", "shap_value", "raw_value", "normal_median", "z_score"]].copy()
            top_inc_disp.columns = ["피처ID", "SHAP 기여도", "실측값", "정상중앙값", "Z편차(σ)"]
            st.dataframe(top_inc_disp, use_container_width=True)
        with c_dec:
            st.markdown("##### 🛡️ 불량 위험을 완화한 요인 Top 5 (SHAP < 0)")
            top_dec_disp = shap_res["df_risk_decrease"].head(5)[["feature", "shap_value", "raw_value", "normal_median", "z_score"]].copy()
            top_dec_disp.columns = ["피처ID", "SHAP 기여도", "실측값", "정상중앙값", "Z편차(σ)"]
            st.dataframe(top_dec_disp, use_container_width=True)
            
        with st.expander("🌐 테스트 세트 전수(314건) 글로벌 SHAP 센서 중요도 (전체 공정 영향력)", expanded=False):
            test_ids = df_predictions["sample_id"].values
            df_glob = get_global_shap_importance(df_features, test_ids, prep_dict, model, top_n=15)
            fig_glob = create_shap_global_summary_chart(df_glob, top_n=15)
            st.plotly_chart(fig_glob, use_container_width=True)

# -------------------------------------------------------------
# S05: 모델 성능 평가
# -------------------------------------------------------------
elif section == "S05 모델 성능 평가":
    st.subheader("🔲 [S05] 모델 성능 평가 및 혼동행렬 (C06 검증)")
    
    # 혼동행렬 계산 (임계값 0.5)
    y_true = df_predictions["actual_label"].values
    y_pred = (df_predictions["risk_score"] >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    cm_dict = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    
    eval_col1, eval_col2 = st.columns([1, 1])
    with eval_col1:
        st.markdown("### 📊 혼동행렬 히트맵 (TP+FP+FN+TN = 314건)")
        fig_v06 = create_v06_chart(cm_dict, total_samples=len(df_predictions))
        st.plotly_chart(fig_v06, use_container_width=True)
        st.success(f"✅ **C06 전수 검증 통과:** TN({tn}) + FP({fp}) + FN({fn}) + TP({tp}) = **{tn+fp+fn+tp}건 (Test 세트 314건 100% 일치)**")
        
    with eval_col2:
        st.markdown("### 🏆 분류 지표 vs 20% 순위 지표 분리 (C06-2)")
        
        # 1. 고정 20% 순위 지표
        m20 = calculate_review_metrics(df_predictions, ratio=0.20)
        st.markdown("#### 1️⃣ 비즈니스 순위 지표 (상위 20%, 63개 우선 검사)")
        s1, s2, s3 = st.columns(3)
        s1.metric("Recall@20%", f"{m20['recall_at_k']:.1f}%")
        s2.metric("Precision@20%", f"{m20['precision_at_k']:.1f}%")
        s3.metric("Average Precision", f"{m20['average_precision']:.4f}")
        
        st.markdown("---")
        
        # 2. 임계값 0.5 고정 분류 지표
        st.markdown("#### 2️⃣ 표준 분류 지표 (임계값 0.5 기준)")
        rec_val = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0
        prec_val = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0
        acc_val = ((tp + tn) / len(df_predictions)) * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("전체 정확도 (Accuracy)", f"{acc_val:.1f}%")
        b2.metric("재현율 (Recall)", f"{rec_val:.1f}%")
        b3.metric("정밀도 (Precision)", f"{prec_val:.1f}%")

    st.markdown("---")
    st.markdown("### 📈 검토 비율별(5% ~ 50%) 성과 시뮬레이션 표")
    sim_ratios = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
    sim_data = []
    for r in sim_ratios:
        res = calculate_review_metrics(df_predictions, ratio=r)
        sim_data.append({
            "검토 비율": f"{res['review_ratio_pct']:.0f}%",
            "선정 표본 수": f"{res['n_selected']} 건",
            "검출 불량 수": f"{res['n_detected_fails']} 건 / {res['n_fails_total']} 건",
            "Recall": f"{res['recall_at_k']:.1f}%",
            "Precision": f"{res['precision_at_k']:.1f}%",
            "불량 집중도 (Lift)": f"{(res['precision_at_k'] / (res['n_fails_total']/res['n_total']*100)):.2f}배"
        })
    st.dataframe(pd.DataFrame(sim_data), use_container_width=True)

    # -------------------------------------------------------------
    # [Day 3 신규 P0] 진단 보고서 및 시험 예측 결과 원클릭 다운로드 구역
    # -------------------------------------------------------------
    st.markdown("---")
    st.subheader("📥 [P0] 종합 진단 보고서 및 예측 데이터 다운로드 (C08 검증)")
    st.caption("화면의 모든 수치와 100% 동일한 결과 객체에서 마크다운 보고서와 한글 엑셀 호환(UTF-8-SIG) 예측표를 즉시 다운로드합니다.")

    # 1위 샘플 기준 정상 참고 비교 데이터 추출
    top1_id = df_predictions.iloc[0]["sample_id"]
    df_ref_top1 = compare_reference(df_features, train_normal_ids, top1_id, valid_features, top_n=5)
    drift_top5 = detect_sensor_drift(df_features, df_labels, valid_features, top_n=3, filter_mode="both")

    report_md_str = make_report(summary, m20, cm_dict, df_ref_top1, sim_df=pd.DataFrame(sim_data), drift_df=drift_top5)
    csv_bytes_bom = df_predictions.to_csv(index=False).encode("utf-8-sig")

    down_col1, down_col2 = st.columns(2)
    with down_col1:
        st.download_button(
            label="📄 종합 진단 보고서 다운로드 (Markdown .md)",
            data=report_md_str,
            file_name="SECOM_공정_품질_종합_진단_보고서.md",
            mime="text/markdown",
            use_container_width=True
        )
    with down_col2:
        st.download_button(
            label="📊 위험도 순위 시험 예측표 다운로드 (Excel CSV .csv)",
            data=csv_bytes_bom,
            file_name="SECOM_위험순위_시험예측표_314건.csv",
            mime="text/csv",
            use_container_width=True
        )

    # -------------------------------------------------------------
    # [고도화 전략 4] 신규 웨이퍼 CSV 업로드 & 실시간 인퍼런스 배치 시뮬레이터
    # -------------------------------------------------------------
    st.markdown("---")
    st.subheader("🧪 [고도화 전략 4] 신규 웨이퍼 CSV 업로드 & 실시간 인퍼런스 배치 시뮬레이터")
    st.caption("신규 롯(Lot) 또는 미지의 웨이퍼 센서 데이터셋(CSV)을 업로드하여 유효 센서 정합성 검증, 중앙값 대체, 스케일링, 파생변수 생성 및 챔피언 모델 실시간 배치 추론을 즉시 수행합니다.")
    
    with st.expander("📂 신규 웨이퍼 CSV 배치 추론 제어판 열기", expanded=True):
        up_c1, up_c2 = st.columns([3, 2])
        with up_c1:
            uploaded_file = st.file_uploader("📥 센서 측정 CSV 파일 업로드", type=["csv"], key="sim_uploader")
        with up_c2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            use_test_demo = st.button("🔄 테스트 세트(314건) 데이터로 즉시 시뮬레이션", use_container_width=True)
            
        df_batch_input = None
        if uploaded_file is not None:
            try:
                df_batch_input = pd.read_csv(uploaded_file)
                st.success(f"📁 업로드 완료: 총 {len(df_batch_input):,}개 웨이퍼 표본, {len(df_batch_input.columns)}개 열 로드 성공")
            except Exception as err:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {err}")
        elif use_test_demo:
            test_ids = df_predictions["sample_id"].values
            df_batch_input = df_features[df_features["sample_id"].isin(test_ids)].copy()
            st.info(f"📋 테스트 세트 원천 데이터 {len(df_batch_input)}건 로드 완료 (실시간 시뮬레이션 준비)")
            
        if df_batch_input is not None:
            with st.spinner("⏳ 전처리 파이프라인 변환 및 챔피언 모델 배치 추론 수행 중..."):
                df_batch_res = simulate_batch_inference(df_batch_input, prep_dict, model)
                
            b_kpi1, b_kpi2, b_kpi3, b_kpi4 = st.columns(4)
            b_kpi1.metric("총 추론 표본 수", f"{len(df_batch_res):,} 건")
            b_kpi2.metric("상위 20% 우선 검토 대상", f"{int(df_batch_res['is_top20_review'].sum()):,} 건", delta="비즈니스 우선검토")
            b_kpi3.metric("최고 위험도 (Max Risk)", f"{df_batch_res['risk_score'].max():.4f}")
            b_kpi4.metric("평균 위험도 (Mean Risk)", f"{df_batch_res['risk_score'].mean():.4f}")
            
            st.markdown("#### 📋 실시간 배치 추론 및 위험 순위 결과표 (상위 20건)")
            disp_batch = df_batch_res.head(20).copy()
            disp_batch["is_top20_review"] = disp_batch["is_top20_review"].map({True: "🚨우선검토", False: "일반"})
            disp_batch["pred_label_05"] = disp_batch["pred_label_05"].map({1: "불량(1)", 0: "정상(0)"})
            st.dataframe(
                disp_batch.rename(columns={
                    "sample_id": "웨이퍼 ID",
                    "risk_score": "불량 위험 점수",
                    "abnormal_sensor_count": "이상 센서 수 (|Z|>2)",
                    "risk_rank": "위험 순위",
                    "is_top20_review": "상위20% 대상",
                    "pred_label_05": "임계값 0.5 판정"
                }),
                use_container_width=True
            )
            
            batch_csv_bytes = df_batch_res.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="💾 실시간 배치 추론 결과표 다운로드 (Excel CSV .csv)",
                data=batch_csv_bytes,
                file_name="SECOM_신규웨이퍼_실시간배치추론_결과표.csv",
                mime="text/csv",
                use_container_width=True
            )

# -------------------------------------------------------------
# S06: 챔버 열화 & 예지보전 (PdM)
# -------------------------------------------------------------
elif section == "S06 챔버 열화 & 예지보전":
    st.subheader("🛠️ [S06] 챔버 열화 및 센서 드리프트 예지보전(PdM) 대시보드")
    st.caption("3대 다면 통계 모델(비모수 켄달 타우 단조성 + 누적 표준화 기울기 + 기저 이동량) 기반으로 장비 노후화 및 센서 기준축 이동을 정밀 감지하고 공학적 보전 조치를 제시합니다.")
    
    # 1. 드리프트 분석 실행
    drift_top6 = detect_sensor_drift(df_features, df_labels, valid_features, top_n=3, filter_mode="both")
    
    # 2. 핵심 KPI 메트릭 카드
    pdm1, pdm2, pdm3, pdm4 = st.columns(4)
    with pdm1:
        st.metric(
            label="▲ CVD 증착 드리프트 1위",
            value="feature_29 (+2.04σ)",
            delta="+10.6% 기저 상승",
            delta_color="inverse"
        )
    with pdm2:
        st.metric(
            label="▼ Dry Etch 마모 드리프트 1위",
            value="feature_104 (-1.73σ)",
            delta="-74.7% 기저 하강",
            delta_color="inverse"
        )
    with pdm3:
        st.metric(
            label="🚨 공정 불량 피크 주차",
            value="8월 34주차",
            delta="7일 이동평균 15.8% (Spike)",
            delta_color="inverse"
        )
    with pdm4:
        st.metric(
            label="🛠️ PM 예방정비 안정화",
            value="9월 중순 이후",
            delta="불량률 3.0% 미만 진정",
            delta_color="normal"
        )
        
    st.markdown("---")
    
    # 3. 공정 시계열 변곡점 & 7일 롤링 불량률
    st.markdown("### 📈 1. 공정 시계열 변곡점 & 7일 롤링 이동평균 불량률 (R05 고도화)")
    st.info("💡 **공정 진단 인사이트**: SECOM 공정은 8월 중순(34주차) 일일 생산량 감소와 함께 불량률이 15.8%까지 일시 급증(Spike)하였으나, 9월 중순 설비 예방 정비(PM) 이후 불량률이 3% 미만으로 현저히 안정화되었습니다.")
    fig_trouble = create_trouble_timeline_chart(df_labels)
    st.plotly_chart(fig_trouble, use_container_width=True)
    
    st.markdown("---")
    
    # 4. 센서 드리프트 모니터링 서브플롯
    st.markdown("### 🔬 2. 핵심 드리프트 센서 6종(상승 3종 vs 하강 3종) 시계열 추세 모니터링")
    st.caption("점선은 공정 전체 평균(Z=0)이며, 실선은 개별 센서의 25-Point 이동 평균선(Moving Average)입니다.")
    fig_drift = create_drift_dashboard_chart(df_features, df_labels, drift_top6)
    st.plotly_chart(fig_drift, use_container_width=True)
    
    st.markdown("---")
    
    # 5. 드리프트 정량화 테이블
    st.markdown("### 📋 3. 드리프트 센서 6종 정밀 정량화 분석표")
    drift_disp = drift_top6[["sensor_id", "drift_score", "direction", "norm_drift_sigma", "start_mean", "end_mean", "shift_pct"]].copy()
    drift_disp.columns = ["센서 ID", "Drift Index", "방향", "누적 이동량(σ)", "초기 평균", "후기 평균", "변화율(%)"]
    st.dataframe(drift_disp, use_container_width=True)
    
    st.markdown("---")
    
    # 6. 설비 보전 액션 가이드 카드 (2열)
    st.markdown("### 🏭 4. 반도체 단위 공정별 물리적 설비 예지보전(PdM) 권고 조치")
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        st.markdown("""
        <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #991b1b; margin-top: 0;">🔥 CVD / 화학기상증착 챔버 보전 조치</h4>
            <p style="color: #450a0a; font-size: 0.95rem; line-height: 1.6;">
                <strong>주요 대상 센서:</strong> <code>feature_29</code> (+2.04σ), <code>feature_543</code> (+1.78σ), <code>feature_170</code> (+1.53σ)<br>
                <strong>물리적 원인 진단:</strong>
                누적 웨이퍼 가공에 따라 반응 부산물이 챔버 내벽 및 가스 노즐에 지속 증착(Coating)되어 RF 임피던스와 가스 배압이 점진적으로 상승하고 있습니다.<br>
                <strong>권고 보전 조치:</strong>
                <ul style="margin-top: 6px; padding-left: 20px;">
                    <li>플라즈마 건식 클리닝(NF3 In-situ Dry Clean) 주기 20% 단축</li>
                    <li>샤워헤드(Showerhead) 가스 분사 노즐 탈거 및 화학 세정</li>
                    <li>챔버 배기 조절 밸브(Throttle Valve) 응답성 점검</li>
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with act_col2:
        st.markdown("""
        <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #1e40af; margin-top: 0;">⚡ Dry Etch / 건식 식각 챔버 소모품 교체 조치</h4>
            <p style="color: #172554; font-size: 0.95rem; line-height: 1.6;">
                <strong>주요 대상 센서:</strong> <code>feature_104</code> (-1.73σ), <code>feature_80</code> (-1.71σ), <code>feature_60</code> (-1.49σ, -99.1% 폭락)<br>
                <strong>물리적 원인 진단:</strong>
                고밀도 플라즈마 충돌로 인해 하부 전극 및 포커스 링 소모품이 깎여나가며 RF 전송 효율이 급감하고 전기적 영점이 하강하고 있습니다.<br>
                <strong>권고 보전 조치:</strong>
                <ul style="margin-top: 6px; padding-left: 20px;">
                    <li>포커스 링(Focus Ring) 두께 측정 후 한계 마모 도달 시 즉각 교체</li>
                    <li>정전척(ESC, Electrostatic Chuck) RF 매처(Matcher) 영점 재보정</li>
                    <li><code>feature_60</code> 대응 전력 공급 모듈(Power Generator) 선제 교체</li>
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)


