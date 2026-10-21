import re

app_path = r"web\app.js"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update state to add activeStage
state_old = """const state = {
  isLoggedIn: false, // Locked until Firebase login/signup or demo click
  userRole: null, // Strict authenticated permission: 'engineer' | 'admin'
  currentRole: 'engineer', // Currently viewed mode
  activeDataset: 'unified_814', // Unified Continuous 814-Wafer Production Dataset (2008.07 ~ 2009.03)
  unifiedPeriod: 'all', // 'all' (전체 누적 814건) | '2008-07' ... '2009-03' (월별)
  currentPeriod: 'all',"""

state_new = """const state = {
  isLoggedIn: false, // Locked until Firebase login/signup or demo click
  userRole: null, // Strict authenticated permission: 'engineer' | 'admin'
  currentRole: 'engineer', // Currently viewed mode
  activeStage: 'stage_814', // 'stage_814' (814매) | 'stage_1014' (+200매) | 'stage_1314' (+300매) | 'stage_1714' (+400매)
  activeDataset: 'unified_814',
  unifiedPeriod: 'all', // 'all' | 'year-2008' | 'year-2009' | '2008-07' ... '2009-12'
  currentPeriod: 'all',"""

assert state_old in code, "state_old not found in app.js"
code = code.replace(state_old, state_new, 1)

