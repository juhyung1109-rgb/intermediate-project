import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

# 프로젝트 루트 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.analysis import summarize_data
from src.visualization import create_v01_chart, create_v02_chart, create_monthly_trend_chart

# 1. 데이터 로드 및 요약
features_path = os.path.join(base_dir, "data", "processed", "secom_features.csv")
labels_path = os.path.join(base_dir, "data", "processed", "secom_labels.csv")

if not (os.path.exists(features_path) and os.path.exists(labels_path)):
    from src.data_loader import prepare_secom_dataset
    df_features, df_labels = prepare_secom_dataset(base_dir)
else:
    df_features = pd.read_csv(features_path)
    df_labels = pd.read_csv(labels_path)
    df_labels["timestamp"] = pd.to_datetime(df_labels["timestamp"])

summary = summarize_data(df_features, df_labels)
picture_dir = os.path.join(base_dir, "picture")
os.makedirs(picture_dir, exist_ok=True)

# 2. 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.autolayout'] = False

# ==========================================
# [Chart 1] V01: 정상 vs 불량 클래스 불균형 차트
# ==========================================
fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
labels = ['정상 (Pass)', '불량 (Fail)']
counts = [summary['n_normal'], summary['n_fail']]
percentages = [100 - summary['fail_rate'], summary['fail_rate']]
colors = ['#2563EB', '#DC2626']

bars = ax.bar(labels, counts, color=colors, width=0.48, edgecolor='#0F172A', linewidth=1.2, zorder=3)

# 막대 위 수치 라벨링
for bar, count, pct in zip(bars, counts, percentages):
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height + 25,
        f'{count:,}건\n({pct:.2f}%)',
        ha='center', va='bottom', fontsize=12, fontweight='bold', color='#0F172A'
    )

