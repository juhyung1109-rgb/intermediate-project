app_path = r"web\app.js"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update renderYieldDashboard to support all 18 months and dynamic active pool
old_yield = """    const months = [
      { m: '2008-07', prod: '412 건', prodFail: '29 건', prodRate: '7.04%', testTotal: 17, testFail: 6, testRate: '35.29%', note: '양산 초기 안정화' },
      { m: '2008-08', prod: '380 건', prodFail: '42 건', prodRate: '11.05%', testTotal: 95, testFail: 10, testRate: '10.53%', note: '🚨 1차 트러블 피크 (34주차)' },
      { m: '2008-09', prod: '395 건', prodFail: '18 건', prodRate: '4.56%', testTotal: 116, testFail: 3, testRate: '2.59%', note: '🛠️ 1차 PM 정비 안정화' },
      { m: '2008-10', prod: '380 건', prodFail: '15 건', prodRate: '3.95%', testTotal: 86, testFail: 2, testRate: '2.33%', note: '✅ 1차 고수율 정상화' },
      { m: '2008-11', prod: '100 건', prodFail: '4 건', prodRate: '4.00%', testTotal: 100, testFail: 4, testRate: '4.00%', note: '45주차 롤아웃 기준선' },
      { m: '2008-12', prod: '100 건', prodFail: '8 건', prodRate: '8.00%', testTotal: 100, testFail: 8, testRate: '8.00%', note: '⚠️ 칠러 냉각수/배압 이상' },
      { m: '2009-01', prod: '100 건', prodFail: '12 건', prodRate: '12.00%', testTotal: 100, testFail: 12, testRate: '12.00%', note: '🚨 2차 트러블 피크 (53주차)' },
      { m: '2009-02', prod: '100 건', prodFail: '4 건', prodRate: '4.00%', testTotal: 100, testFail: 4, testRate: '4.00%', note: '🛠️ 2차 긴급 PM 수율 회복' },
      { m: '2009-03', prod: '100 건', prodFail: '3 건', prodRate: '3.00%', testTotal: 100, testFail: 3, testRate: '3.00%', note: '✅ 2차 고수율 양산 정상화' }
    ];

    let html = '';
    months.forEach(row => {
      const isSelected = p === row.m;
      const isPeak = row.m === '2008-08' || row.m === '2009-01';
      const isRecover = row.m === '2008-10' || row.m === '2009-03';
      let rowStyle = 'cursor:pointer;';
      if (isSelected) {
        rowStyle += 'background:#e0f2fe; font-weight:700; border-left:4px solid #0284c7;';
      } else if (isPeak) {
        rowStyle += 'background:var(--danger-soft);';
      } else if (isRecover) {
        rowStyle += 'background:var(--success-soft);';
      }

      html += `
        <tr style="${rowStyle}" onclick="setUnifiedGlobalPeriod('${row.m}')" title="클릭 시 ${row.m} 월별 관제 전환">
          <td><b>${row.m}</b></td>
          <td>${row.prod}</td>
          <td><b>${row.prodFail}</b></td>
          <td>${row.prodRate}</td>
          <td><b>${row.testTotal}매</b> (불량 ${row.testFail}매 / ${row.testRate})</td>
          <td><span style="font-size:0.82rem;">${row.note}</span></td>
        </tr>
      `;
    });

    // Accumulated Total row
    const isAllSelected = p === 'all';
    const allStyle = isAllSelected ? 'background:#dbeafe; font-weight:800; border:2px solid #0284c7; cursor:pointer;' : 'background:#f1f5f9; font-weight:800; border-top:2px solid #cbd5e1; cursor:pointer;';
    html += `
      <tr style="${allStyle}" onclick="setUnifiedGlobalPeriod('all')" title="클릭 시 전체 누적 관제 전환">
        <td><b>전사 9개월 누적 전수 합계</b></td>
        <td><b>2,067 건</b></td>
        <td><b style="color:var(--danger);">127 건</b></td>
        <td><b style="color:var(--danger);">6.14%</b></td>
        <td><b>814매 (불량 52매 / 6.39%)</b></td>
        <td><span class="risk-badge primary">🌐 814매 전수 누적 SSOT</span></td>
      </tr>
    `;

    monthlyTbody.innerHTML = html;"""