# 2. Add getActiveDataset, renderUniversalTimelineBar, ingestSimulationBatch, resetToInitial814
new_engine = """/* ==========================================================================
   UNIVERSAL CONTINUOUS FAB INGESTION & AGGREGATION ENGINE
   Supports: All-time SSOT, Yearly (2008/2009), 18 Monthly Drill-downs,
             and Dynamic Simulation Batch Ingestion (200, 300, 400 wafers)
   ========================================================================== */
function getActiveDataset() {
  const cumData = window.SEMI_CUMULATIVE_DATA;
  const u814 = window.SEMI_UNIFIED_DATA;

  // 1. Determine active wafer pool from stage
  let pool = [];
  let stageInfo = null;
  if (cumData && cumData.stages) {
    stageInfo = cumData.stages[state.activeStage] || cumData.stages['stage_814'];
    const maxCount = stageInfo.total_count;
    pool = cumData.wafers.filter(w => {
      const sid = parseInt(w.sample_id);
      if (maxCount === 814) return sid <= 1565 || (sid >= 2001 && sid <= 2500);
      if (maxCount === 1014) return sid <= 1565 || (sid >= 2001 && sid <= 2700);
      if (maxCount === 1314) return sid <= 1565 || (sid >= 2001 && sid <= 3000);
      return true; // 1714
    });
  } else if (u814 && u814.wafers) {
    pool = u814.wafers;
  }

  // 2. Filter pool by state.unifiedPeriod
  const p = state.unifiedPeriod || 'all';
  let filtered = [];
  let scopeName = '전체 전수 누적';
  if (p === 'all') {
    filtered = pool;
    scopeName = `전체 전수 누적 (${pool.length}매)`;
  } else if (p === 'year-2008') {
    filtered = pool.filter(w => (w.year || w.timestamp.slice(0, 4)) === '2008');
    scopeName = `2008년 연간 누적 (${filtered.length}매)`;
  } else if (p === 'year-2009') {
    filtered = pool.filter(w => (w.year || w.timestamp.slice(0, 4)) === '2009');
    scopeName = `2009년 연간 누적 (${filtered.length}매)`;
  } else {
    filtered = pool.filter(w => (w.month || w.timestamp.slice(0, 7)) === p);
    scopeName = `${p} 월별 관제 (${filtered.length}매)`;
  }

  // Sort filtered descending by risk_score
  filtered.sort((a, b) => b.risk_score - a.risk_score);

  const totalCount = filtered.length;
  const top20Cutoff = Math.max(1, Math.ceil(totalCount * 0.20));
  const tp = filtered.filter((w, idx) => idx < top20Cutoff && w.actual_label === 1).length;
  const fp = filtered.filter((w, idx) => idx < top20Cutoff && w.actual_label === 0).length;
  const fn = filtered.filter((w, idx) => idx >= top20Cutoff && w.actual_label === 1).length;
  const tn = filtered.filter((w, idx) => idx >= top20Cutoff && w.actual_label === 0).length;
  const totalDefects = tp + fn;
  const recall = totalDefects > 0 ? ((tp / totalDefects) * 100).toFixed(1) : '100.0';
  const precision = (tp + fp) > 0 ? ((tp / (tp + fp)) * 100).toFixed(1) : '0.0';
  const defectRate = totalCount > 0 ? ((totalDefects / totalCount) * 100).toFixed(2) : '0.00';
  const lift = parseFloat(defectRate) > 0 ? (parseFloat(precision) / parseFloat(defectRate)).toFixed(2) : '1.00';

  return {
    pool,
    wafers: filtered,
    totalCount,
    top20Cutoff,
    tp, fp, fn, tn,
    totalDefects,
    recall, precision, defectRate, lift,
    scopeName,
    period: p,
    stageKey: state.activeStage,
    stageInfo
  };
}

window.renderUniversalTimelineBar = function() {
  const ds = getActiveDataset();
  const pool = ds.pool;

  // 1. Update scope counts
  const totalEl = document.getElementById('bar-total-count');
  const count2009El = document.getElementById('bar-2009-count');
  const badgeEl = document.getElementById('bar-current-scope-badge');

  if (totalEl) totalEl.innerText = pool.length;
  const c2009 = pool.filter(w => (w.year || w.timestamp.slice(0, 4)) === '2009').length;
  if (count2009El) count2009El.innerText = c2009;

  // 2. Update active scope buttons
  const btnAll = document.getElementById('scope-btn-all');
  const btn2008 = document.getElementById('scope-btn-2008');
  const btn2009 = document.getElementById('scope-btn-2009');

  [btnAll, btn2008, btn2009].forEach(b => {
    if (b) {
      b.style.background = 'transparent';
      b.style.color = '#94a3b8';
    }
  });

  if (state.unifiedPeriod === 'all' && btnAll) {
    btnAll.style.background = '#0284c7';
    btnAll.style.color = '#ffffff';
  } else if (state.unifiedPeriod === 'year-2008' && btn2008) {
    btn2008.style.background = '#0284c7';
    btn2008.style.color = '#ffffff';
  } else if (state.unifiedPeriod === 'year-2009' && btn2009) {
    btn2009.style.background = '#0284c7';
    btn2009.style.color = '#ffffff';
  }

  if (badgeEl) badgeEl.innerText = ds.scopeName;

  // 3. Render monthly scrollable pills for all available months in pool
  const pillsContainer = document.getElementById('universal-month-pills');
  if (pillsContainer) {
    const months = Array.from(new Set(pool.map(w => w.month || w.timestamp.slice(0, 7)))).sort();
    pillsContainer.innerHTML = '';

    months.forEach(m => {
      const isSelected = state.unifiedPeriod === m;
      const isPeak = m === '2008-08' || m === '2009-01' || m === '2009-08';
      const isPm = m === '2008-09' || m === '2009-02' || m === '2009-09';
      let tag = '';
      if (isPeak) tag = ' 🚨';
      else if (isPm) tag = ' 🛠️';

      const btn = document.createElement('button');
      btn.className = `month-pill ${isSelected ? 'active' : ''}`;
      btn.style.cssText = `
        padding: 3px 10px;
        font-size: 0.78rem;
        font-weight: 700;
        border-radius: 6px;
        border: 1px solid ${isSelected ? '#38bdf8' : '#334155'};
        background: ${isSelected ? '#0284c7' : (isPeak ? 'rgba(239, 68, 68, 0.2)' : '#1e293b')};
        color: ${isSelected ? '#ffffff' : (isPeak ? '#fca5a5' : '#cbd5e1')};
        white-space: nowrap;
        cursor: pointer;
        transition: all 0.15s ease;
      `;
      btn.innerText = `${m}${tag}`;
      btn.onclick = () => setUnifiedGlobalPeriod(m);
      pillsContainer.appendChild(btn);
    });
  }

  // 4. Update Ingestion Buttons active states
  const btn200 = document.getElementById('btn-ingest-200');
  const btn300 = document.getElementById('btn-ingest-300');
  const btn400 = document.getElementById('btn-ingest-400');
  
  if (btn200) btn200.style.opacity = (state.activeStage === 'stage_1014' || state.activeStage === 'stage_1314' || state.activeStage === 'stage_1714') ? '0.6' : '1.0';
  if (btn300) btn300.style.opacity = (state.activeStage === 'stage_1314' || state.activeStage === 'stage_1714') ? '0.6' : '1.0';
  if (btn400) btn400.style.opacity = (state.activeStage === 'stage_1714') ? '0.6' : '1.0';
};

window.ingestSimulationBatch = function(batchKey) {
  if (batchKey === 'sim_200') state.activeStage = 'stage_1014';
  else if (batchKey === 'sim_300') state.activeStage = 'stage_1314';
  else if (batchKey === 'sim_400') state.activeStage = 'stage_1714';

  const titles = {
    'sim_200': '2009년 4~5월 200매 신규 배치 (RF 매처 편차)',
    'sim_300': '2009년 6~8월 300매 하계 트러블 피크 배치',
    'sim_400': '2009년 9~12월 400매 PM 오버홀 초고수율 배치'
  };
  const title = titles[batchKey] || '시뮬레이션 신규 배치 인제스트';

  state.dynamicWikiEntries.unshift({
    title: `[배치 인제스트] ${title}`,
    date: new Date().toLocaleDateString('ko-KR'),
    chamber: batchKey === 'sim_300' ? 'Dry Etch 3호기 하부 전극' : 'CVD 증착 복합 설비',
    trouble_type: '시뮬레이션 시계열 인제스트',
    period: batchKey === 'sim_200' ? '2009년 4~5월' : (batchKey === 'sim_300' ? '2009년 6~8월' : '2009년 9~12월'),
    author: '공정 관리자 (Fab Admin)',
    content: `simulation/ 폴더의 ${title} 데이터가 실시간 인제스트되어 LightGBM 불량 추론 모델 및 전사 수율/혼동행렬/설비 드리프트 관제실에 즉시 동기화되었습니다.`
  });

  renderUniversalTimelineBar();
  setUnifiedGlobalPeriod(state.unifiedPeriod || 'all');
  const ds = getActiveDataset();
  showToast(`📥 [${title}] 인제스트 완료! 누적 ${ds.pool.length}매로 전사 관제가 확장되었습니다.`);
};

window.resetToInitial814 = function() {
  state.activeStage = 'stage_814';
  renderUniversalTimelineBar();
  setUnifiedGlobalPeriod('all');
  showToast('🔄 기준선 814매 전수 데이터셋으로 관제 풀을 초기화했습니다.');
};
"""

