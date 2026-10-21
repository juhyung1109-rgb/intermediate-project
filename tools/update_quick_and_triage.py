import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('web/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update renderQuickSamples
old_render_quick = """  container.innerHTML = '';
  samples.forEach(s => {
    const btn = document.createElement('button');
    btn.className = `preset-chip ${String(s.id) === String(state.selectedWaferId) ? 'active' : ''}`;
    btn.setAttribute('data-wafer-id', s.id);
    btn.innerHTML = `<span>${s.icon} ${s.label}</span>`;
    btn.onclick = () => {
      syncWaferSelection(s.id);
      renderWafer(s.id);
      showToast(`⚡ 빠른 진단 샘플: 웨이퍼 #${s.id} 진단 결과 로딩 완료`);
    };
    container.appendChild(btn);
  });
}"""

new_render_quick = """  container.innerHTML = '';
  samples.forEach(s => {
    const btn = document.createElement('button');
    btn.className = `preset-chip ${String(s.id) === String(state.selectedWaferId) ? 'active' : ''}`;
    btn.setAttribute('data-wafer-id', s.id);
    btn.innerHTML = `<span>${s.icon} ${s.label}</span>`;
    btn.onclick = () => {
      document.querySelectorAll('#triage-preset-chips .preset-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.selectedWaferId = String(s.id);
      const input = document.getElementById('wafer-search-input');
      if (input) input.value = s.id;
      if (typeof syncWaferSelection === 'function') syncWaferSelection(s.id);
      renderWafer(s.id);
      showToast(`⚡ 빠른 진단 샘플: 웨이퍼 #${s.id} 진단 결과 로딩 완료`);
    };
    container.appendChild(btn);
  });
}"""

assert old_render_quick in js, "old_render_quick not found"
js = js.replace(old_render_quick, new_render_quick, 1)
print("Updated renderQuickSamples click handler!")

# 2. Update setUnifiedGlobalPeriod with bulletproof execution sequence
old_set_unified = """  // 5. Update All Screens Dynamically
  const ds = getActiveDataset();

  // Dynamically switch analyzed wafer to that month's top abnormal wafer (never stuck on 1254!)
  if (ds.wafers && ds.wafers.length > 0) {
    const topDefect = ds.wafers.find(w => w.actual_label === 1) || ds.wafers[0];
    const targetWaferId = String(topDefect.sample_id);
    state.selectedWaferId = targetWaferId;
    if (typeof renderWafer === 'function') {
      renderWafer(targetWaferId);
    }
    const searchInput = document.getElementById('wafer-search-input');
    if (searchInput) searchInput.value = targetWaferId;
  }

  if (typeof renderShapComparison === 'function') renderShapComparison(state.unifiedPeriod);
  if (typeof filterConfusionTable === 'function') filterConfusionTable('ALL');
  if (typeof renderYieldDashboard === 'function') renderYieldDashboard();
  if (typeof renderAdminPerf === 'function') renderAdminPerf();
  if (typeof renderSimulationTable === 'function') renderSimulationTable();
  if (typeof renderAdminDriftTable === 'function') renderAdminDriftTable(state.unifiedPeriod);
  if (typeof runTriagePeriodInference === 'function') runTriagePeriodInference(state.unifiedPeriod);
  if (typeof renderQuickSamples === 'function') renderQuickSamples(state.unifiedPeriod);
  if (typeof runBatchSimulation === 'function') runBatchSimulation();

  showToast(`🔄 팹 관제 타임라인: [${ds.scopeName}] 연동 완료`);"""

new_set_unified = """  // 5. Update All Screens Dynamically (Bulletproof Sequence)
  const ds = getActiveDataset();

  // A. Quick samples & dynamic target wafer selection
  try {
    if (typeof renderQuickSamples === 'function') renderQuickSamples(state.unifiedPeriod);
  } catch (e) { console.warn('renderQuickSamples err:', e); }

  if (ds.wafers && ds.wafers.length > 0) {
    const topDefect = ds.wafers.find(w => w.actual_label === 1) || ds.wafers[0];
    const targetWaferId = String(topDefect.sample_id);
    state.selectedWaferId = targetWaferId;
    const searchInput = document.getElementById('wafer-search-input');
    if (searchInput) searchInput.value = targetWaferId;

    try {
      if (typeof renderWafer === 'function') renderWafer(targetWaferId);
    } catch (e) { console.warn('renderWafer err:', e); }
  }

  // B. Other screen updates
  try { if (typeof renderShapComparison === 'function') renderShapComparison(state.unifiedPeriod); } catch (e) { console.warn(e); }
  try { if (typeof filterConfusionTable === 'function') filterConfusionTable('ALL'); } catch (e) { console.warn(e); }
  try { if (typeof renderYieldDashboard === 'function') renderYieldDashboard(); } catch (e) { console.warn(e); }
  try { if (typeof renderAdminPerf === 'function') renderAdminPerf(); } catch (e) { console.warn(e); }
  try { if (typeof renderSimulationTable === 'function') renderSimulationTable(); } catch (e) { console.warn(e); }
  try { if (typeof renderAdminDriftTable === 'function') renderAdminDriftTable(state.unifiedPeriod); } catch (e) { console.warn(e); }
  try { if (typeof runTriagePeriodInference === 'function') runTriagePeriodInference(state.unifiedPeriod); } catch (e) { console.warn(e); }
  try { if (typeof runBatchSimulation === 'function') runBatchSimulation(); } catch (e) { console.warn(e); }

  showToast(`🔄 팹 관제 타임라인: [${ds.scopeName}] 연동 완료`);"""

assert old_set_unified in js, "old_set_unified not found in app.js"
js = js.replace(old_set_unified, new_set_unified, 1)
print("Updated setUnifiedGlobalPeriod with bulletproof execution sequence!")

# 3. Update runTriagePeriodInference to use dynamic dataset stats
old_run_triage = """window.runTriagePeriodInference = function(period) {
  const p = period || state.unifiedPeriod || state.selectedTriagePeriod || 'all';

  const statsMap = {
    'all': { total: 814, tp: 24, fails: 52, top20: 163, recall: 46.2, name: '전사 9개월 전수 누적' },
    '2008-07': { total: 17, tp: 2, fails: 6, top20: 4, recall: 33.3, name: '7월 양산 초기' },
    '2008-08': { total: 95, tp: 4, fails: 10, top20: 19, recall: 40.0, name: '8월 1차 트러블 피크' },
    '2008-09': { total: 116, tp: 1, fails: 3, top20: 24, recall: 33.3, name: '9월 1차 PM 정비 안정화' },
    '2008-10': { total: 86, tp: 2, fails: 2, top20: 18, recall: 100.0, name: '10월 1차 고수율 안정화' },
    '2008-11': { total: 100, tp: 0, fails: 4, top20: 20, recall: 0.0, name: '11월 45주차 롤아웃 기준선' },
    '2008-12': { total: 100, tp: 4, fails: 8, top20: 20, recall: 50.0, name: '12월 칠러/배압 이상 조짐' },
    '2009-01': { total: 100, tp: 5, fails: 12, top20: 20, recall: 41.7, name: '1월 53주차 2차 트러블 피크' },
    '2009-02': { total: 100, tp: 1, fails: 4, top20: 20, recall: 25.0, name: '2월 2차 PM 수율 회복' },
    '2009-03': { total: 100, tp: 1, fails: 3, top20: 20, recall: 33.3, name: '3월 2차 고수율 양산 정상화' }
  };"""

new_run_triage = """window.runTriagePeriodInference = function(period) {
  const p = period || state.unifiedPeriod || state.selectedTriagePeriod || 'all';
  const ds = getActiveDataset();

  const dynamicStat = {
    total: ds.totalCount,
    tp: ds.tp,
    fails: ds.totalDefects,
    top20: ds.top20Cutoff,
    recall: parseFloat(ds.recall),
    name: ds.scopeName
  };

  const statsMap = {
    'all': dynamicStat
  };"""

assert old_run_triage in js, "old_run_triage not found in app.js"
js = js.replace(old_run_triage, new_run_triage, 1)
print("Updated runTriagePeriodInference to use dynamic dataset stats!")

with open('web/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("web/app.js successfully updated!")