new_yield = """    const allMonthsMaster = [
      { m: '2008-07', prodNum: 412, failNum: 29, testTotal: 17, testFail: 6, note: '양산 초기 안정화' },
      { m: '2008-08', prodNum: 380, failNum: 42, testTotal: 95, testFail: 10, note: '🚨 1차 트러블 피크 (34주차)' },
      { m: '2008-09', prodNum: 395, failNum: 18, testTotal: 116, testFail: 3, note: '🛠️ 1차 PM 정비 안정화' },
      { m: '2008-10', prodNum: 380, failNum: 15, testTotal: 86, testFail: 2, note: '✅ 1차 고수율 정상화' },
      { m: '2008-11', prodNum: 100, failNum: 4, testTotal: 100, testFail: 4, note: '45주차 롤아웃 기준선' },
      { m: '2008-12', prodNum: 100, failNum: 8, testTotal: 100, testFail: 8, note: '⚠️ 칠러 냉각수/배압 이상' },
      { m: '2009-01', prodNum: 100, failNum: 12, testTotal: 100, testFail: 12, note: '🚨 2차 트러블 피크 (53주차)' },
      { m: '2009-02', prodNum: 100, failNum: 4, testTotal: 100, testFail: 4, note: '🛠️ 2차 긴급 PM 수율 회복' },
      { m: '2009-03', prodNum: 100, failNum: 3, testTotal: 100, testFail: 3, note: '✅ 2차 고수율 양산 정상화' },
      { m: '2009-04', prodNum: 100, failNum: 4, testTotal: 100, testFail: 4, note: '2009 봄철 램프업 가동' },
      { m: '2009-05', prodNum: 100, failNum: 5, testTotal: 100, testFail: 5, note: '⚠️ RF 매처/서셉터 미세 편차' },
      { m: '2009-06', prodNum: 100, failNum: 4, testTotal: 100, testFail: 4, note: '초여름 정상 가동' },
      { m: '2009-07', prodNum: 100, failNum: 7, testTotal: 100, testFail: 7, note: '⚠️ 냉각탑 효율 저하 칠러 상승' },
      { m: '2009-08', prodNum: 100, failNum: 11, testTotal: 100, testFail: 11, note: '🚨 하계 트러블 피크 (식각 마모)' },
      { m: '2009-09', prodNum: 100, failNum: 3, testTotal: 100, testFail: 3, note: '🛠️ 하계 오버홀 PM 복구' },
      { m: '2009-10', prodNum: 100, failNum: 2, testTotal: 100, testFail: 2, note: '✅ 초고수율 양산 안정 (2.0%)' },
      { m: '2009-11', prodNum: 100, failNum: 3, testTotal: 100, testFail: 3, note: '고수율 유지' },
      { m: '2009-12', prodNum: 100, failNum: 4, testTotal: 100, testFail: 4, note: '연말 안정 가동' }
    ];

    const ds = getActiveDataset();
    const activeMonthsSet = new Set(ds.pool.map(w => w.month || w.timestamp.slice(0, 7)));
    const activeMonths = allMonthsMaster.filter(row => activeMonthsSet.has(row.m));

    let sumProd = 0, sumFail = 0, sumTest = 0, sumTestFail = 0;
    let html = '';

    activeMonths.forEach(row => {
      sumProd += row.prodNum;
      sumFail += row.failNum;
      sumTest += row.testTotal;
      sumTestFail += row.testFail;

      const isSelected = p === row.m;
      const isPeak = row.m === '2008-08' || row.m === '2009-01' || row.m === '2009-08';
      const isRecover = row.m === '2008-10' || row.m === '2009-03' || row.m === '2009-10';
      let rowStyle = 'cursor:pointer;';
      if (isSelected) {
        rowStyle += 'background:#e0f2fe; font-weight:700; border-left:4px solid #0284c7;';
      } else if (isPeak) {
        rowStyle += 'background:var(--danger-soft);';
      } else if (isRecover) {
        rowStyle += 'background:var(--success-soft);';
      }

      const prodRate = (row.failNum / row.prodNum * 100).toFixed(2) + '%';
      const testRate = (row.testFail / row.testTotal * 100).toFixed(2) + '%';

      html += `
        <tr style="${rowStyle}" onclick="setUnifiedGlobalPeriod('${row.m}')" title="클릭 시 ${row.m} 월별 관제 전환">
          <td><b>${row.m}</b></td>
          <td>${row.prodNum.toLocaleString()} 건</td>
          <td><b>${row.failNum} 건</b></td>
          <td>${prodRate}</td>
          <td><b>${row.testTotal}매</b> (불량 ${row.testFail}매 / ${testRate})</td>
          <td><span style="font-size:0.82rem;">${row.note}</span></td>
        </tr>
      `;
    });

    // Accumulated Total row
    const totalProdRate = (sumFail / sumProd * 100).toFixed(2) + '%';
    const totalTestRate = (sumTestFail / sumTest * 100).toFixed(2) + '%';
    const isAllSelected = p === 'all';
    const allStyle = isAllSelected ? 'background:#dbeafe; font-weight:800; border:2px solid #0284c7; cursor:pointer;' : 'background:#f1f5f9; font-weight:800; border-top:2px solid #cbd5e1; cursor:pointer;';
    
    html += `
      <tr style="${allStyle}" onclick="setUnifiedGlobalPeriod('all')" title="클릭 시 전체 누적 관제 전환">
        <td><b>전사 활성 누적 합계 (${activeMonths.length}개월)</b></td>
        <td><b>${sumProd.toLocaleString()} 건</b></td>
        <td><b style="color:var(--danger);">${sumFail} 건</b></td>
        <td><b style="color:var(--danger);">${totalProdRate}</b></td>
        <td><b>${sumTest}매 (불량 ${sumTestFail}매 / ${totalTestRate})</b></td>
        <td><span class="risk-badge primary">🌐 누적 ${sumTest}매 SSOT</span></td>
      </tr>
    `;

    monthlyTbody.innerHTML = html;"""