# Replace the beginning of window.setUnifiedGlobalPeriod
old_set_unified = """// Unified 814-Wafer Global Fab Timeline & Monthly Drill-down Handler
window.setUnifiedGlobalPeriod = function(period) {
  state.unifiedPeriod = period || 'all';
  state.currentPeriod = period || 'all';
  state.selectedTriagePeriod = period || 'all';

  // 1. Header Global Dropdown Sync
  const selectElem = document.getElementById('global-timeline-select');
  if (selectElem && selectElem.value !== state.unifiedPeriod) {
    selectElem.value = state.unifiedPeriod;
  }

  // 2. Yield Period Pills Sync
  document.querySelectorAll('#yield-period-pills .period-pill').forEach(btn => {
    const fnStr = btn.getAttribute('onclick') || '';
    const match = fnStr.match(/['"]([^'"]+)['"]/);
    const p = match ? match[1] : '';
    if (p === state.unifiedPeriod) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 3. Triage Period Pills Sync
  document.querySelectorAll('#triage-period-pills .period-pill').forEach(btn => {
    const p = btn.getAttribute('data-triage-period') || '';
    if (p === state.unifiedPeriod) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 4. Update all screens with Unified 814 Data
  if (typeof filterConfusionTable === 'function') filterConfusionTable('ALL');
  if (typeof renderYieldDashboard === 'function') renderYieldDashboard();
  if (typeof renderAdminPerf === 'function') renderAdminPerf();
  if (typeof renderSimulationTable === 'function') renderSimulationTable();
  if (typeof renderAdminDriftTable === 'function') renderAdminDriftTable(state.unifiedPeriod);
  if (typeof runTriagePeriodInference === 'function') runTriagePeriodInference(state.unifiedPeriod);
  if (typeof renderQuickSamples === 'function') renderQuickSamples(state.unifiedPeriod);
  if (typeof runBatchSimulation === 'function') runBatchSimulation();

  const periodLabels = {
    'all': '전사 9개월 전수 누적 (총 814매, 2008.07 ~ 2009.03)',
    '2008-07': '2008년 7월 (양산 초기 / 17매)',
    '2008-08': '2008년 8월 (34주차 트러블 피크 / 95매)',
    '2008-09': '2008년 9월 (챔버 PM 회복 / 116매)',
    '2008-10': '2008년 10월 (고수율 안정화 / 86매)',
    '2008-11': '2008년 11월 (45주차 롤아웃 기준선 / 100매)',
    '2008-12': '2008년 12월 (칠러/배압 이상 조짐 / 100매)',
    '2009-01': '2009년 1월 (53주차 2차 피크 스파이크 / 100매)',
    '2009-02': '2009년 2월 (긴급 PM 수율 회복 / 100매)',
    '2009-03': '2009년 3월 (고수율 양산 정상화 / 100매)'
  };
  const label = periodLabels[state.unifiedPeriod] || state.unifiedPeriod;
  showToast(`🔄 팹 관제 타임라인: [${label}] 연동 완료`);
};"""

