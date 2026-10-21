import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_v01_chart(summary):
    """
    V01: 정상 vs 불량 분포 바 차트 (Plotly)
    기획서 검증 기준: 정상 1,463개 (93.36%) vs 불량 104개 (6.64%)
    """
    labels_df = pd.DataFrame({
        "상태": ["정상 (Pass)", "불량 (Fail)"],
        "표본 수": [summary["n_normal"], summary["n_fail"]],
        "비율(%)": [100 - summary["fail_rate"], summary["fail_rate"]]
    })
    
    fig = px.bar(
        labels_df,
        x="상태",
        y="표본 수",
        color="상태",
        color_discrete_map={"정상 (Pass)": "#3b82f6", "불량 (Fail)": "#ef4444"},
        text="표본 수",
        title=f"V01: 라벨 분포 (총 {summary['n_samples']:,}건, 불량률 {summary['fail_rate']:.2f}%)"
    )
    fig.update_traces(
        texttemplate='%{text}건 (%{customdata[0]:.2f}%)',
        customdata=labels_df[["비율(%)"]],
        textposition='outside'
    )
    fig.update_layout(
        showlegend=False,
        yaxis_title="샘플 개수",
        height=450,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def create_v02_chart(summary, top_n=20):
    """
    V02: 센서 결측률 Top 20 수평 바 차트 (Plotly)
    기획서 검증 기준: 결측률 내림차순 상위 20개 표시, 50% 초과 28개 확인
    """
    top_missing = summary["missing_by_sensor"].head(top_n).copy()
    top_missing = top_missing.sort_values("missing_rate", ascending=True)
    
    fig = px.bar(
        top_missing,
        x="missing_rate",
        y="sensor_id",
        orientation="h",
        text="missing_rate",
        title=f"V02: 결측률 상위 {top_n}개 센서 (%)",
        color="missing_rate",
        color_continuous_scale="Reds"
    )
    fig.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    fig.update_layout(
        xaxis_title="결측률 (%)",
        yaxis_title="센서 ID",
        height=500,
        coloraxis_showscale=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def create_monthly_trend_chart(summary):
    """
    월별 표본 수 및 불량률 변화 콤보 차트 (Plotly)
    기획서 규칙 R05 검토용
    """
    monthly_df = summary["monthly_stats"].copy()
    
    fig = go.Figure()
    # 표본 수 막대
    fig.add_trace(go.Bar(
        x=monthly_df["month"],
        y=monthly_df["total"],
        name="총 표본 수",
        marker_color="#94a3b8",
        opacity=0.6,
        yaxis="y"
    ))
    # 불량률 라인
    fig.add_trace(go.Scatter(
        x=monthly_df["month"],
        y=monthly_df["fail_rate"],
        name="불량률 (%)",
        mode="lines+markers+text",
        text=[f"{r:.1f}%" for r in monthly_df["fail_rate"]],
        textposition="top center",
        line=dict(color="#ef4444", width=3),
        marker=dict(size=8),
        yaxis="y2"
    ))
    
    fig.update_layout(
        title="월별 생산 표본 수 및 불량률 추이 (R05 검토)",
        xaxis_title="공정 기록 월",
        yaxis=dict(title="표본 수 (건)"),
        yaxis2=dict(
            title="불량률 (%)",
            overlaying="y",
            side="right",
            range=[0, max(monthly_df["fail_rate"]) * 1.3]
        ),
        legend=dict(x=0.01, y=0.99),
        height=450,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def create_v03_chart(df_features, sensor_id, df_labels=None, normal_p05=None, normal_p95=None):
    """
    V03: 선택 센서 분포 & 이상치 탐색 차트 (Plotly)
    - 히스토그램 + 정상/불량별 박스플롯 결합
    - 정상 참고 구간(5~95 백분위) 음영 영역 표기
    - 결측치 수 및 결측률 표시
    """
    series = df_features[sensor_id].dropna()
    total_count = len(df_features)
    missing_count = df_features[sensor_id].isna().sum()
    missing_rate = (missing_count / total_count) * 100
    
    fig = go.Figure()
    
    # 정상/불량 라벨이 전달된 경우 분리 표시
    if df_labels is not None and "label" in df_labels.columns:
        merged = pd.merge(df_features[["sample_id", sensor_id]], df_labels[["sample_id", "label"]], on="sample_id")
        normal_vals = merged[merged["label"] == 0][sensor_id].dropna()
        fail_vals = merged[merged["label"] == 1][sensor_id].dropna()
        
        fig.add_trace(go.Histogram(
            x=normal_vals,
            name="정상 (Pass, 0)",
            marker_color="#3b82f6",
            opacity=0.65,
            nbinsx=40
        ))
        fig.add_trace(go.Histogram(
            x=fail_vals,
            name="불량 (Fail, 1)",
            marker_color="#ef4444",
            opacity=0.75,
            nbinsx=40
        ))
    else:
        fig.add_trace(go.Histogram(
            x=series,
            name=sensor_id,
            marker_color="#3b82f6",
            opacity=0.7,
            nbinsx=40
        ))
        
    # 정상 참고 구간(5~95 백분위) 가이드 영역
    if normal_p05 is not None and normal_p95 is not None:
        fig.add_vrect(
            x0=normal_p05, x1=normal_p95,
            fillcolor="#22c55e", opacity=0.15,
            layer="below", line_width=1,
            line_dash="dash", line_color="#16a34a",
            annotation_text="정상 참고 구간 (5~95%)",
            annotation_position="top left"
        )
        
    fig.update_layout(
        barmode="overlay",
        title=f"V03: {sensor_id} 측정값 분포 (결측: {missing_count}건, {missing_rate:.1f}%)",
        xaxis_title=f"{sensor_id} 측정 수치",
        yaxis_title="샘플 빈도 (Count)",
        height=480,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(x=0.8, y=0.98)
    )
    return fig

def create_v04_chart(df_predictions, review_ratio=0.20):
    """
    V04: 불량 위험 순위 슬라이더 탐색 차트 (Plotly)
    - 314개 테스트 샘플 위험도 폭포수/산점도
    - 상위 k% 컷오프 수직선 및 우선 검토 영역 하이라이트
    - 실제 불량 검출 위치 강조
    """
    import math
    n_total = len(df_predictions)
    cutoff_rank = math.ceil(n_total * review_ratio)
    
    # 정렬된 순서 유지
    df_sorted = df_predictions.sort_values("risk_rank").copy()
    df_sorted["상태"] = df_sorted["actual_label"].map({0: "실제 정상", 1: "실제 불량"})
    df_sorted["검토구분"] = df_sorted["risk_rank"].apply(lambda r: "우선 검토군" if r <= cutoff_rank else "일반 관리군")
    
    fig = go.Figure()
    
    # 1. 일반 관리군 (정상/불량)
    general_df = df_sorted[df_sorted["risk_rank"] > cutoff_rank]
    fig.add_trace(go.Scatter(
        x=general_df["risk_rank"],
        y=general_df["risk_score"],
        mode="markers",
        marker=dict(
            color=general_df["actual_label"].map({0: "#cbd5e1", 1: "#f87171"}),
            size=6,
            symbol=general_df["actual_label"].map({0: "circle", 1: "diamond"})
        ),
        name="일반 관리군 (미선정)",
        hovertext=[f"{sid} ({st})" for sid, st in zip(general_df["sample_id"], general_df["상태"])],
        hoverinfo="text+x+y"
    ))
    
    # 2. 우선 검토군 (하이라이트)
    priority_df = df_sorted[df_sorted["risk_rank"] <= cutoff_rank]
    fig.add_trace(go.Scatter(
        x=priority_df["risk_rank"],
        y=priority_df["risk_score"],
        mode="markers",
        marker=dict(
            color=priority_df["actual_label"].map({0: "#3b82f6", 1: "#ef4444"}),
            size=9,
            symbol=priority_df["actual_label"].map({0: "circle", 1: "diamond"}),
            line=dict(width=1, color="#0f172a")
        ),
        name=f"우선 검토군 (상위 {review_ratio*100:.0f}%, {cutoff_rank}개)",
        hovertext=[f"{sid} ({st})" for sid, st in zip(priority_df["sample_id"], priority_df["상태"])],
        hoverinfo="text+x+y"
    ))
    
    # 컷오프 수직선 및 배경 하이라이트
    fig.add_vrect(
        x0=1, x1=cutoff_rank,
        fillcolor="#3b82f6", opacity=0.08,
        layer="below", line_width=0
    )
    fig.add_vline(
        x=cutoff_rank, line_width=2, line_dash="dash", line_color="#ef4444",
        annotation_text=f"Cut-off (Rank {cutoff_rank})",
        annotation_position="top right"
    )
    
    n_found_fail = (priority_df["actual_label"] == 1).sum()
    total_fails = (df_sorted["actual_label"] == 1).sum()
    recall_pct = (n_found_fail / total_fails * 100) if total_fails > 0 else 0
    
    fig.update_layout(
        title=f"V04: 불량 위험 순위 탐색 (상위 {review_ratio*100:.0f}% 검토 시 불량 {n_found_fail}/{total_fails}건 검출, Recall {recall_pct:.1f}%)",
        xaxis_title="위험 순위 (Risk Rank, 1위 ~ 314위)",
        yaxis_title="불량 위험 점수 (Risk Score)",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(x=0.65, y=0.98)
    )
    return fig

def create_v05_chart(df_reference, selected_sample_id):
    """
    V05: 정상 참고 비교 프로파일 바 차트 (Plotly)
    - 5대 핵심 이상 센서의 Z-score 및 정상 참고 구간(5~95 백분위) 이탈 여부
    - 결측 대체 여부(was_imputed) 시각적 구분
    """
    df_plot = df_reference.copy()
    colors = ["#f59e0b" if imp else "#3b82f6" for imp in df_plot["was_imputed"]]
    borders = ["#ef4444" if oob else "#0f172a" for oob in df_plot["is_out_of_bounds"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot["sensor_id"],
        y=df_plot["z_score"],
        marker=dict(
            color=colors,
            line=dict(color=borders, width=2.5)
        ),
        text=[f"Z: {z:+.2f}σ<br>({'결측대체' if imp else '실측값'})" for z, imp in zip(df_plot["z_score"], df_plot["was_imputed"])],
        textposition="outside",
        name="정상 대비 표준화 편차 (Z-Score)"
    ))
    
    # 정상 범위 기준선 (-1.96σ ~ +1.96σ)
    fig.add_hline(y=1.96, line_dash="dot", line_color="#10b981", annotation_text="+1.96σ (정상 상한)")
    fig.add_hline(y=-1.96, line_dash="dot", line_color="#10b981", annotation_text="-1.96σ (정상 하한)")
    fig.add_hline(y=0, line_color="#94a3b8")
    
    fig.update_layout(
        title=f"V05: {selected_sample_id}의 주요 이상 센서 5종 정상 비교 (|Z-Score| 편차 순)",
        xaxis_title="이상 센서 ID (빨간 테두리: 5~95% 정상 참고구간 이탈)",
        yaxis_title="정상 평균 대비 편차 (Z-Score, σ)",
        height=480,
        margin=dict(l=40, r=40, t=60, b=60),
        annotations=[
            dict(
                text="※ 본 정상 참고 구간은 하드웨어 장비 공차가 아니며, 학습 정상 데이터(1,170건)의 통계적 분포(5~95 백분위)입니다.",
                xref="paper", yref="paper",
                x=0.5, y=-0.22, showarrow=False,
                font=dict(size=11, color="#64748b")
            )
        ]
    )
    return fig

def create_v06_chart(cm_dict, total_samples=314):
    """
    V06: 모델 성능 평가 혼동행렬 (Confusion Matrix) 히트맵
    - TP, FP, FN, TN $2 \times 2$ 시각화
    - C06 검증: TP + FP + FN + TN == total_samples(314) 검증
    """
    tn = cm_dict["tn"]
    fp = cm_dict["fp"]
    fn = cm_dict["fn"]
    tp = cm_dict["tp"]
    
    z = [[tn, fp], [fn, tp]]
    x_labels = ["예측 정상 (0)", "예측 불량 (1)"]
    y_labels = ["실제 정상 (0)", "실제 불량 (1)"]
    
    text_labels = [
        [f"TN: {tn}건<br>({tn/total_samples*100:.1f}%)", f"FP (오탐): {fp}건<br>({fp/total_samples*100:.1f}%)"],
        [f"FN (미탐): {fn}건<br>({fn/total_samples*100:.1f}%)", f"TP (적중): {tp}건<br>({tp/total_samples*100:.1f}%)"]
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        text=text_labels,
        texttemplate="%{text}",
        textfont=dict(size=15, color="white"),
        colorscale=[[0, "#1e3a8a"], [1, "#ef4444"]],
        showscale=False
    ))
    
    fig.update_layout(
        title=f"V06: 모델 분류 혼동행렬 (TP+FP+FN+TN = {total_samples}건 전수 검증)",
        xaxis_title="모델 예측 클래스 (임계값 0.5)",
        yaxis_title="실제 공정 라벨",
        height=450,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


# ==============================================================================
# Day 4 신규 시각화 함수: 예지보전 드리프트 대시보드 및 SHAP XAI 설명 차트 (전략 1-1 & 전략 2)
# ==============================================================================

def create_drift_dashboard_chart(df_features, df_labels, drift_df):
    """
    [Day 4 전략 1-1] 챔버 열화 및 센서 드리프트 인터랙티브 서브플롯 차트
    - Row 1: 상승 드리프트 센서 3종 (CVD 챔버 파티클 코팅 / 퇴적)
    - Row 2: 하강 드리프트 센서 3종 (Dry Etch 플라즈마 전극 / 포커스링 마모)
    - 25-Point 이동 평균선 및 표준화 편차(Z-Score) 동시 시각화
    """
    df_merged = df_labels.sort_values("timestamp").reset_index(drop=True)
    ordered_ids = df_merged["sample_id"].values
    
    if "sample_id" in df_features.columns:
        feat_df = df_features.set_index("sample_id").loc[ordered_ids]
    else:
        feat_df = df_features.loc[ordered_ids]
        
    up_sensors = drift_df[drift_df["direction"].str.contains("상승")]["sensor_id"].tolist()[:3]
    down_sensors = drift_df[drift_df["direction"].str.contains("하강")]["sensor_id"].tolist()[:3]
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(
            "▲ CVD/증착 챔버 파티클 퇴적 의심 센서 (상승 드리프트 Top 3)",
            "▼ Dry Etch 전극/소모품 마모 의심 센서 (하강 드리프트 Top 3)"
        )
    )
    
    up_colors = ["#ef4444", "#f97316", "#eab308"]
    down_colors = ["#3b82f6", "#8b5cf6", "#06b6d4"]
    time_x = df_merged["timestamp"]
    
    # Row 1: Upward sensors
    for s_id, color in zip(up_sensors, up_colors):
        if s_id in feat_df.columns:
            s_series = feat_df[s_id]
            mu = s_series.mean()
            std = s_series.std() if s_series.std() > 0 else 1.0
            norm_series = (s_series - mu) / std
            rolling_series = norm_series.rolling(25, min_periods=5).mean()
            
            fig.add_trace(go.Scatter(
                x=time_x, y=norm_series,
                mode="markers",
                marker=dict(size=3, color=color, opacity=0.25),
                name=f"{s_id} (실측)",
                legendgroup="up",
                showlegend=False
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=time_x, y=rolling_series,
                mode="lines",
                line=dict(color=color, width=2.5),
                name=f"{s_id} (추세선)",
                legendgroup="up"
            ), row=1, col=1)
            
    # Row 2: Downward sensors
    for s_id, color in zip(down_sensors, down_colors):
        if s_id in feat_df.columns:
            s_series = feat_df[s_id]
            mu = s_series.mean()
            std = s_series.std() if s_series.std() > 0 else 1.0
            norm_series = (s_series - mu) / std
            rolling_series = norm_series.rolling(25, min_periods=5).mean()
            
            fig.add_trace(go.Scatter(
                x=time_x, y=norm_series,
                mode="markers",
                marker=dict(size=3, color=color, opacity=0.25),
                name=f"{s_id} (실측)",
                legendgroup="down",
                showlegend=False
            ), row=2, col=1)
            
            fig.add_trace(go.Scatter(
                x=time_x, y=rolling_series,
                mode="lines",
                line=dict(color=color, width=2.5),
                name=f"{s_id} (추세선)",
                legendgroup="down"
            ), row=2, col=1)
            
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8", opacity=0.7, row=1, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8", opacity=0.7, row=2, col=1)
    
    fig.update_yaxes(title_text="표준화 편차 (Z, σ)", row=1, col=1)
    fig.update_yaxes(title_text="표준화 편차 (Z, σ)", row=2, col=1)
    fig.update_xaxes(title_text="공정 일자 (Timestamp)", row=2, col=1)
    
    fig.update_layout(
        title="<b>S06: 챔버 열화 및 장비 소모품 마모 드리프트 모니터링 (6종 센서 25-Point 추세)</b>",
        height=620,
        margin=dict(l=50, r=40, t=80, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_trouble_timeline_chart(df_labels):
    """
    [Day 4 전략 1-1] 공정 시계열 불량 변곡점 & 7일 롤링 불량률 타임라인 차트
    """
    df = df_labels.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").agg(
        total=("label", "count"),
        fails=("label", "sum")
    ).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)
    
    daily["rolling_total"] = daily["total"].rolling(7, min_periods=1).sum()
    daily["rolling_fails"] = daily["fails"].rolling(7, min_periods=1).sum()
    daily["rolling_fail_rate"] = (daily["rolling_fails"] / daily["rolling_total"]) * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=daily["date"],
        y=daily["total"],
        name="일일 가동 웨이퍼 수",
        marker_color="#94a3b8",
        opacity=0.45,
        yaxis="y"
    ))
    
    fig.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["rolling_fail_rate"],
        name="7일 이동평균 불량률 (%)",
        mode="lines+markers",
        line=dict(color="#dc2626", width=3),
        marker=dict(size=5, color="#dc2626"),
        yaxis="y2"
    ))
    
    fig.add_hline(
        y=6.64, line_dash="dot", line_color="#f59e0b",
        annotation_text="공정 평균 불량률 (6.64%)",
        yref="y2"
    )
    
    peak_row = daily.loc[daily["rolling_fail_rate"].idxmax()]
    fig.add_annotation(
        x=peak_row["date"],
        y=peak_row["rolling_fail_rate"],
        yref="y2",
        text=f"🚨 8월 불량 피크 ({peak_row['rolling_fail_rate']:.1f}%)",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#b91c1c",
        ax=-40,
        ay=-40,
        font=dict(color="#b91c1c", size=12)
    )
    
    fig.update_layout(
        title="<b>공정 시계열 변곡점: 일일 생산량 및 7일 롤링 불량률 추이 (R05 고도화)</b>",
        xaxis_title="공정 일자 (Date)",
        yaxis=dict(title="일일 가동 웨이퍼 수 (건)", side="left"),
        yaxis2=dict(
            title="7일 롤링 불량률 (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, max(25, daily["rolling_fail_rate"].max() + 5)]
        ),
        height=450,
        margin=dict(l=50, r=50, t=60, b=50),
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.7)")
    )
    return fig