ax.set_title('[V01] SECOM 공정 웨이퍼 정상 vs 불량 라벨 분포', fontsize=15, fontweight='bold', pad=22, color='#0F172A')
ax.set_ylabel('웨이퍼 표본 수 (건)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_ylim(0, 1750)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
ax.grid(axis='y', linestyle='--', alpha=0.4, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 인사이트 박스
ax.text(
    0.5, 0.72,
    "💡 [발표 핵심 인사이트 - 규칙 R03]\n"
    "• 전체 1,567건 중 불량률은 단 6.64% (극심한 불균형)\n"
    "• 단순 Accuracy(정확도) 대신 PR-AUC 및 Class Weight 필수",
    transform=ax.transAxes, ha='center', va='center',
    bbox=dict(boxstyle='round,pad=0.8', facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1.5),
    fontsize=10.5, color='#1E3A8A', fontweight='medium'
)

v01_png = os.path.join(picture_dir, "V01_클래스_불균형_분포.png")
plt.savefig(v01_png, bbox_inches='tight')
plt.close()
print(f"✅ 저장 완료: {v01_png}")

# ==========================================
# [Chart 2] V02: 결측률 상위 20개 센서 차트
# ==========================================
fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
top20 = summary['missing_by_sensor'].head(20).copy()
top20 = top20.sort_values('missing_rate', ascending=True)

# 결측률 50% 초과 여부에 따른 색상 분기
bar_colors = ['#DC2626' if rate > 50 else '#F97316' for rate in top20['missing_rate']]
bars = ax.barh(top20['sensor_id'], top20['missing_rate'], color=bar_colors, height=0.68, edgecolor='#334155', linewidth=0.8, zorder=3)

for bar in bars:
    width = bar.get_width()
    ax.text(
        width + 1.2, bar.get_y() + bar.get_height() / 2,
        f'{width:.1f}%',
        ha='left', va='center', fontsize=9.5, fontweight='bold', color='#0F172A'
    )

# 50% 기준선 강조
ax.axvline(x=50, color='#991B1B', linestyle='--', linewidth=1.8, zorder=4, label='50% 제거 임계 기준선')
ax.set_title('[V02] 결측률 상위 20개 공정 센서 현황 (품질 취약 센서)', fontsize=15, fontweight='bold', pad=20, color='#0F172A')
ax.set_xlabel('결측률 (Missing Rate, %)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_xlim(0, 105)
ax.grid(axis='x', linestyle='--', alpha=0.4, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='lower right', frameon=True, facecolor='#FEF2F2', edgecolor='#EF4444', fontsize=10)

# 인사이트 박스
ax.text(
    0.68, 0.40,
    "⚠️ [전처리 핵심 기준]\n"
    f"• 결측률 50% 초과 센서: 총 {summary['high_missing_count']}개 존재\n"
    "• 정보 왜곡 방지를 위해 Day 2에서 우선 Drop 제거\n"
    "• 나머지 결측치는 Train 중앙값(Median) 대입",
    transform=ax.transAxes, ha='left', va='center',
    bbox=dict(boxstyle='round,pad=0.7', facecolor='#FFFBEB', edgecolor='#F59E0B', linewidth=1.5),
    fontsize=10, color='#78350F'
)

v02_png = os.path.join(picture_dir, "V02_결측률_상위20개_센서.png")
plt.savefig(v02_png, bbox_inches='tight')
plt.close()
print(f"✅ 저장 완료: {v02_png}")

# ==========================================
# [Chart 3] R05: 월별 생산량 및 불량률 추이 콤보 차트
# ==========================================
fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
monthly_df = summary['monthly_stats'].copy()
x_indices = np.arange(len(monthly_df))
months = monthly_df['month'].tolist()

# 1. 생산량 바 차트 (왼쪽 Y축)
bar_width = 0.45
bars = ax1.bar(x_indices, monthly_df['total'], width=bar_width, color='#94A3B8', alpha=0.75, edgecolor='#475569', label='생산 웨이퍼 수 (건)', zorder=2)
ax1.set_xlabel('공정 기록 월 (Year-Month)', fontsize=12, fontweight='bold', labelpad=10)
ax1.set_ylabel('월별 생산 웨이퍼 수 (건)', fontsize=12, fontweight='bold', color='#475569', labelpad=10)
ax1.set_xticks(x_indices)
ax1.set_xticklabels(months, fontsize=11, fontweight='bold')
ax1.set_ylim(0, max(monthly_df['total']) * 1.3)
ax1.grid(axis='y', linestyle=':', alpha=0.4, zorder=0)

for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, height + 10, f'{int(height)}건', ha='center', va='bottom', fontsize=10, color='#334155', fontweight='bold')

# 2. 불량률 꺾은선 차트 (오른쪽 Y축)
ax2 = ax1.twinx()
line = ax2.plot(x_indices, monthly_df['fail_rate'], color='#DC2626', linewidth=2.8, marker='o', markersize=8, label='공정 불량률 (%)', zorder=5)
ax2.set_ylabel('공정 불량률 (%)', fontsize=12, fontweight='bold', color='#DC2626', labelpad=10)
ax2.set_ylim(0, max(monthly_df['fail_rate']) * 1.45)

for x, y in zip(x_indices, monthly_df['fail_rate']):
    ax2.text(x, y + 0.8, f'{y:.2f}%', ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='#DC2626')

# 통합 범례
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

ax1.set_title(f"[R05] 월별 생산 표본 수 및 불량률 변화 추이 (최대 편차: {summary['month_rate_diff']:.2f}%p)", fontsize=15, fontweight='bold', pad=20, color='#0F172A')

# 인사이트 박스
ax1.text(
    0.60, 0.85,
    "📈 [규칙 R05 충족]\n"
    f"• 월별 불량률 편차: {summary['month_rate_diff']:.2f}%p (5%p 이상 충족)\n"
    "• 2008년 7월 불량률 정점(14.29%) 후 점진적 안정화 추세\n"
    "• 공정 계절성/시간 피처 엔지니어링 활용 권장",
    transform=ax1.transAxes, ha='left', va='top',
    bbox=dict(boxstyle='round,pad=0.7', facecolor='#F0FDF4', edgecolor='#16A34A', linewidth=1.5),
    fontsize=9.5, color='#14532D'
)

r05_png = os.path.join(picture_dir, "R05_월별_생산량_및_불량률_추이.png")
plt.savefig(r05_png, bbox_inches='tight')
plt.close()
print(f"✅ 저장 완료: {r05_png}")

# ==========================================
# 3. Plotly 인터랙티브 HTML 파일 저장 (V01, V02, R05)
# ==========================================
fig_v01 = create_v01_chart(summary)
fig_v01.write_html(os.path.join(picture_dir, "V01_클래스_불균형_분포.html"))

fig_v02 = create_v02_chart(summary, top_n=20)
fig_v02.write_html(os.path.join(picture_dir, "V02_결측률_상위20개_센서.html"))

fig_r05 = create_monthly_trend_chart(summary)
fig_r05.write_html(os.path.join(picture_dir, "R05_월별_생산량_및_불량률_추이.html"))

# ==========================================
# 4. [Day 2 신규] V03, V04, V05, V06 차트 생성 및 저장
# ==========================================
from src.analysis import predict_risk, compare_reference
from src.visualization import create_v03_chart, create_v04_chart, create_v05_chart, create_v06_chart
from sklearn.metrics import confusion_matrix
import joblib

pred_csv_path = os.path.join(base_dir, "artifacts", "test_predictions.csv")
prep_joblib_path = os.path.join(base_dir, "artifacts", "preprocessor.joblib")
model_joblib_path = os.path.join(base_dir, "artifacts", "baseline_model.joblib")
train_idx_path = os.path.join(base_dir, "artifacts", "train_indices.csv")

if os.path.exists(pred_csv_path):
    df_pred = pd.read_csv(pred_csv_path)
else:
    df_test_idx = pd.read_csv(os.path.join(base_dir, "artifacts", "test_indices.csv"))
    df_pred = predict_risk(prep_joblib_path, model_joblib_path, df_features, df_test_idx)

prep_dict = joblib.load(prep_joblib_path)
valid_features = prep_dict["valid_features"]
df_train_idx = pd.read_csv(train_idx_path)
train_normal_ids = df_train_idx[df_train_idx["label"] == 0]["sample_id"].values

top1_sample_id = df_pred.iloc[0]["sample_id"]
df_ref_top1 = compare_reference(df_features, train_normal_ids, top1_sample_id, valid_features, top_n=5)
target_sensor = df_ref_top1.iloc[0]["sensor_id"]
p05_val = df_ref_top1.iloc[0]["normal_p05"]
p95_val = df_ref_top1.iloc[0]["normal_p95"]

# V03: 선택 센서 분포
fig_v03 = create_v03_chart(df_features, target_sensor, df_labels, p05_val, p95_val)
fig_v03.write_html(os.path.join(picture_dir, "V03_선택센서_분포.html"))

# V04: 위험 순위 슬라이더 탐색
fig_v04 = create_v04_chart(df_pred, review_ratio=0.20)
fig_v04.write_html(os.path.join(picture_dir, "V04_위험순위_탐색.html"))

# V05: 정상 참고 비교
fig_v05 = create_v05_chart(df_ref_top1, top1_sample_id)
fig_v05.write_html(os.path.join(picture_dir, "V05_정상참고_비교.html"))

# V06: 혼동행렬
y_true = df_pred["actual_label"].values
y_pred = (df_pred["risk_score"] >= 0.5).astype(int)
cm = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel()
cm_dict = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}

fig_v06 = create_v06_chart(cm_dict, total_samples=len(df_pred))
fig_v06.write_html(os.path.join(picture_dir, "V06_성능평가_혼동행렬.html"))

print("🎉 모든 6종 핵심 차트(V01~V06) 및 R05 인터랙티브 HTML 저장 완료!")