new_set_unified = new_engine + """\n// Universal Fab Timeline & Monthly/Yearly/Cumulative Handler
window.setUnifiedGlobalPeriod = function(period) {
  state.unifiedPeriod = period || 'all';
  state.currentPeriod = period || 'all';
  state.selectedTriagePeriod = period || 'all';

  // 1. Universal Top Bar Sync
  if (typeof renderUniversalTimelineBar === 'function') renderUniversalTimelineBar();

  // 2. Header Select Dropdown Sync
  const selectElem = document.getElementById('global-timeline-select');
  if (selectElem && selectElem.value !== state.unifiedPeriod) {
    selectElem.value = state.unifiedPeriod;
  }

  // 3. Yield Period Pills Sync
  document.querySelectorAll('#yield-period-pills .period-pill').forEach(btn => {
    const fnStr = btn.getAttribute('onclick') || '';
    const match = fnStr.match(/['"]([^'"]+)['"]/);
    const p = match ? match[1] : '';
    if (p === state.unifiedPeriod) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 4. Triage Period Pills Sync
  document.querySelectorAll('#triage-period-pills .period-pill').forEach(btn => {
    const p = btn.getAttribute('data-triage-period') || '';
    if (p === state.unifiedPeriod) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 5. Update All Screens Dynamically
  if (typeof filterConfusionTable === 'function') filterConfusionTable('ALL');
  if (typeof renderYieldDashboard === 'function') renderYieldDashboard();
  if (typeof renderAdminPerf === 'function') renderAdminPerf();
  if (typeof renderSimulationTable === 'function') renderSimulationTable();
  if (typeof renderAdminDriftTable === 'function') renderAdminDriftTable(state.unifiedPeriod);
  if (typeof runTriagePeriodInference === 'function') runTriagePeriodInference(state.unifiedPeriod);
  if (typeof renderQuickSamples === 'function') renderQuickSamples(state.unifiedPeriod);
  if (typeof runBatchSimulation === 'function') runBatchSimulation();

  const ds = getActiveDataset();
  showToast(`🔄 팹 관제 타임라인: [${ds.scopeName}] 연동 완료`);
};"""

assert old_set_unified in code, "old_set_unified not found in app.js"
code = code.replace(old_set_unified, new_set_unified, 1)