assert old_yield in code, "old_yield not found in app.js"
code = code.replace(old_yield, new_yield, 1)

# 2. Update renderSimulationTable to dynamically calculate from active dataset
old_sim_table = """window.renderSimulationTable = function() {
  const simTbody = document.getElementById('admin-sim-tbody');
  if (!simTbody) return;

  simTbody.innerHTML = '';
  const uData = window.SEMI_UNIFIED_DATA;
  const tableData = (uData && uData.sim_table) ? uData.sim_table : [];
  const totalDefects = (uData && uData.total_defects) ? uData.total_defects : 52;

  tableData.forEach(row => {
    const tr = document.createElement('tr');
    const ratioStr = row.pct || row.ratio || '';
    const isBase = ratioStr.includes('20%');
    if (isBase) tr.style.backgroundColor = 'rgba(37, 99, 235, 0.08)';

    const count = row.sample_count || row.selected || 0;
    const detected = row.detected_defects !== undefined ? row.detected_defects : row.detected;
    const recallStr = String(row.recall).includes('%') ? row.recall : `${row.recall}%`;
    const precStr = String(row.precision).includes('%') ? row.precision : `${row.precision}%`;
    const liftStr = String(row.lift).includes('x') || String(row.lift).includes('배') ? row.lift : `${row.lift}배`;

    tr.innerHTML = `
      <td><b>${ratioStr}</b></td>
      <td>${count} 건</td>
      <td><b>${detected} 건</b> / ${totalDefects}건</td>
      <td style="color: var(--primary); font-weight:700;">${recallStr}</td>
      <td>${precStr}</td>
      <td><span class="brand-tag">${liftStr}</span></td>
    `;
    simTbody.appendChild(tr);
  });
};"""

