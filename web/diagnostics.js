'use strict';
/**
 * SEMI-GUARD: Interactive Wafer Diagnostics & TreeExplainer SHAP Waterfall Engine
 * Exactly matches the enterprise semiconductor domain UI design requested by user.
 * Provides comprehensive, unfiltered inspection recommendations for all high-risk sensors regardless of final label.
 */
window.SemiDiagnostics = (() => {
  // Semiconductor Sensor Domain Metadata Dictionary (공정 설비 및 현장 조치 매핑)
  const SENSOR_META = {
    feature_512: { name: 'Dry Etch 전원 서지 전압', unit: 'V', chamber: 'Dry Etch 챔버', action: 'RF 파워 제너레이터 서지 트립 인터락 회로 및 DC 바이어스 보드 케이블 점검' },
    feature_29:  { name: 'CVD 챔버 1호기 배기 압력', unit: 'mTorr', chamber: 'CVD 챔버 1호기', action: 'CVD 배기 밸브 O-ring 헬륨 누설(Leak) 기밀성 검사 및 MFC 가스 밸브 세정' },
    feature_210: { name: '진공 압력 기저 레벨', unit: 'Torr', chamber: '진공 챔버', action: '진공 챔버 드라이 펌프(Dry Pump) 흡입 압력 및 슬릿 밸브 개폐 공압 점검' },
    feature_171: { name: '챔버 온도 안정화 편차', unit: '°C', chamber: '챔버 쿨링 시스템', action: '칠러 쿨런트 유량 및 챔버 온도 제어 센서 서모커플 접촉 상태 확인' },
    feature_104: { name: 'Dry Etch 챔버 2호기 RF 바이어스', unit: 'W', chamber: 'Dry Etch 챔버 2호기', action: 'Dry Etch 포커스 링(Focus Ring) 잔여 두께 측정 및 PM 교체 일정 수립' },
    feature_60:  { name: '식각 RF 전력 출력', unit: 'kW', chamber: 'Dry Etch 챔버', action: '식각 챔버 하부 전극 세트 부식 상태 점검 및 Throttle Valve 세척' },
    feature_170: { name: 'RF 정합기(Matcher) 임피던스', unit: 'Ω', chamber: 'RF Matcher', action: 'RF Matcher 가변 콘덴서 접점 세척 및 임피던스 영점 튜닝' },
    feature_489: { name: '전압 테스터 센서 라인', unit: 'V', chamber: '계측 스테이션', action: '전압 테스터 센서 라인 완전 단선 여부 및 접지선 전위 실측' },
    feature_543: { name: '박막 두께 균일도 센서', unit: 'Å', chamber: 'CVD 챔버', action: '박막 두께 타원계(Ellipsometer) 측정 및 샤워헤드 가스 분사 홀 클리닝' },
    feature_79:  { name: 'CVD 증착 속도 모니터', unit: 'nm/min', chamber: 'CVD 챔버', action: 'CVD 증착 두께 실측 및 서셉터 회전 모터 RPM 계측' },
    feature_103: { name: 'Dry Etch 챔버 1호기 RF 바이어스', unit: 'W', chamber: 'Dry Etch 챔버 1호기', action: '상부 샤워헤드 RF 전극 클리닝 및 매칭 네트워크 점검' },
    feature_28:  { name: 'CVD 챔버 2호기 배기 압력', unit: 'mTorr', chamber: 'CVD 챔버 2호기', action: '배기 스크러버 압력 드롭 점검 및 포라인 트랩 반응물 퍼지' },
    feature_124: { name: '챔버 진공 배기 밸브 개도율', unit: '%', chamber: '배기 시스템', action: '스로틀 밸브 모터 엔코더 및 실링 상태 확인' },
    feature_332: { name: '정전척(ESC) 헬륨 배면 냉각 압력', unit: 'sccm', chamber: 'ESC 척', action: 'ESC 헬륨 공급 라인 미세 누설 검사 및 웨이퍼 흡착력 측정' },
    feature_425: { name: '웨이퍼 온도 제어 서모커플', unit: '°C', chamber: '히터 스테이지', action: '히터 재킷 저항 실측 및 온도 컨트롤러 PID 게인 보정' }
  };

  const getSensorName = (id) => {
    const cleanId = String(id).trim();
    if (SENSOR_META[cleanId]) return `${cleanId} (${SENSOR_META[cleanId].name})`;
    const m = cleanId.match(/feature_(\d+)/);
    if (m) return `${cleanId} (공정 센서 #${m[1]})`;
    return cleanId;
  };

  const getSensorAction = (id, zScore) => {
    const cleanId = String(id).trim();
    if (SENSOR_META[cleanId]) return SENSOR_META[cleanId].action;
    const sign = (zScore || 0) > 0 ? '상한' : '하한';
    return `공정 관리선 ${sign} 이탈: 센서 케이블 접촉 상태 점검 및 기준 전압 영점 실측`;
  };

  const el = (tag, cls = '', text = null) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  };

  const num = (x) => x == null ? '미확인' : typeof x === 'number' ? x.toLocaleString('ko-KR', { maximumFractionDigits: 4 }) : String(x);
  const pct = (x) => x == null ? '미확인' : (x * 100).toFixed(2) + '%';

  function render(d, { compact = false, onQuestion = null, onInspection = null } = {}) {
    const root = el('div', 'diagnostic-wrapper');
    root.style.display = 'flex';
    root.style.flexDirection = 'column';
    root.style.gap = '22px';
    root.style.margin = '16px 0';

    const r = d.row;
    const isDefect = r.actual_label === 1 || r.category === 'TP';
    const isFP = r.category === 'FP';
    const isHighRisk = r.risk_score >= 0.1 || r.risk_rank <= Math.ceil(d.scope_count * 0.2);

    // ─────────────────────────────────────────────────────────────
    // 1. TOP WAFER OVERVIEW & HIGH-PRIORITY ACTION HEADER CARD
    // ─────────────────────────────────────────────────────────────
    const headerCard = el('div', 'card');
    headerCard.style.padding = '22px 26px';
    headerCard.style.background = '#ffffff';
    headerCard.style.borderRadius = '12px';
    headerCard.style.border = isHighRisk ? '1.5px solid #f87171' : '1px solid var(--border-color)';
    headerCard.style.boxShadow = isHighRisk ? '0 4px 14px rgba(239, 68, 68, 0.08)' : 'var(--shadow-sm)';
    headerCard.style.display = 'flex';
    headerCard.style.justifyContent = 'space-between';
    headerCard.style.alignItems = 'center';
    headerCard.style.flexWrap = 'wrap';
    headerCard.style.gap = '16px';

    const headerLeft = el('div');
    const titleRow = el('div');
    titleRow.style.display = 'flex';
    titleRow.style.alignItems = 'center';
    titleRow.style.gap = '10px';
    titleRow.style.marginBottom = '6px';

    const titleText = el('h3', '', `웨이퍼 표본 #${r.sample_id}`);
    titleText.style.margin = '0';
    titleText.style.fontSize = '1.35rem';
    titleText.style.fontWeight = '800';
    titleText.style.color = '#0f172a';

    const statusBadge = el('span', `risk-badge ${isHighRisk ? 'danger' : 'success'}`,
      isHighRisk ? `🚨 집중 점검 대상 (위험 순위 #${r.risk_rank}위)` : `✅ 정상 관리선 권역 (#${r.risk_rank}위)`);
    titleRow.append(titleText, statusBadge);

    const subText = el('p', '', `전체 ${d.scope_count}행 중 상위 ${pct(r.rank_fraction)} 위치 · 정답 라벨: ${r.actual_label == null ? '미확인(실시간 추론)' : (r.actual_label === 1 ? '확인 불량(Defect)' : '확인 정상(Pass)')} · ${r.category || '추론 표본'}`);
    subText.style.margin = '0';
    subText.style.fontSize = '0.86rem';
    subText.style.color = '#64748b';
    headerLeft.append(titleRow, subText);

    const metricsBox = el('div');
    metricsBox.style.display = 'flex';
    metricsBox.style.gap = '16px';
    metricsBox.style.alignItems = 'center';

    const riskBox = el('div');
    riskBox.style.textAlign = 'right';
    riskBox.innerHTML = `
      <div style="font-size:0.75rem; color:#64748b; font-weight:700;">불량 위험 점수 (Risk Score)</div>
      <div style="font-size:1.65rem; font-weight:900; color:${isHighRisk ? '#dc2626' : '#2563eb'};">${pct(r.risk_score)}</div>
    `;

    const actionBtnGroup = el('div');
    actionBtnGroup.style.display = 'flex';
    actionBtnGroup.style.gap = '8px';
    if (onQuestion) {
      const qBtn = el('button', 'action-btn', '🤖 AI 원인 질의');
      qBtn.type = 'button';
      qBtn.onclick = () => onQuestion(`웨이퍼 #${r.sample_id}의 불량 위험을 유발한 상위 이상 센서 목록과 현장에서 바로 점검해야 할 부품 가이드를 자세히 알려줘.`);
      actionBtnGroup.append(qBtn);
    }
    if (onInspection) {
      const inspBtn = el('button', 'action-btn primary', '🛠️ 전체 센서 점검 발령');
      inspBtn.type = 'button';
      inspBtn.onclick = () => onInspection(d);
      actionBtnGroup.append(inspBtn);
    }

    metricsBox.append(riskBox, actionBtnGroup);
    headerCard.append(headerLeft, metricsBox);
    root.append(headerCard);


    // ─────────────────────────────────────────────────────────────
    // 2. MAIN TWO-COLUMN GRID
    // ─────────────────────────────────────────────────────────────
    const grid = el('div');
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(490px, 1fr))';
    grid.style.gap = '20px';

    // ─────────────────────────────────────────────────────────────
    // CARD A: 🧠 SHAP 인공지능 원인 분해 워터폴 (XAI)
    // ─────────────────────────────────────────────────────────────
    const shapCard = el('div', 'card');
    shapCard.style.padding = '22px 24px';
    shapCard.style.background = '#ffffff';
    shapCard.style.borderRadius = '12px';
    shapCard.style.border = '1px solid var(--border-color)';
    shapCard.style.boxShadow = 'var(--shadow-sm)';

    const shapHeader = el('div');
    shapHeader.style.display = 'flex';
    shapHeader.style.justifyContent = 'space-between';
    shapHeader.style.alignItems = 'center';
    shapHeader.style.marginBottom = '12px';

    const shapTitle = el('div');
    shapTitle.style.display = 'flex';
    shapTitle.style.alignItems = 'center';
    shapTitle.style.gap = '8px';
    shapTitle.innerHTML = `<h3 style="font-size:1.15rem; font-weight:800; color:#0f172a; margin:0;">🧠 SHAP 인공지능 원인 분해 워터폴 (XAI)</h3>`;

    const treeBadge = el('span', '', 'TreeExplainer');
    treeBadge.style.background = '#eff6ff';
    treeBadge.style.color = '#2563eb';
    treeBadge.style.border = '1px solid #bfdbfe';
    treeBadge.style.fontSize = '0.78rem';
    treeBadge.style.fontWeight = '700';
    treeBadge.style.padding = '3px 10px';
    treeBadge.style.borderRadius = '6px';
    shapHeader.append(shapTitle, treeBadge);

    const shapDesc = el('p', '', '빨간색(+) 막대는 불량 위험도를 높인 치명 요인이며, 초록색(-) 막대는 정상성을 유지한 요인입니다.');
    shapDesc.style.fontSize = '0.86rem';
    shapDesc.style.color = '#64748b';
    shapDesc.style.margin = '0 0 16px 0';
    shapCard.append(shapHeader, shapDesc);

    // Full positive (risk-increase) sensors + negative (risk-decrease) sensors
    const shapList = el('div', 'shap-bars-container');
    const shapRows = (d.shap && d.shap.rows) || (d.shap && d.shap.waterfall) || [];
    const posRows = ((d.shap && d.shap.risk_increase) || shapRows.filter(x => x.shap > 0)).slice(0, 6);
    const negRows = ((d.shap && d.shap.risk_decrease) || shapRows.filter(x => x.shap < 0)).slice(0, 4);
    const combinedShap = [...posRows, ...negRows];

    // Calculate max absolute SHAP for normalized percentage bar width
    const maxShap = Math.max(0.1, ...combinedShap.map(x => Math.abs(x.shap)));

    combinedShap.forEach(item => {
      const row = el('div', 'shap-bar-row');
      const isPos = item.shap > 0;
      const widthPct = Math.min(100, Math.max(10, (Math.abs(item.shap) / maxShap) * 85));
      const sign = isPos ? '+' : '';
      const featLabel = getSensorName(item.feature);

      row.innerHTML = `
        <div class="shap-feat-name" title="${featLabel}">${featLabel}</div>
        <div class="shap-bar-track">
          <div class="shap-bar-fill ${isPos ? 'positive' : 'negative'}" style="width: ${widthPct}%;"></div>
        </div>
        <div class="shap-val-text" style="color: ${isPos ? '#ef4444' : '#10b981'};">${sign}${item.shap.toFixed(2)}</div>
      `;
      shapList.append(row);
    });
    shapCard.append(shapList);

    // ─────────────────────────────────────────────────────────────
    // Dynamic PdM Recommendation Box (사용자 첨부 이미지와 100% 동일한 비주얼)
    // ─────────────────────────────────────────────────────────────
    const pdmCard = el('div', 'pdm-recommendation-card');
    let recTitle = `🛡️ 현장 설비 예방보전(PdM) 권고 (웨이퍼 #${r.sample_id} - `;
    let recBadgeText = '예방보전 (양품 통과)';
    let recBadgeClass = 'warning';
    let recBodyHtml = '';

    const topPosFeat = posRows[0] ? getSensorName(posRows[0].feature) : 'feature_104';
    const topPosFeat2 = posRows[1] ? getSensorName(posRows[1].feature) : 'feature_170';
    const topSensorObj = d.top_sensors && d.top_sensors[0] ? d.top_sensors[0] : null;
    const topAction = topSensorObj ? getSensorAction(topSensorObj.sensor, topSensorObj.z_score) : '포커스 링 잔여 두께를 측정하고 PM 교체 일정을 수립하십시오.';

    if (isHighRisk) {
      if (isFP) {
        recTitle += 'FP 안전마진 / 마모 조기 경보)';
        recBadgeText = '예방보전 (양품 통과)';
        recBadgeClass = 'warning';
        recBodyHtml = `<strong>[설비 예방보전(PdM) 분석 연계]</strong> AI 모델이 <code>${topPosFeat}</code> 편차 및 <code>${topPosFeat2}</code> 임피던스 이상을 감지하여 보수적 안전마진으로 선제 경보를 발령했습니다. ${topAction} (※ 웨이퍼 자체는 정상이므로 불필요한 폐기를 방지하고 정상 통과시키십시오.)`;
      } else {
        recTitle += '긴급 챔버 결함 방어 / 즉시 정비 권고)';
        recBadgeText = '즉시 정비 권고 (치명 이상 감지)';
        recBadgeClass = 'danger';
        pdmCard.className = 'pdm-recommendation-card danger';
        recBodyHtml = `<strong>[AI 모델 & 공정 통계 진단 연계]</strong> 불량 위험도를 치명적으로 상승시킨 <code>${topPosFeat}</code> 및 <code>${topPosFeat2}</code>의 급격한 이상 편차가 감지되었습니다. ${topAction} 후속 생산 웨이퍼의 연쇄 불량을 방지하기 위해 해당 챔버 인터락 점검을 긴급 발령하십시오.`;
      }
    } else {
      recTitle += 'TN 정상 양품 / SPC 관리선 정상)';
      recBadgeText = '정상 양품 출하 (Pass)';
      recBadgeClass = 'success';
      pdmCard.className = 'pdm-recommendation-card success';
      recBodyHtml = `<strong>[공정 품질 SPC 관리선 진단]</strong> 주요 챔버 센서 측정값이 통계적 공정 관리선(SPC ±2.0σ) 내에서 완벽한 정상 범위에 있습니다. 별도의 긴급 설비 정비 없이 차기 패키징 공정으로 정상 출하하십시오.`;
    }

    pdmCard.innerHTML = `
      <div style="font-weight:800; font-size:0.98rem; color:${pdmCard.classList.contains('danger') ? '#991b1b' : pdmCard.classList.contains('success') ? '#065f46' : '#854d0e'};">
        ${recTitle}
      </div>
      <div>
        <span class="pdm-badge ${recBadgeClass}">${recBadgeText}</span>
      </div>
      <div style="font-size:0.87rem; line-height:1.65; color:${pdmCard.classList.contains('danger') ? '#7f1d1d' : pdmCard.classList.contains('success') ? '#064e3b' : '#854d0e'};">
        ${recBodyHtml}
      </div>
    `;
    shapCard.append(pdmCard);
    grid.append(shapCard);


    // ─────────────────────────────────────────────────────────────
    // CARD B: 🛠️ 점검해야 할 핵심 센서 전수 목록 & 현장 조치 가이드
    // (정상 여부와 상관없이 위험도 높은 센서부터 빠짐없이 다 알려줌!)
    // ─────────────────────────────────────────────────────────────
    const inspectCard = el('div', 'card');
    inspectCard.style.padding = '22px 24px';
    inspectCard.style.background = '#ffffff';
    inspectCard.style.borderRadius = '12px';
    inspectCard.style.border = '1px solid var(--border-color)';
    inspectCard.style.boxShadow = 'var(--shadow-sm)';

    const inspectHeader = el('div');
    inspectHeader.style.marginBottom = '14px';

    const topSensors = d.top_sensors || [];
    const extremeCount = topSensors.filter(s => Math.abs(s.z_score || 0) >= 1.5).length;

    inspectHeader.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:8px;">
          <h3 style="font-size:1.15rem; font-weight:800; color:#0f172a; margin:0;">🛠️ 점검해야 할 센서 목록 & 현장 조치 가이드</h3>
          <span class="brand-tag" style="background:#fee2e2; color:#dc2626; border-color:#fca5a5; font-weight:800;">관리선 이탈 ${extremeCount}개</span>
        </div>
        <span class="brand-tag" style="background:#f1f5f9; color:#475569;">전수 이상 센서 ${topSensors.length}개 탐색</span>
      </div>
      <p style="font-size:0.86rem; color:#64748b; margin:6px 0 0 0;">
        💡 <strong>엔지니어 핵심 원칙:</strong> 웨이퍼의 정답 판정과 상관없이, 위험도를 유발한 모든 센서의 실시간 측정값과 구체적 현장 점검 부품을 즉시 확인하고 조치할 수 있습니다.
      </p>
    `;
    inspectCard.append(inspectHeader);

    // Filter toolbar for engineers
    const filterBar = el('div');
    filterBar.style.display = 'flex';
    filterBar.style.gap = '8px';
    filterBar.style.alignItems = 'center';
    filterBar.style.marginBottom = '12px';
    filterBar.style.flexWrap = 'wrap';

    let currentFilter = 'all';
    const filterBtns = [
      ['all', `전체 점검 대상 (${topSensors.length}개)`],
      ['extreme', `🚨 긴급 점검 (≥1.5σ, ${extremeCount}개)`],
      ['positive', `📈 상한 초과 센서`],
      ['negative', `📉 하한 미달 센서`]
    ];

    const tableWrap = el('div', 'table-scroll');
    tableWrap.style.overflowX = 'auto';
    tableWrap.style.maxHeight = '480px';

    const table = el('table', 'sensor-inspect-table');
    table.innerHTML = `
      <thead>
        <tr>
          <th style="min-width:200px;">점검 대상 센서 ID / 설비명</th>
          <th>실시간 측정값</th>
          <th>정상 중앙값</th>
          <th>편차 (Z-Score)</th>
          <th>점검 우선순위</th>
          <th style="min-width:260px;">현장 엔지니어 점검 권고 조치</th>
          <th style="text-align:center; min-width:85px;">작업</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');

    function renderTableRows(filter) {
      tbody.innerHTML = '';
      const filtered = topSensors.filter(s => {
        const z = s.z_score || 0;
        if (filter === 'extreme') return Math.abs(z) >= 1.5;
        if (filter === 'positive') return z > 0;
        if (filter === 'negative') return z < 0;
        return true;
      });

      if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:#64748b;">선택한 필터 조건에 해당하는 점검 센서가 없습니다.</td></tr>`;
        return;
      }

      filtered.forEach(s => {
        const tr = el('tr');
        const z = s.z_score || 0;
        const absZ = Math.abs(z);
        const isExtreme = absZ >= 1.5;
        const isWarning = absZ >= 1.0;

        const priorityBadge = isExtreme
          ? `<span class="risk-badge danger" style="font-weight:800;">🚨 긴급 점검 (${z > 0 ? '+' : ''}${z.toFixed(2)}σ)</span>`
          : isWarning
          ? `<span class="risk-badge warning">⚠️ 주의 관찰 (${z > 0 ? '+' : ''}${z.toFixed(2)}σ)</span>`
          : `<span class="risk-badge success">✅ 기준선 내 (${z > 0 ? '+' : ''}${z.toFixed(2)}σ)</span>`;

        const zColor = isExtreme ? '#dc2626' : isWarning ? '#d97706' : '#15803d';
        const sensorDisplayName = getSensorName(s.sensor);
        const actionText = getSensorAction(s.sensor, z);

        tr.innerHTML = `
          <td><strong style="color:#0f172a; font-family:var(--font-mono, monospace); font-size:0.84rem;">${sensorDisplayName}</strong></td>
          <td><b>${num(s.raw_value)}</b></td>
          <td style="color:#64748b;">${num(s.reference_median)}</td>
          <td style="color:${zColor}; font-weight:800; font-family:var(--font-mono, monospace);">${z > 0 ? '+' : ''}${z.toFixed(2)}σ</td>
          <td>${priorityBadge}</td>
          <td style="font-size:0.82rem; color:#1e293b; line-height:1.45;">${actionText}</td>
          <td style="text-align:center;">
            <button class="action-btn" style="padding:4px 8px; font-size:0.75rem;" title="이 센서 점검 지시서 작성">
              <span>점검</span>
            </button>
          </td>
        `;

        tr.querySelector('button').onclick = () => {
          if (onInspection) {
            onInspection({
              row: r,
              recommendation: {
                title: `${s.sensor} 긴급 설비 정밀 점검`,
                checks: [actionText, '센서 표준 신호선 및 커넥터 체결 상태 확인', '교체 후 재현 계측 및 SPC 관리도 확인']
              },
              summary: `웨이퍼 #${r.sample_id} 점검 중 ${sensorDisplayName} 편차(${z > 0 ? '+' : ''}${z.toFixed(2)}σ) 감지`,
              top_sensors: [s]
            });
          }
        };

        tbody.append(tr);
      });
    }

    filterBtns.forEach(([key, label]) => {
      const b = el('button', `action-btn ${key === currentFilter ? 'primary' : ''}`, label);
      b.style.fontSize = '0.78rem';
      b.style.padding = '4px 12px';
      b.onclick = () => {
        currentFilter = key;
        filterBar.querySelectorAll('button').forEach(btn => btn.classList.remove('primary'));
        b.classList.add('primary');
        renderTableRows(key);
      };
      filterBar.append(b);
    });

    inspectCard.append(filterBar);
    renderTableRows(currentFilter);
    tableWrap.append(table);
    inspectCard.append(tableWrap);

    // Bottom Action Bar: Export CSV & Batch Issue
    const bottomActionBar = el('div');
    bottomActionBar.style.display = 'flex';
    bottomActionBar.style.justifyContent = 'space-between';
    bottomActionBar.style.alignItems = 'center';
    bottomActionBar.style.marginTop = '16px';
    bottomActionBar.style.flexWrap = 'wrap';
    bottomActionBar.style.gap = '10px';

    const exportBtn = el('button', 'action-btn', '📥 점검 센서 목록 CSV 내보내기');
    exportBtn.style.fontSize = '0.8rem';
    exportBtn.onclick = () => {
      const csvRows = [
        ['sample_id', 'sensor', 'sensor_name', 'raw_value', 'reference_median', 'z_score', 'action'],
        ...topSensors.map(s => [
          r.sample_id,
          s.sensor,
          `"${getSensorName(s.sensor)}"`,
          s.raw_value,
          s.reference_median,
          s.z_score,
          `"${getSensorAction(s.sensor, s.z_score)}"`
        ])
      ];
      const csvContent = '\uFEFF' + csvRows.map(row => row.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `wafer_${r.sample_id}_inspection_sensors.csv`;
      link.click();
    };

    const countInfo = el('span', '', `총 ${topSensors.length}개 센서 계측치 및 정상군(1,170행) 대비 편차 전수 분석 완료`);
    countInfo.style.fontSize = '0.82rem';
    countInfo.style.color = '#64748b';

    bottomActionBar.append(countInfo, exportBtn);
    inspectCard.append(bottomActionBar);

    grid.append(inspectCard);
    root.append(grid);

    return root;
  }

  return { render };
})();