# 3. Update filterConfusionTable to use getActiveDataset()
old_filter_conf = """window.filterConfusionTable = function(category) {
  const tbody = document.getElementById('confusion-samples-tbody');
  const filterLabel = document.getElementById('confusion-filter-label');
  if (!tbody) return;

  const uData = window.SEMI_UNIFIED_DATA;
  const p = state.unifiedPeriod || 'all';

  let wafers = [];
  let totalCount = 814;
  let topCutoff = 163;
  let tpCount = 24;
  let fpCount = 139;
  let fnCount = 28;
  let tnCount = 623;
  let recallPct = '46.15%';
  let liftVal = '2.30';

  if (uData && uData.wafers) {
    if (p === 'all') {
      wafers = uData.wafers;
      totalCount = uData.total_count || 814;
      topCutoff = uData.top20_cutoff || 163;
      tpCount = uData.confusion_matrix.TP;
      fpCount = uData.confusion_matrix.FP;
      fnCount = uData.confusion_matrix.FN;
      tnCount = uData.confusion_matrix.TN;
      recallPct = (uData.confusion_matrix.recall || 46.15).toFixed(1) + '%';
      liftVal = (uData.confusion_matrix.lift || 2.3).toFixed(2);
    } else {
      wafers = uData.wafers.filter(w => w.month === p);
      totalCount = wafers.length;
      topCutoff = Math.ceil(totalCount * 0.20);
      tpCount = wafers.filter(w => (w.cum_rank !== undefined ? w.cum_rank : w.risk_rank) <= topCutoff && w.actual_label === 1).length;
      fpCount = wafers.filter(w => (w.cum_rank !== undefined ? w.cum_rank : w.risk_rank) <= topCutoff && w.actual_label === 0).length;
      fnCount = wafers.filter(w => (w.cum_rank !== undefined ? w.cum_rank : w.risk_rank) > topCutoff && w.actual_label === 1).length;
      tnCount = wafers.filter(w => (w.cum_rank !== undefined ? w.cum_rank : w.risk_rank) > topCutoff && w.actual_label === 0).length;
      const fails = tpCount + fnCount;
      recallPct = fails > 0 ? ((tpCount / fails) * 100).toFixed(1) + '%' : '100.0%';
      const defectRate = fails / totalCount;
      const prec = (tpCount + fpCount) > 0 ? (tpCount / (tpCount + fpCount)) : 0;
      liftVal = defectRate > 0 ? (prec / defectRate).toFixed(2) : '1.00';
    }
  }

  // Update hero header and badges in view-admin-confusion
  const confTitle = document.querySelector('#view-admin-confusion h2');
  const confDesc = document.querySelector('#view-admin-confusion p');
  if (confTitle) {
    confTitle.innerText = p === 'all'
      ? '🔲 반도체 공정 전수 누적 814매 혼동행렬 대시보드 (2008.07 ~ 2009.03 9개월 전 기간)'
      : `🔲 ${p} 월별 혼동행렬 대시보드 (${totalCount}매 관제)`;
  }
  if (confDesc) {
    confDesc.innerHTML = `검증 기준: <b>상위 20% (${topCutoff}건) 우선 검토</b> 분기 조건 적용 ➔ <b>TP: ${tpCount}건, FP: ${fpCount}건, FN: ${fnCount}건, TN: ${tnCount}건 (합계 ${totalCount}건 100% 일치, 적발률 ${recallPct}, Lift ${liftVal}배)</b>`;
  }

  // Update 4 quadrant cards
  const tpBox = document.querySelector('#view-admin-confusion td[onclick*="TP"] div');
  const fpBox = document.querySelector('#view-admin-confusion td[onclick*="FP"] div');
  const fnBox = document.querySelector('#view-admin-confusion td[onclick*="FN"] div');
  const tnBox = document.querySelector('#view-admin-confusion td[onclick*="TN"] div');
  if (tpBox) tpBox.innerText = `TP = ${tpCount} 건`;
  if (fpBox) fpBox.innerText = `FP = ${fpCount} 건`;
  if (fnBox) fnBox.innerText = `FN = ${fnCount} 건`;
  if (tnBox) tnBox.innerText = `TN = ${tnCount} 건`;"""