new_sim_table = """window.renderSimulationTable = function() {
  const simTbody = document.getElementById('admin-sim-tbody');
  if (!simTbody) return;

  simTbody.innerHTML = '';
  const ds = getActiveDataset();
  const sortedWafers = [...ds.wafers].sort((a, b) => b.risk_score - a.risk_score);
  const totalWafers = sortedWafers.length;
  const totalDefects = ds.totalDefects;
  const defectRate = parseFloat(ds.defectRate) / 100;

  const ratios = [5, 10, 15, 20, 25, 30, 40, 50];

  ratios.forEach(pct => {
    const count = Math.max(1, Math.ceil(totalWafers * (pct / 100)));
    const detected = sortedWafers.slice(0, count).filter(w => w.actual_label === 1).length;
    const recallVal = totalDefects > 0 ? ((detected / totalDefects) * 100).toFixed(1) : '100.0';
    const precVal = count > 0 ? ((detected / count) * 100).toFixed(1) : '0.0';
    const liftVal = defectRate > 0 ? (parseFloat(precVal) / (defectRate * 100)).toFixed(2) : '1.00';

    const tr = document.createElement('tr');
    if (pct === 20) tr.style.backgroundColor = 'rgba(37, 99, 235, 0.08)';

    tr.innerHTML = `
      <td><b>${pct}%</b></td>
      <td>${count} 건</td>
      <td><b>${detected} 건</b> / ${totalDefects}건</td>
      <td style="color: var(--primary); font-weight:700;">${recallVal}%</td>
      <td>${precVal}%</td>
      <td><span class="brand-tag">${liftVal}x</span></td>
    `;
    simTbody.appendChild(tr);
  });
};"""

assert old_sim_table in code, "old_sim_table not found in app.js"
code = code.replace(old_sim_table, new_sim_table, 1)

# 3. Update renderWafer to look into SEMI_CUMULATIVE_DATA.wafer_details
old_render_w = """function renderWafer(waferId) {
  state.selectedWaferId = String(waferId);
  const wid = String(waferId);
  const totalCount = 814;
  const top20Cutoff = 163;

  let detail = null;
  if (window.SEMI_UNIFIED_DATA && window.SEMI_UNIFIED_DATA.wafer_details && window.SEMI_UNIFIED_DATA.wafer_details[wid]) {
    detail = window.SEMI_UNIFIED_DATA.wafer_details[wid];
  } else if (window.SEMI_BATCH500_DATA && window.SEMI_BATCH500_DATA.wafer_details && window.SEMI_BATCH500_DATA.wafer_details[wid]) {
    detail = window.SEMI_BATCH500_DATA.wafer_details[wid];
  } else if (typeof SEMI_DATA !== 'undefined' && SEMI_DATA.waferDetails && SEMI_DATA.waferDetails[wid]) {
    detail = SEMI_DATA.waferDetails[wid];
  } else {
    detail = generateDynamicWafer(waferId);
  }"""

new_render_w = """function renderWafer(waferId) {
  state.selectedWaferId = String(waferId);
  const wid = String(waferId);
  const ds = getActiveDataset();
  const totalCount = ds.pool.length;
  const top20Cutoff = Math.max(1, Math.ceil(totalCount * 0.20));

  let detail = null;
  const cumData = window.SEMI_CUMULATIVE_DATA;
  if (cumData && cumData.wafer_details && cumData.wafer_details[wid]) {
    detail = cumData.wafer_details[wid];
  } else if (window.SEMI_UNIFIED_DATA && window.SEMI_UNIFIED_DATA.wafer_details && window.SEMI_UNIFIED_DATA.wafer_details[wid]) {
    detail = window.SEMI_UNIFIED_DATA.wafer_details[wid];
  } else if (window.SEMI_BATCH500_DATA && window.SEMI_BATCH500_DATA.wafer_details && window.SEMI_BATCH500_DATA.wafer_details[wid]) {
    detail = window.SEMI_BATCH500_DATA.wafer_details[wid];
  } else if (typeof SEMI_DATA !== 'undefined' && SEMI_DATA.waferDetails && SEMI_DATA.waferDetails[wid]) {
    detail = SEMI_DATA.waferDetails[wid];
  } else {
    detail = generateDynamicWafer(waferId);
  }"""

assert old_render_w in code, "old_render_w not found in app.js"
code = code.replace(old_render_w, new_render_w, 1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully polished full cumulative app.js!")
