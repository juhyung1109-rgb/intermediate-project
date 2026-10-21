import re

# 1. Update web/index.html
index_path = r"web\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

bar_html = """    <!-- ==============================================================
         UNIVERSAL FAB TIMELINE & DYNAMIC INGESTION CONTROL BAR
         (Persistently active across ALL screens for both Engineer & Admin)
         ============================================================== -->
    <div id="fab-global-timeline-bar" class="fab-global-control-bar" style="background:#0f172a; color:#ffffff; padding:10px 24px; border-bottom:1px solid #334155; box-shadow:0 4px 12px rgba(0,0,0,0.15); position:sticky; top:0; z-index:900;">
      <div style="max-width:1400px; margin:0 auto; display:flex; flex-direction:column; gap:8px;">
        <!-- Row 1: Aggregation Scope & Dynamic Ingestion Actions -->
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <!-- Left: Scope Selection (All Time, Year 2008, Year 2009) -->
          <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <span style="font-size:0.84rem; font-weight:800; color:#38bdf8; display:flex; align-items:center; gap:5px;">
              <span>🌐 관제 범위:</span>
            </span>
            <div class="scope-btn-group" style="display:flex; gap:4px; background:#1e293b; padding:3px; border-radius:8px; border:1px solid #475569;">
              <button class="scope-btn active" id="scope-btn-all" onclick="setUnifiedGlobalPeriod('all')" style="padding:4px 12px; font-size:0.82rem; font-weight:700; border-radius:6px; border:none; background:#0284c7; color:#ffffff; cursor:pointer;">
                전체 전수 누적 (<span id="bar-total-count">814</span>매)
              </button>
              <button class="scope-btn" id="scope-btn-2008" onclick="setUnifiedGlobalPeriod('year-2008')" style="padding:4px 12px; font-size:0.82rem; font-weight:700; border-radius:6px; border:none; background:transparent; color:#94a3b8; cursor:pointer;">
                2008년 누적 (514매)
              </button>
              <button class="scope-btn" id="scope-btn-2009" onclick="setUnifiedGlobalPeriod('year-2009')" style="padding:4px 12px; font-size:0.82rem; font-weight:700; border-radius:6px; border:none; background:transparent; color:#94a3b8; cursor:pointer;">
                2009년 누적 (<span id="bar-2009-count">300</span>매)
              </button>
            </div>
            <span id="bar-current-scope-badge" class="brand-tag" style="background:#0284c7; color:#ffffff; font-weight:800; border:none; font-size:0.8rem; padding:4px 10px;">
              🌐 전체 전수 누적 SSOT 활성
            </span>
          </div>

          <!-- Right: Live Simulation Data Ingestion -->
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <span style="font-size:0.82rem; color:#94a3b8; font-weight:600;">📥 시뮬레이션 즉시 누적 인제스트:</span>
            <button class="action-btn" id="btn-ingest-200" onclick="ingestSimulationBatch('sim_200')" style="background:#0284c7; color:#ffffff; border:none; padding:4px 10px; font-size:0.8rem; font-weight:700; border-radius:6px;" title="2009년 4~5월 200매 신규 배치 인제스트">
              <span>➕ 200건 인제스트 (1,014매)</span>
            </button>
            <button class="action-btn" id="btn-ingest-300" onclick="ingestSimulationBatch('sim_300')" style="background:#0284c7; color:#ffffff; border:none; padding:4px 10px; font-size:0.8rem; font-weight:700; border-radius:6px;" title="2009년 6~8월 300매 하계 배치 인제스트">
              <span>➕ 300건 인제스트 (1,314매)</span>
            </button>
            <button class="action-btn" id="btn-ingest-400" onclick="ingestSimulationBatch('sim_400')" style="background:#0284c7; color:#ffffff; border:none; padding:4px 10px; font-size:0.8rem; font-weight:700; border-radius:6px;" title="2009년 9~12월 400매 전수 배치 인제스트">
              <span>➕ 400건 인제스트 (1,714매)</span>
            </button>
            <button class="action-btn" onclick="resetToInitial814()" style="background:#475569; color:#cbd5e1; border:none; padding:4px 10px; font-size:0.8rem; font-weight:600; border-radius:6px;" title="초기 기준 814매로 리셋">
              <span>🔄 814매 리셋</span>
            </button>
          </div>
        </div>

        <!-- Row 2: Horizontal Scrollable Monthly Timeline Pills -->
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:0.8rem; font-weight:700; color:#cbd5e1; white-space:nowrap;">📅 월별 이동:</span>
          <div id="universal-month-pills" class="universal-month-pills" style="display:flex; gap:6px; overflow-x:auto; padding:2px 0; scrollbar-width:thin;">
            <!-- Populated dynamically by JS -->
          </div>
        </div>
      </div>
    </div>
"""

# Check if bar already inserted
if 'id="fab-global-timeline-bar"' not in html:
    header_end = '</header>'
    assert header_end in html, "header_end not found"
    html = html.replace(header_end, header_end + "\n" + bar_html, 1)

# Ensure data_cumulative_all.js is included in index.html
if 'data_cumulative_all.js' not in html:
    script_target = '<script src="data_unified814.js?v=20261019_v19"></script>'
    script_replacement = '<script src="data_unified814.js?v=20261019_v20"></script>\n  <script src="data_cumulative_all.js?v=20261019_v20"></script>'
    if script_target in html:
        html = html.replace(script_target, script_replacement, 1)
    else:
        # Fallback regex replace for any version of data_unified814.js
        html = re.sub(r'<script src="data_unified814\.js[^"]*"></script>', r'<script src="data_unified814.js?v=20261019_v20"></script>\n  <script src="data_cumulative_all.js?v=20261019_v20"></script>', html)

# Bump other script versions to v20
html = html.replace("app.js?v=20261019_v19", "app.js?v=20261019_v20")
html = html.replace("data.js?v=20261019_v19", "data.js?v=20261019_v20")
html = html.replace("data_batch500.js?v=20261019_v19", "data_batch500.js?v=20261019_v20")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Updated web/index.html with Universal Timeline Control Bar and data_cumulative_all.js!")
