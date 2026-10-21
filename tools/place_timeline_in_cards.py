import re
import os

index_path = r"web\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Define the reusable options HTML for the dropdown
options_html = """
              <option value="all" selected>🌐 전체 누적 전수 (총 814~1,714매 | 2008.07 ~ 2009.12)</option>
              <option value="year-2008">📅 2008년 연간 누적 (514매)</option>
              <option value="year-2009">📅 2009년 연간 누적 (300~1,200매)</option>
              <optgroup label="── 2008년 하반기 (초기 314건) ──">
                <option value="2008-07">2008년 07월 (16매 | 초기 램프업)</option>
                <option value="2008-08">2008년 08월 (99매 | 🚨 1차 피크 트러블)</option>
                <option value="2008-09">2008년 09월 (115매 | 🛠️ 1차 PM 안정화)</option>
                <option value="2008-10">2008년 10월 (84매 | ✅ 고수율 유지)</option>
              </optgroup>
              <optgroup label="── 2008.11 ~ 2009.03 (확장 500건) ──">
                <option value="2008-11">2008년 11월 (100매 | 기준선 가동)</option>
                <option value="2008-12">2008년 12월 (100매 | ⚠️ 칠러/배압 드리프트)</option>
                <option value="2009-01">2009년 01월 (100매 | 🚨 2차 피크 트러블)</option>
                <option value="2009-02">2009년 02월 (100매 | 🛠️ 2차 긴급 PM 회복)</option>
                <option value="2009-03">2009년 03월 (100매 | ✅ 2차 고수율 정상화)</option>
              </optgroup>
              <optgroup label="── 2009.04 ~ 2009.12 (시뮬레이션 900건) ──">
                <option value="2009-04">2009년 04월 (100매 | 봄철 램프업)</option>
                <option value="2009-05">2009년 05월 (100매 | ⚠️ RF 매처/서셉터 편차)</option>
                <option value="2009-06">2009년 06월 (100매 | 정상 가동)</option>
                <option value="2009-07">2009년 07월 (100매 | ⚠️ 칠러 냉각 효율 저하)</option>
                <option value="2009-08">2009년 08월 (100매 | 🚨 2차 하계 피크 트러블)</option>
                <option value="2009-09">2009년 09월 (100매 | 🛠️ 하계 오버홀 긴급 PM)</option>
                <option value="2009-10">2009년 10월 (100매 | ✅ 초고수율 양산 안정)</option>
                <option value="2009-11">2009년 11월 (100매 | 고수율 유지)</option>
                <option value="2009-12">2009년 12월 (100매 | 연말 안정 가동)</option>
              </optgroup>"""

# 2. Define the Card-Level Timeline Control Component
card_timeline_component = f"""
        <!-- Card-Level Timeline Control Bar (각 기능 카드 상단 임베디드) -->
        <div class="fab-card-timeline-bar" style="background:#ffffff; padding:12px 18px; border-radius:10px; border:1px solid #cbd5e1; box-shadow:0 1px 4px rgba(0,0,0,0.06); margin-bottom:18px; display:flex; flex-direction:column; gap:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
              <span style="font-size:0.86rem; font-weight:800; color:#0369a1; display:flex; align-items:center; gap:5px;">
                <span>🏭 공정 관제 대상 기간:</span>
              </span>
              <select class="unified-period-dropdown" onchange="setUnifiedGlobalPeriod(this.value)" style="padding:6px 14px; font-size:0.88rem; font-weight:700; border:1.5px solid #0284c7; border-radius:8px; background:#f8fafc; color:#0f172a; cursor:pointer; outline:none; box-shadow:0 1px 3px rgba(2,132,199,0.15);">{options_html}
              </select>
              <span class="card-timeline-badge brand-tag" style="background:#e0f2fe; color:#0369a1; font-weight:800; border:1px solid #bae6fd; font-size:0.8rem; padding:4px 10px;">
                🌐 전체 전수 누적 SSOT
              </span>
            </div>
            <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
              <span style="font-size:0.78rem; color:#64748b; font-weight:600;">📥 시뮬레이션 인제스트:</span>
              <button class="action-btn" onclick="ingestSimulationBatch('sim_200')" style="padding:4px 9px; font-size:0.78rem; font-weight:700; background:#f0f9ff; color:#0284c7; border:1px solid #bae6fd;" title="2009년 4~5월 200매 신규 배치 인제스트">
                <span>➕ 200건</span>
              </button>
              <button class="action-btn" onclick="ingestSimulationBatch('sim_300')" style="padding:4px 9px; font-size:0.78rem; font-weight:700; background:#f0f9ff; color:#0284c7; border:1px solid #bae6fd;" title="2009년 6~8월 300매 하계 배치 인제스트">
                <span>➕ 300건</span>
              </button>
              <button class="action-btn" onclick="ingestSimulationBatch('sim_400')" style="padding:4px 9px; font-size:0.78rem; font-weight:700; background:#f0f9ff; color:#0284c7; border:1px solid #bae6fd;" title="2009년 9~12월 400매 전수 배치 인제스트">
                <span>➕ 400건</span>
              </button>
              <button class="action-btn" onclick="resetToInitial814()" style="padding:4px 9px; font-size:0.78rem; font-weight:600; background:#f1f5f9; color:#64748b; border:1px solid #cbd5e1;" title="초기 기준 814매로 리셋">
                <span>🔄 리셋</span>
              </button>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:0.78rem; font-weight:700; color:#64748b; white-space:nowrap;">📅 월별 이동:</span>
            <div class="card-universal-month-pills" style="display:flex; gap:6px; overflow-x:auto; padding:2px 0; scrollbar-width:thin;">
              <!-- Rendered dynamically -->
            </div>
          </div>
        </div>
"""