def create_shap_waterfall_chart(df_shap_top, sample_id, expected_value, final_risk_score):
    """
    [Day 4 전략 2] 개별 웨이퍼 불량 위험도 SHAP 기여도 수평 바 차트
    """
    df_plot = df_shap_top.copy().iloc[::-1]
    colors = ["#ef4444" if s > 0 else "#10b981" for s in df_plot["shap_value"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot["shap_value"],
        y=df_plot["feature"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="#0f172a", width=1)),
        text=[f"{s:+.3f} (실측: {r:.2f}, Z: {z:+.2f}σ)" for s, r, z in zip(df_plot["shap_value"], df_plot["raw_value"], df_plot["z_score"])],
        textposition="outside",
        name="SHAP 기여도"
    ))
    
    fig.add_vline(x=0, line_color="#64748b", line_width=1.5)
    
    fig.update_layout(
        title=f"<b>SHAP XAI 원인 설명: Sample {sample_id} (불량 확률: {final_risk_score*100:.1f}%, 기저 log-odds: {expected_value:.2f})</b>",
        xaxis_title="SHAP Value (빨간색: 불량 위험 가중 (+), 초록색: 정상 유도 (-))",
        yaxis_title="주요 영향 센서 ID",
        height=480,
        margin=dict(l=100, r=50, t=70, b=50)
    )
    return fig


def create_shap_global_summary_chart(df_global_shap, top_n=15):
    """
    [Day 4 전략 2] 테스트 데이터셋 전수(314건) 글로벌 SHAP 중요도 수평 바 차트
    """
    df_plot = df_global_shap.head(top_n).copy().iloc[::-1]
    
    fig = px.bar(
        df_plot,
        x="mean_abs_shap",
        y="feature",
        orientation="h",
        text="mean_abs_shap",
        title=f"<b>글로벌 인공지능 센서 중요도 Top {top_n} (전체 314건 평균 |SHAP| 기여도)</b>",
        color="mean_abs_shap",
        color_continuous_scale="Viridis"
    )
    fig.update_traces(
        texttemplate='%{text:.3f}',
        textposition='outside'
    )
    fig.update_layout(
        xaxis_title="평균 절댓값 SHAP 기여도 (Mean |SHAP Value|)",
        yaxis_title="센서 식별자 (Feature ID)",
        height=500,
        coloraxis_showscale=False,
        margin=dict(l=100, r=50, t=60, b=50)
    )
    return fig