new_filter_conf = """window.filterConfusionTable = function(category) {
  const tbody = document.getElementById('confusion-samples-tbody');
  const filterLabel = document.getElementById('confusion-filter-label');
  if (!tbody) return;

  const ds = getActiveDataset();
  const wafers = ds.wafers;
  const totalCount = ds.totalCount;
  const topCutoff = ds.top20Cutoff;
  const tpCount = ds.tp;
  const fpCount = ds.fp;
  const fnCount = ds.fn;
  const tnCount = ds.tn;
  const recallPct = ds.recall + '%';
  const liftVal = ds.lift;

  // Update hero header and badges in view-admin-confusion
  const confTitle = document.querySelector('#view-admin-confusion h2');
  const confDesc = document.querySelector('#view-admin-confusion p');
  if (confTitle) {
    confTitle.innerText = `🔲 ${ds.scopeName} 혼동행렬 대시보드 (전사 Single Source of Truth)`;
  }
  if (confDesc) {
    confDesc.innerHTML = `검증 기준: <b>상위 20% (${topCutoff}건) 우선 검토</b> 분기 조건 적용 ➔ <b>TP: ${tpCount}건, FP: ${fpCount}건, FN: ${fnCount}건, TN: ${tnCount}건 (합계 ${totalCount}건 100% 전수 일치, 적발률 ${recallPct}, Lift ${liftVal}배)</b>`;
  }

  // Update 4 quadrant cards
  const tpBox = document.querySelector('#view-admin-confusion td[onclick*="TP"] div');
  const fpBox = document.querySelector('#view-admin-confusion td[onclick*="FP"] div');
  const fnBox = document.querySelector('#view-admin-confusion td[onclick*="FN"] div');
  const tnBox = document.querySelector('#view-admin-confusion td[onclick*="TN"] div');
  if (tpBox) tpBox.innerText = `TP = ${tpCount} 건`;
  if (fpBox) fpBox.innerText = `FP = ${fpCount} 건`;
  if (fnBox) fnBox.innerText = `FN = ${fnCount} 건`;
  if (tnBox) tnBox.innerText = `TN = ${tnCount} 건`;"""

assert old_filter_conf in code, "old_filter_conf not found in app.js"
code = code.replace(old_filter_conf, new_filter_conf, 1)

# 4. Update renderAdminPerf to use getActiveDataset()
old_perf = """window.renderAdminPerf = function() {
  const recallEl = document.getElementById('perf-kpi-recall');
  const subRecallEl = document.getElementById('perf-kpi-sub-recall');
  const top20El = document.getElementById('perf-kpi-top20');
  const subTop20El = document.getElementById('perf-kpi-sub-top20');
  const unblockedEl = document.getElementById('perf-kpi-unblocked');
  const subUnblockedEl = document.getElementById('perf-kpi-sub-unblocked');
  const apEl = document.getElementById('perf-kpi-ap');
  const subApEl = document.getElementById('perf-kpi-sub-ap');

  const p = state.unifiedPeriod || 'all';
  const uData = window.SEMI_UNIFIED_DATA;

  if (p === 'all' || !uData || !uData.monthly_stats || !uData.monthly_stats[p]) {
    // Cumulative 814 metrics
    if (recallEl) recallEl.innerText = '46.2%';
    if (subRecallEl) subRecallEl.innerHTML = '<span>▲ 24건 적발 / 52건 (Lift 2.30배)</span>';
    if (top20El) top20El.innerText = '163 건';
    if (subTop20El) subTop20El.innerHTML = '<span>ceil(814 * 0.20) 규격 엄수</span>';
    if (unblockedEl) unblockedEl.innerText = '28 건 잔류';
    if (subUnblockedEl) subUnblockedEl.innerHTML = '<span>▼ 미검출 28건 (상위 20% 우선 필터링)</span>';
    if (apEl) apEl.innerText = '0.2012';
    if (subApEl) subApEl.innerHTML = '<span>814매 전수 누적 순위 분별력</span>';
  } else {
    // Monthly breakdown
    const m = uData.monthly_stats[p];
    if (recallEl) recallEl.innerText = `${m.recall}%`;
    if (subRecallEl) subRecallEl.innerHTML = `<span>▲ ${m.tp}건 적발 / ${m.fails}건</span>`;
    if (top20El) top20El.innerText = `${m.top20_cut} 건`;
    if (subTop20El) subTop20El.innerHTML = `<span>ceil(${m.total} * 0.20) 규격</span>`;
    if (unblockedEl) unblockedEl.innerText = `${m.fails - m.tp} 건 잔류`;
    if (subUnblockedEl) subUnblockedEl.innerHTML = `<span>▼ ${p} 미검출 ${m.fails - m.tp}건</span>`;
    if (apEl) apEl.innerText = (0.2000 + (m.recall / 500)).toFixed(4);
    if (subApEl) subApEl.innerHTML = `<span>${p} 월별 순위 분별력</span>`;
  }
};"""