# 3. Remove Header Timeline Select Wrapper (so Hub header is clean)
header_select_pattern = r'<div class="fab-timeline-select-wrapper"[\s\S]*?</div>\s*</div>'
if re.search(header_select_pattern, html):
    html = re.sub(header_select_pattern, '</div>', html, count=1)
    print("Removed fab-timeline-select-wrapper from header.")

# 4. Remove Global Bar #fab-global-timeline-bar (so Hub is not cluttered)
global_bar_pattern = r'<!-- =+[\s\r\n]*UNIVERSAL FAB TIMELINE[\s\S]*?<!-- =+[\s\r\n]*MAIN APPLICATION'
# Let's locate fab-global-timeline-bar accurately
bar_start = html.find('<div id="fab-global-timeline-bar"')
if bar_start != -1:
    bar_end = html.find('<!-- Main Container with Clean Screen Transition Architecture -->', bar_start)
    if bar_end != -1:
        html = html[:bar_start] + html[bar_end:]
        print("Removed #fab-global-timeline-bar from global position.")

# 5. Insert Card-Level Timeline Component inside every functional screen card
screens = [
    ("view-triage", r'(<div id="view-triage" class="view-screen">\s*<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-shap-summary", r'(<div id="view-shap-summary" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-pdm", r'(<div id="view-pdm" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-chat", r'(<div id="view-chat" class="view-screen">\s*<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-admin-yield", r'(<div id="view-admin-yield" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-admin-perf", r'(<div id="view-admin-perf" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-admin-confusion", r'(<div id="view-admin-confusion" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-admin-drift", r'(<div id="view-admin-drift" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-admin-simulation", r'(<div id="view-admin-simulation" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)'),
    ("view-admin-wiki", r'(<div id="view-admin-wiki" class="view-screen">[\s\S]*?<div class="nav-back-bar">[\s\S]*?</div>)')
]

for s_id, pattern in screens:
    match = re.search(pattern, html)
    if match:
        matched_str = match.group(1)
        replacement = matched_str + "\n" + card_timeline_component
        html = html.replace(matched_str, replacement, 1)
        print(f"Inserted card-level timeline component into {s_id}")
    else:
        print(f"Warning: pattern for {s_id} not matched!")

# 6. Add mini period selector to each Hub Card inside view-hub
hub_card_mini = f"""
                <div class="hub-card-period-box" onclick="event.stopPropagation();" style="margin-top:8px; display:flex; align-items:center; gap:6px; background:#f8fafc; padding:4px 8px; border-radius:6px; border:1px solid #e2e8f0;">
                  <span style="font-size:0.75rem; font-weight:700; color:#0369a1;">📅 관제 기간:</span>
                  <select class="unified-period-dropdown" onchange="setUnifiedGlobalPeriod(this.value); event.stopPropagation();" style="padding:2px 6px; font-size:0.75rem; font-weight:700; border:1px solid #cbd5e1; border-radius:4px; background:#fff; color:#0f172a; flex:1;">{options_html}
                  </select>
                </div>"""

# Insert hub_card_mini inside hub cards before <div class="hub-card-footer">
# We can search for <div class="hub-card-footer"> and insert before it
# To avoid multiple duplicate insertions, let's replace <div class="hub-card-footer"> inside #view-hub
hub_pos = html.find('id="view-hub"')
hub_end = html.find('id="view-triage"')
if hub_pos != -1 and hub_end != -1:
    hub_section = html[hub_pos:hub_end]
    hub_section_new = hub_section.replace('<div class="hub-card-footer">', hub_card_mini + '\n              <div class="hub-card-footer">')
    html = html[:hub_pos] + hub_section_new + html[hub_end:]
    print("Inserted mini period selector inside all Hub cards.")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Finished updating index.html with card-level timeline controls!")