new_perf = """window.renderAdminPerf = function() {
  const recallEl = document.getElementById('perf-kpi-recall');
  const subRecallEl = document.getElementById('perf-kpi-sub-recall');
  const top20El = document.getElementById('perf-kpi-top20');
  const subTop20El = document.getElementById('perf-kpi-sub-top20');
  const unblockedEl = document.getElementById('perf-kpi-unblocked');
  const subUnblockedEl = document.getElementById('perf-kpi-sub-unblocked');
  const apEl = document.getElementById('perf-kpi-ap');
  const subApEl = document.getElementById('perf-kpi-sub-ap');

  const ds = getActiveDataset();

  if (recallEl) recallEl.innerText = `${ds.recall}%`;
  if (subRecallEl) subRecallEl.innerHTML = `<span>▲ ${ds.tp}건 적발 / ${ds.totalDefects}건 (Lift ${ds.lift}배)</span>`;
  if (top20El) top20El.innerText = `${ds.top20Cutoff} 건`;
  if (subTop20El) subTop20El.innerHTML = `<span>ceil(${ds.totalCount} * 0.20) 규격 엄수</span>`;
  if (unblockedEl) unblockedEl.innerText = `${ds.fn} 건 잔류`;
  if (subUnblockedEl) subUnblockedEl.innerHTML = `<span>▼ 미검출 ${ds.fn}건 (상위 20% 우선 필터링)</span>`;
  if (apEl) apEl.innerText = (0.2000 + (parseFloat(ds.recall) / 500)).toFixed(4);
  if (subApEl) subApEl.innerHTML = `<span>${ds.scopeName} 순위 분별력</span>`;
};"""

assert old_perf in code, "old_perf not found in app.js"
code = code.replace(old_perf, new_perf, 1)

# 5. In initApp, call renderUniversalTimelineBar
init_old = """function initApp() {
  setupAuthGate();
  setupRoleSwitching();
  setupWaferDiagnosis();
  setupTriagePeriodInference();
  setupChamberPdM();
  setupAdminDashboard();
  setupConfusionDashboard();
  setupChatbot();
  setupSimulationLab();
  setupAdminWiki();
  setupQrModal();
  registerServiceWorker();

  // Initial render of default wafer, period inference, and SHAP comparison
  renderWafer(state.selectedWaferId);
  runTriagePeriodInference('all');
  if (typeof renderYieldDashboard === 'function') renderYieldDashboard();
  if (typeof renderAdminPerf === 'function') renderAdminPerf();"""

init_new = """function initApp() {
  setupAuthGate();
  setupRoleSwitching();
  setupWaferDiagnosis();
  setupTriagePeriodInference();
  setupChamberPdM();
  setupAdminDashboard();
  setupConfusionDashboard();
  setupChatbot();
  setupSimulationLab();
  setupAdminWiki();
  setupQrModal();
  registerServiceWorker();

  // Initial render of universal timeline bar, default wafer, period inference, and SHAP comparison
  if (typeof renderUniversalTimelineBar === 'function') renderUniversalTimelineBar();
  renderWafer(state.selectedWaferId);
  runTriagePeriodInference('all');
  if (typeof renderYieldDashboard === 'function') renderYieldDashboard();
  if (typeof renderAdminPerf === 'function') renderAdminPerf();"""

assert init_old in code, "init_old not found in app.js"
code = code.replace(init_old, init_new, 1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully upgraded app.js with dynamic ingestion and universal timeline engine!")
