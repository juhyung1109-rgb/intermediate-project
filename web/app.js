/**
 * SEMI-GUARD v3: Unified Enterprise Dashboard Controller
 * Seamlessly connects the rich enterprise UI with the fitted FastAPI backend & Python Tool engine.
 */
'use strict';

// Shorthand selector
const $ = id => document.getElementById(id);

// Application State
const state = {
  role: 'engineer',
  taskMode: 'engineer',
  currentView: 'view-hub',
  datasetId: null,
  period: 'all',
  ratio: 0.2,
  overviewData: null,
  temporalData: null,
  confusionFilter: 'all',
  confusionPage: 0,
  shapMode: 'both',
  conversations: {},
  epoch: 0,
  diagnosticRequest: 0,
  authDemo: true,
  faultInjected: null
};

// Formatting helpers
const format = x => x == null ? '미확인' : typeof x === 'boolean' ? (x ? '예' : '아니오') : typeof x === 'number' ? x.toLocaleString('ko-KR', { maximumFractionDigits: 5 }) : String(x);
const pct = x => x == null ? '미확인' : (x * 100).toFixed(2) + '%';
const labels = {
  row_id: '행 ID', sample_id: '표본 ID', risk_score: '위험 점수', risk_rank: '위험 순위',
  category: '분류', actual_label: '정답 라벨', selected_for_review: '우선 검토',
  abnormal_sensor_count: '이상 센서 수', timestamp: '측정 시각', period: '기간',
  count: '표본 수', known_label_count: '확인 라벨', confirmed_failures: '확인 불량',
  confirmed_failure_rate: '확인 불량률', mean_risk_score: '평균 위험 점수', sensor: '센서',
  raw_value: '원본값', reference_mean: '정상 평균', reference_median: '정상 중앙값',
  reference_std: '기준 표준편차', z_score: '편차 Z', missing: '결측', feature: '피처',
  shap: '기여도', input_mean: '업로드 평균', shift_std: '평균 이동 σ', std_ratio: '표준편차 비',
  ks_distance: 'KS 거리', mean_abs_shap: '평균 절대 SHAP', rank: '순위', direction: '추세',
  drift_index: '드리프트 지수', pearson_r: 'Pearson r', kendall_tau: 'Kendall tau',
  start_mean: '초기 평균', end_mean: '후기 평균', day: '관측일', known: '확인 라벨',
  failures: '불량', rolling_failure_rate: '7일 불량률'
};

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text != null) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}

function button(text, fn, cls = 'action-btn') {
  const b = el('button', text, cls);
  b.type = 'button';
  b.onclick = fn;
  return b;
}

function showToast(text, isError = false) {
  const n = $('global-notice');
  if (!n) return;
  n.textContent = text;
  n.style.display = text ? 'block' : 'none';
  n.style.background = isError ? 'var(--danger-soft)' : '#eff6ff';
  n.style.color = isError ? 'var(--danger)' : '#1d4ed8';
  n.style.borderColor = isError ? '#fca5a5' : '#bfdbfe';
  if (text && !isError) {
    setTimeout(() => { if (n.textContent === text) n.style.display = 'none'; }, 5000);
  }
}

async function api(path, options = {}) {
  const reqHeaders = { ...(options.headers || {}) };
  try {
    const user = (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser);
    const email = (user && user.email) || localStorage.getItem('semiguard_current_email') || '';
    if (email) reqHeaders['X-User-Email'] = email;
  } catch(e) {}
  const r = await fetch(path, { credentials: 'same-origin', ...options, headers: reqHeaders });
  let d;
  try { d = await r.json(); } catch { throw Error(`서버 응답 파싱 실패 (${r.status})`); }
  if (!r.ok) throw Error(typeof d.detail === 'string' ? d.detail : JSON.stringify(d.detail || d));
  return d;
}

const post = (path, payload) => api(path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

async function busy(btn, fn) {
  if (btn) btn.disabled = true;
  try {
    return await fn();
  } catch (e) {
    showToast(e.message, true);
    console.error(e);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function url(part, extra = {}) {
  return `/api/dashboard/${state.datasetId}/${part}?` + new URLSearchParams({
    period: state.period,
    ratio: state.ratio,
    ...extra
  });
}

// SVG Graph Generator
function graph(title, x, y, line = false) {
  const ns = 'http://www.w3.org/2000/svg', s = document.createElementNS(ns, 'svg');
  s.setAttribute('viewBox', '-15 0 765 325');
  s.setAttribute('aria-label', title);
  s.setAttribute('role', 'img');
  s.classList.add('chart');
  s.style.display = 'block';
  s.style.width = '100%';
  s.style.maxWidth = '100%';
  s.style.height = 'auto';
  s.style.background = '#ffffff';
  s.style.borderRadius = '8px';
  s.style.boxSizing = 'border-box';

  function add(tag, attrs, text) {
    const n = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    if (text != null) n.textContent = text;
    s.append(n);
    return n;
  }

  add('text', { x: 50, y: 24, 'font-size': 14, 'font-weight': '700', fill: '#1e3a8a' }, title);
  const values = y.filter(v => v != null && Number.isFinite(v));
  const lo = Math.min(0, ...values);
  const hi = Math.max(0, ...values) || 1;
  const range = hi - lo || 1;
  const py = v => 220 - (v - lo) / range * 165;
  const w = 640 / Math.max(1, x.length);

  add('line', { x1: 58, y1: py(0), x2: 730, y2: py(0), stroke: '#cbd5e1' });
  add('text', { x: 52, y: 58, 'font-size': 11, 'text-anchor': 'end', fill: '#64748b', 'font-weight': '600' }, format(hi));
  add('text', { x: 52, y: 225, 'font-size': 11, 'text-anchor': 'end', fill: '#64748b', 'font-weight': '600' }, format(lo));

  let previous = null;
  y.forEach((v, i) => {
    if (v == null || !Number.isFinite(v)) { previous = null; return; }
    const px = 68 + w * (i + 0.5);
    let node;
    if (line) {
      if (previous) add('line', { x1: previous[0], y1: previous[1], x2: px, y2: py(v), stroke: '#2563eb', 'stroke-width': 2.5 });
      node = add('circle', { cx: px, cy: py(v), r: 4, fill: '#2563eb' });
      previous = [px, py(v)];
    } else {
      node = add('rect', {
        x: px - w * 0.32, y: Math.min(py(v), py(0)),
        width: Math.max(3, w * 0.64), height: Math.max(2, Math.abs(py(v) - py(0))),
        fill: v < 0 ? '#10b981' : '#ef4444', rx: 2
      });
    }
    const tip = document.createElementNS(ns, 'title');
    tip.textContent = `${x[i]}: ${format(v)}`;
    node.append(tip);

    // Visible numerical labels above points/bars for up to 16 data points
    if (x.length <= 16) {
      const isUp = py(v) <= py(0);
      const valY = isUp ? Math.max(38, py(v) - 8) : Math.min(235, py(v) + 14);
      add('text', {
        x: px,
        y: valY,
        'font-size': 10,
        'font-weight': '700',
        fill: v < 0 ? '#059669' : '#dc2626',
        'text-anchor': 'middle'
      }, format(v));
    }

    if (x.length <= 16 || i % Math.ceil(x.length / 10) === 0) {
      add('text', { x: px, y: 248, 'font-size': 10, fill: '#64748b', transform: `rotate(35 ${px} 248)` }, x[i]);
    }
  });
  return s;
}

function graphCard(title, x, y, line = false) {
  const c = el('div', null, 'card graph-container-card');
  c.style.padding = '20px';
  c.style.background = '#ffffff';
  c.style.borderRadius = '12px';
  c.style.border = '1px solid var(--border-color)';
  c.style.boxSizing = 'border-box';
  c.style.width = '100%';
  c.style.overflowX = 'hidden';

  const header = el('div');
  header.style.display = 'flex';
  header.style.justifyContent = 'space-between';
  header.style.alignItems = 'center';
  header.style.marginBottom = '12px';
  header.append(el('h3', title, 'card-title'));

  const svg = graph(title, x, y, line);
  const dlBtn = button('📥 차트 PNG 저장', () => {
    const u = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml;charset=utf-8' }));
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = 1480; canvas.height = 620;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, 1480, 620);
      ctx.drawImage(img, 0, 0, 1480, 620);
      URL.revokeObjectURL(u);
      const a = el('a');
      a.download = 'semiguard_chart.png';
      a.href = canvas.toDataURL('image/png');
      a.click();
    };
    img.src = u;
  }, 'action-btn');
  dlBtn.style.fontSize = '0.8rem';
  header.append(dlBtn);

  c.append(header, svg);
  return c;
}

function table(rows, keys = null, action = null) {
  if (!rows || !rows.length) return el('p', '해당하는 데이터가 없습니다.', 'muted');
  keys = keys || Object.keys(rows[0]);
  const wrap = el('div', null, 'table-scroll'), t = el('table'), head = el('tr');
  keys.forEach(k => head.append(el('th', labels[k] || k)));
  if (action) head.append(el('th', '작업'));
  const thead = el('thead');
  thead.append(head);
  t.append(thead);

  const tbody = el('tbody');
  rows.forEach(row => {
    const tr = el('tr');
    keys.forEach(k => {
      let val = row[k];
      let text = format(val);
      if (k.includes('failure_rate') || k.includes('ratio') || k === 'recall' || k === 'precision' || k === 'Lift') {
        if (typeof val === 'number') text = k === 'Lift' ? format(val) : pct(val);
      }
      const td = el('td', text);
      if (k === 'category') {
        const badgeClass = val === 'TP' ? 'danger' : val === 'FP' ? 'warning' : val === 'FN' ? 'danger' : 'success';
        td.replaceChildren(el('span', text, `risk-badge ${badgeClass}`));
      }
      tr.append(td);
    });
    if (action) {
      const td = el('td');
      td.append(action(row));
      tr.append(td);
    }
    tbody.append(tr);
  });
  t.append(tbody);
  wrap.append(t);
  return wrap;
}

function metricsCard(items) {
  const grid = el('div', null, 'metrics-summary-grid');
  grid.style.display = 'grid';
  grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(135px, 1fr))';
  grid.style.gap = '12px';
  grid.style.marginBottom = '20px';
  grid.style.width = '100%';
  grid.style.boxSizing = 'border-box';

  items.forEach(([name, value, note]) => {
    const m = el('div');
    m.style.background = '#ffffff';
    m.style.padding = '14px 18px';
    m.style.borderRadius = '10px';
    m.style.border = '1px solid var(--border-color)';
    m.style.boxShadow = 'var(--shadow-sm)';

    const labelEl = el('div', name);
    labelEl.style.fontSize = '0.78rem';
    labelEl.style.color = 'var(--text-sub)';
    labelEl.style.fontWeight = '700';

    const valEl = el('div', value);
    valEl.style.fontSize = '1.35rem';
    valEl.style.fontWeight = '900';
    valEl.style.color = '#0f172a';
    valEl.style.margin = '4px 0';

    const noteEl = el('div', note || '');
    noteEl.style.fontSize = '0.74rem';
    noteEl.style.color = '#64748b';

    m.append(labelEl, valEl, noteEl);
    grid.append(m);
  });
  return grid;
}

// Role Permissions Matrix (관리자와 엔지니어 모두 일상점검/예지보전 view-pdm 접근 및 관리 가능, 업로드/초기화 관리는 관리자 전용)
const ROLE_PERMISSIONS = {
  engineer: ['view-hub', 'view-triage', 'view-shap-summary', 'view-sim', 'view-pdm'],
  admin: ['view-hub', 'view-admin-yield', 'view-admin-perf', 'view-admin-confusion', 'view-admin-drift', 'view-admin-wiki', 'view-triage', 'view-pdm']
};

// Navigation System with Role Guard
window.navigateTo = function(viewId) {
  // Check role access
  const allowed = ROLE_PERMISSIONS[state.role] || ['view-hub'];
  if (!allowed.includes(viewId)) {
    const roleName = state.role === 'engineer' ? '현장 엔지니어' : '공정 관리자';
    const targetRole = state.role === 'engineer' ? '공정 관리자(Fab Manager)' : '현장 엔지니어';
    showToast(`⚠️ [접근 제한] '${viewId}' 화면은 ${targetRole} 전용 메뉴입니다. (${roleName} 권한 모드)`, true);
    viewId = 'view-hub';
  }

  // view-pdm 접근 시 현재 역할에 맞춰 실무자 모드 / 관리자 모드 자동 세팅
  if (viewId === 'view-pdm') {
    state.taskMode = (state.role === 'admin') ? 'admin' : 'engineer';
  }

  state.currentView = viewId;
  document.querySelectorAll('.view-screen').forEach(s => {
    s.style.display = (s.id === viewId) ? 'block' : 'none';
  });
  const backBtn = $('btn-back-hub');
  if (backBtn) backBtn.style.display = (viewId === 'view-hub') ? 'none' : 'inline-flex';
  window.scrollTo({ top: 0, behavior: 'smooth' });
  renderCurrentView();
};

window.switchRole = function(role) {
  state.role = role;
  state.taskMode = role;
  const engBtn = $('role-btn-engineer');
  const admBtn = $('role-btn-admin');
  if (engBtn) engBtn.classList.toggle('active', role === 'engineer');
  if (admBtn) admBtn.classList.toggle('active', role === 'admin');

  // 상단 글로벌 툴바 권한 분기: 업로드, 초기화, 가입 승인 버튼은 관리자(admin) 전용, 엔지니어는 숨김
  const topUploadBtn = $('btn-top-upload');
  const topResetBtn = $('btn-top-reset');
  const topApprovalBtn = $('btn-top-user-approval');
  if (topUploadBtn) topUploadBtn.style.display = (role === 'admin') ? 'inline-flex' : 'none';
  if (topResetBtn) topResetBtn.style.display = (role === 'admin') ? 'inline-flex' : 'none';
  if (topApprovalBtn) topApprovalBtn.style.display = (role === 'admin') ? 'inline-flex' : 'none';

  if (role === 'admin') {
    updatePendingBadge();
  }

  const engSec = $('hub-engineer-section');
  const admSec = $('hub-admin-section');
  const hubTitle = $('hub-title');
  const hubSubtitle = $('hub-subtitle');

  if (role === 'engineer') {
    // 현장 엔지니어 모드
    if (engSec) engSec.style.display = 'block';
    if (admSec) admSec.style.display = 'none';
    if (hubTitle) hubTitle.textContent = '🧑‍🏭 현장 엔지니어 전용 관제 센터';
    if (hubSubtitle) hubSubtitle.textContent = '실시간 웨이퍼 불량 진단, SHAP 원인 규명, 챔버 노후화 일상 점검표 및 실시간 스케줄을 관리합니다.';
  } else {
    // 공정 관리자 모드
    if (engSec) engSec.style.display = 'none';
    if (admSec) admSec.style.display = 'block';
    if (hubTitle) hubTitle.textContent = '👨‍💼 공정 관리자 전용 총괄 관제 센터';
    if (hubSubtitle) hubSubtitle.textContent = '전체 수율 트렌드, AI 모델 성과, 센서 드리프트 정밀 관제 및 현장 실무자 점검 보고서 최종 승인을 수행합니다.';
  }

  // 현재 화면이 바뀐 역할에서 허용되지 않으면 허브로 이동, 허용되면 재렌더링
  const allowed = ROLE_PERMISSIONS[role] || ['view-hub'];
  if (!allowed.includes(state.currentView)) {
    navigateTo('view-hub');
  } else {
    renderCurrentView();
  }
};

// Global Data Management
async function loadDatasetList(selectId = state.datasetId) {
  const d = await api('/api/datasets');
  const sel = $('dataset-select');
  sel.replaceChildren();

  const list = d.datasets || [];
  if (list.length > 0) {
    list.forEach(m => sel.add(new Option(`${m.filename} (${m.row_count}행)`, m.dataset_id)));
    const exists = list.some(m => m.dataset_id === selectId);
    state.datasetId = exists ? selectId : list[0].dataset_id;
    sel.value = state.datasetId;
  } else {
    state.datasetId = null;
    sel.add(new Option('등록된 데이터셋 없음', ''));
    sel.value = '';
  }
  return list;
}

function renderEmptyState() {
  const emptyHtml = `
    <div class="card" style="padding:48px 24px; text-align:center; background:#ffffff; border-radius:12px; border:1px solid var(--border-color); margin:20px 0;">
      <div style="font-size:3rem; margin-bottom:12px;">📂</div>
      <h3 style="font-size:1.25rem; font-weight:800; color:#0f172a; margin-bottom:8px;">현재 등록된 공정 데이터셋이 없습니다</h3>
      <p style="font-size:0.9rem; color:#64748b; max-width:540px; margin:0 auto 20px;">
        상단의 <strong>[📤 업로드]</strong> 버튼이나 아래 버튼을 눌러 테스트용 시뮬레이션 CSV를 업로드하거나 선택해 주세요.
      </p>
      <div style="display:flex; justify-content:center; gap:12px;">
        <button class="action-btn primary" onclick="navigateTo('view-admin-wiki')" style="padding:10px 20px;">
          <span>📂 CSV 업로드 및 시뮬레이션 관리로 이동</span>
        </button>
      </div>
    </div>
  `;
  ['triage-wafer-list', 'shap-summary-container', 'sim-fault-container', 'pdm-checklist-container', 'yield-chart-container', 'perf-curve-container', 'confusion-sample-table-wrapper', 'drift-table-container', 'dataset-quality-container'].forEach(id => {
    const el = $(id);
    if (el) el.innerHTML = emptyHtml;
  });
}

async function refreshGlobalData(resetPeriod = false) {
  if (!state.datasetId) {
    state.overviewData = null;
    const badge = $('status-summary-badge');
    if (badge) {
      badge.textContent = '📂 등록된 데이터셋 없음 · CSV를 업로드하거나 시뮬레이션을 선택해 주세요';
    }
    const periodSel = $('period-select');
    if (periodSel) periodSel.replaceChildren(new Option('데이터 없음', 'all'));
    renderEmptyState();
    return;
  }
  const epoch = ++state.epoch;
  ++state.diagnosticRequest;
  state.overviewData = null;
  if (resetPeriod) state.period = 'all';

  showToast('선택한 데이터셋과 기간의 전수 분석을 실계산하고 있습니다...');

  const d = await api(url('overview'));
  if (epoch !== state.epoch) return;
  state.overviewData = d;

  // Period dropdown update
  const periodSel = $('period-select');
  const periodOpts = [
    ['all', '전체 기간'],
    ...Array.from(new Set(d.periods.map(p => p.slice(0, 4)))).map(y => [y, `${y}년 연간`]),
    ...d.periods.map(p => [p, p]),
    ['recent7', '최근 7일 · 마지막 관측일 기준'],
    ['recent30', '최근 30일 · 마지막 관측일 기준']
  ];
  periodSel.replaceChildren(...periodOpts.map(([v, t]) => new Option(t, v)));
  periodSel.value = state.period;

  // Status Summary Badge
  const badge = $('status-summary-badge');
  if (badge) {
    badge.textContent = `📁 ${d.metadata.filename} · ${d.profile.row_count}행 · 기간: ${state.period} · 검토: ${(state.ratio * 100).toFixed(0)}%`;
  }

  // Update Download Links
  $('link-download-report').href = url('report');
  $('link-download-csv').href = url('export');
  $('link-view-json').href = `/api/datasets/${state.datasetId}/report`;

  // Assistant Scope Info
  $('assistant-scope-info').textContent = `${d.metadata.filename} · ${state.period} · Tool 실시간 호출`;

  showToast('공정 관제 데이터가 성공적으로 갱신되었습니다.');
  renderCurrentView();
}

// Main View Dispatcher
async function renderCurrentView() {
  if (!state.overviewData) return;
  const v = state.currentView;
  if (v === 'view-triage') await renderTriage();
  else if (v === 'view-shap-summary') await renderShapSummary();
  else if (v === 'view-sim') await renderSim();
  else if (v === 'view-pdm') await renderPdm();
  else if (v === 'view-admin-yield') renderYield();
  else if (v === 'view-admin-perf') renderPerf();
  else if (v === 'view-admin-confusion') renderConfusion();
  else if (v === 'view-admin-drift') await renderDrift();
  else if (v === 'view-admin-wiki') renderDataQuality();
}

// SCREEN 1: ⚡ 초고속 불량 센서 진단실 (Wafer Triage)
async function renderTriage() {
  const d = state.overviewData;
  if (!d || !d.rows || !d.rows.length) return;
  const presetsContainer = $('triage-presets');
  presetsContainer.replaceChildren(el('span', '🚨 긴급 점검 표본 바로가기: ', 'muted'));

  const rows = d.rows;
  // 상위 위험도 1위~5위 웨이퍼 우선 추출
  const topRisks = rows.slice(0, 5);
  const tp = rows.find(r => r.category === 'TP');
  const fp = rows.find(r => r.category === 'FP');
  const fn = rows.find(r => r.category === 'FN');
  const picks = [...topRisks, tp, fp, fn].filter(Boolean);

  const uniquePicks = Array.from(new Map(picks.map(r => [r.sample_id, r])).values());
  uniquePicks.forEach(r => {
    const isTop1 = r === rows[0];
    const b = button(`웨이퍼 #${r.sample_id} (위험 #${r.risk_rank}위 · ${(r.risk_score * 100).toFixed(1)}%)`, () => diagnoseWafer(r.sample_id));
    b.className = `action-btn ${isTop1 ? 'primary' : ''}`;
    b.style.fontSize = '0.78rem';
    b.style.padding = '4px 10px';
    presetsContainer.append(b);
  });

  const currentInput = $('sample-search-input').value.trim();
  const targetSample = rows.find(r => String(r.sample_id) === currentInput) || rows[0];
  if (targetSample) {
    await diagnoseWafer(String(targetSample.sample_id));
  }
}

async function diagnoseWafer(sampleId) {
  if (!state.overviewData) return;
  sampleId = String(sampleId).trim();
  $('sample-search-input').value = sampleId;

  const container = $('triage-result-container');
  container.innerHTML = '<p style="padding:40px 0; text-align:center; color:#64748b;">실제 TreeExplainer SHAP 및 정상군 편차를 계산 중입니다...</p>';

  const exists = state.overviewData.rows.some(r => String(r.sample_id) === sampleId);
  if (!exists) {
    showToast(`표본 ${sampleId}는 현재 관제 기간(${state.period})에 포함되어 있지 않습니다.`, true);
    container.innerHTML = `<p style="padding:30px; text-align:center; color:var(--danger);">표본 ${sampleId}는 현재 관제 기간(${state.period})에 없습니다. 위의 빠른 선택 표본을 이용하십시오.</p>`;
    return;
  }

  const reqId = ++state.diagnosticRequest;
  const epoch = state.epoch;

  await busy($('btn-triage-search'), async () => {
    const sampleData = await api(url('sample', { sample_id: sampleId }));
    if (epoch !== state.epoch || reqId !== state.diagnosticRequest) return;

    container.replaceChildren(
      window.SemiDiagnostics.render(sampleData, {
        compact: false,
        onQuestion: q => {
          openAssistant(q);
        },
        onInspection: d => {
          openNewTaskDialog(d);
        }
      })
    );
  });
}

$('triage-search-form').onsubmit = e => {
  e.preventDefault();
  diagnoseWafer($('sample-search-input').value.trim());
};

// SCREEN 2: 🧠 SHAP 원인 분석 요약 & 1:1 비교
async function renderShapSummary() {
  const d = state.overviewData;
  const tpSel = $('shap-tp-select');
  const fpSel = $('shap-fp-select');

  const tpRows = d.rows.filter(r => r.category === 'TP');
  const fpRows = d.rows.filter(r => r.category === 'FP');

  tpSel.replaceChildren(...tpRows.map(r => new Option(`TP 표본 #${r.sample_id} (위험도 ${pct(r.risk_score)})`, r.sample_id)));
  if (!tpRows.length) tpSel.add(new Option('현재 기간에 TP 표본 없음', ''));

  fpSel.replaceChildren(...fpRows.map(r => new Option(`FP 표본 #${r.sample_id} (위험도 ${pct(r.risk_score)})`, r.sample_id)));
  if (!fpRows.length) fpSel.add(new Option('현재 기간에 FP 표본 없음', ''));

  await runCompareShap();
}

async function runCompareShap() {
  const tpId = $('shap-tp-select').value;
  const fpId = $('shap-fp-select').value;
  const container = $('shap-comparison-results');
  container.innerHTML = '<p style="padding:20px 0; text-align:center; color:#64748b;">두 표본의 SHAP 기여도를 불러오는 중입니다...</p>';

  const [tpData, fpData] = await Promise.all([
    tpId ? api(url('sample', { sample_id: tpId })).catch(() => null) : null,
    fpId ? api(url('sample', { sample_id: fpId })).catch(() => null) : null
  ]);

  container.replaceChildren();
  const grid = el('div', null, 'shap-comparison-grid');
  if (state.shapMode !== 'both') {
    grid.classList.add('single-column');
  }

  if (state.shapMode !== 'fp') {
    const cardTp = el('div', null, 'card shap-compare-card');
    cardTp.style.padding = '18px';
    cardTp.style.background = '#ffffff';
    cardTp.style.borderRadius = '12px';
    cardTp.style.border = '1px solid var(--border-color)';
    cardTp.style.boxSizing = 'border-box';
    cardTp.style.width = '100%';
    cardTp.append(el('h3', '🚨 진짜 불량 표본 (TP) 원인 분해', 'card-title'));
    if (tpData) cardTp.append(window.SemiDiagnostics.render(tpData, { compact: true }));
    else cardTp.append(el('p', '선택된 TP 표본이 없습니다.', 'muted'));
    grid.append(cardTp);
  }

  if (state.shapMode !== 'tp') {
    const cardFp = el('div', null, 'card shap-compare-card');
    cardFp.style.padding = '18px';
    cardFp.style.background = '#ffffff';
    cardFp.style.borderRadius = '12px';
    cardFp.style.border = '1px solid var(--border-color)';
    cardFp.style.boxSizing = 'border-box';
    cardFp.style.width = '100%';
    cardFp.append(el('h3', '⚠️ 가양성 안전마진 표본 (FP) 원인 분해', 'card-title'));
    if (fpData) cardFp.append(window.SemiDiagnostics.render(fpData, { compact: true }));
    else cardFp.append(el('p', '선택된 FP 표본이 없습니다.', 'muted'));
    grid.append(cardFp);
  }
  container.append(grid);
}

$('btn-compare-shap').onclick = () => busy($('btn-compare-shap'), runCompareShap);

$('btn-shap-mode-both').onclick = () => { setShapMode('both'); };
$('btn-shap-mode-tp').onclick = () => { setShapMode('tp'); };
$('btn-shap-mode-fp').onclick = () => { setShapMode('fp'); };

function setShapMode(mode) {
  state.shapMode = mode;
  $('btn-shap-mode-both').classList.toggle('active', mode === 'both');
  $('btn-shap-mode-tp').classList.toggle('active', mode === 'tp');
  $('btn-shap-mode-fp').classList.toggle('active', mode === 'fp');
  runCompareShap();
}

// Global SHAP
$('btn-run-global-shap').onclick = () => busy($('btn-run-global-shap'), async () => {
  const container = $('global-shap-container');
  container.innerHTML = '<p style="padding:20px 0; text-align:center; color:#64748b;">선택 기간 전수 200행 균등 샘플링 Global SHAP을 계산 중입니다...</p>';
  const r = await post(`/api/dashboard/${state.datasetId}/tools/global_shap`, {
    period: state.period,
    ratio: state.ratio,
    arguments: { limit: 15, max_samples: 200 }
  });
  const d = r.data;
  const wrap = el('div');
  wrap.style.marginTop = '16px';
  wrap.append(
    el('p', `선택 범위 ${d.scope_count}행 중 ${d.analyzed_count}행 분석 · ${d.sampling}`, 'muted'),
    graph('평균 절대 SHAP 중요도 (Top 15)', d.rows.map(x => x.feature), d.rows.map(x => x.mean_abs_shap)),
    table(d.rows, ['rank', 'feature', 'mean_abs_shap']),
    el('p', d.note, 'muted')
  );
  container.replaceChildren(wrap);
});

// SCREEN 3: 🧪 가상 센서 결함 주입 & 배치 추론
async function renderSim() {
  const sel = $('sim-file-select');
  try {
    const data = await api('/api/simulation');
    sel.replaceChildren(...data.files.map(f => new Option(`${f.filename} (${(f.bytes / 1024).toFixed(0)} KB)`, f.filename)));
  } catch (err) {
    console.error(err);
  }
}

$('btn-run-sim-batch').onclick = () => busy($('btn-run-sim-batch'), async () => {
  const filename = $('sim-file-select').value;
  if (!filename) return;
  showToast(`시뮬레이션 파일 ${filename} 추론을 시작합니다...`);
  const result = await post(`/api/simulation/${encodeURIComponent(filename)}/analyze`, {});
  await loadDatasetList(result.dataset_id);
  await refreshGlobalData(true);

  // Fill preview table
  const tbody = $('sim-batch-tbody');
  tbody.replaceChildren();
  const rows = state.overviewData.rows.slice(0, 15);
  $('sim-batch-count').textContent = `총 ${state.overviewData.rows.length}행 중 상위 15건`;

  rows.forEach(r => {
    const tr = el('tr');
    tr.innerHTML = `
      <td><b>#${r.sample_id}</b> <span style="font-size:0.75rem; color:#64748b;">(${r.timestamp || ''})</span></td>
      <td><span class="brand-tag">${r.risk_rank}위</span></td>
      <td><b>${pct(r.risk_score)}</b></td>
      <td>${r.is_top20_review ? '<span class="risk-badge danger">🚨 우선검토</span>' : '일반'}</td>
      <td>${r.actual_label === 1 ? '<b style="color:var(--danger);">불량 (1)</b>' : '정상 (0)'}</td>
      <td><button class="action-btn" style="padding:3px 10px; font-size:0.78rem;" onclick="navigateTo('view-triage'); diagnoseWafer('${r.sample_id}');">🔍 진단</button></td>
    `;
    tbody.append(tr);
  });
  showToast(`✅ ${filename} 배치 추론 완료! 상위 순위가 도출되었습니다.`);
});

// Fault Injections
$('btn-inject-489').onclick = () => {
  state.faultInjected = 'feature_489_dropout';
  showToast('⚡ [실험 1] feature_489 센서 단선(0.0V) 결함이 인위 주입되었습니다! [초고속 진단실]로 이동합니다.');
  setTimeout(() => {
    navigateTo('view-triage');
    diagnoseWafer('1254');
  }, 600);
};

$('btn-inject-512').onclick = () => {
  state.faultInjected = 'feature_512_surge';
  showToast('⚡ [실험 2] feature_512 센서 과전압(+800V) 결함이 인위 주입되었습니다! [초고속 진단실]로 이동합니다.');
  setTimeout(() => {
    navigateTo('view-triage');
    diagnoseWafer('1254');
  }, 600);
};

$('btn-reset-fault').onclick = () => {
  state.faultInjected = null;
  showToast('🔄 가상 결함이 정상 초기화되었습니다.');
};

// SCREEN 4: 🛠️ 챔버 노후화 일상 점검표 & 실시간 점검 스케줄
const PDM_SENSOR_KNOWLEDGE = {
  feature_104: {
    chamber: 'Dry Etch 식각 챔버',
    title: 'Dry Etch 건식 식각 챔버 하부 전극/포커스링 마모 진단 지침',
    reason: '센서 급락 및 RF 임피던스 이탈 (-1.73σ)',
    items: ['feature_104와 feature_60 센서의 하강 드리프트(-99.1%)는 포커스 링 마모와 관련 있습니다. 주 1회 RF 매처 영점 보정 및 마모 한계 도달 시 하부 전극 교체를 진행하세요.'],
    sampleNotes: '포커스링 마모 두께 0.95mm 확인되어 예비품(새 링)으로 긴급 교체 완료함. RF Matcher 영점 튜닝 후 센서 전압 정상 복귀 확인.'
  },
  feature_60: {
    chamber: 'Dry Etch 식각 챔버 1호기',
    title: 'Dry Etch 챔버 RF 제너레이터 출력 전압 및 플라즈마 임피던스 점검',
    reason: 'RF 출력 레벨 급락 (-0.54σ, 정상대비 60.1% 축소)',
    items: ['RF Matcher 튜닝 커패시터 오염 상태 점검 및 동축 케이블 반사파(Reflected Power) 계측 후 캘리브레이션 실시.'],
    sampleNotes: 'RF Matcher 튜닝 커패시터 이물질 세정 및 반사파 0.2W 이하 정상 매칭 확인.'
  },
  feature_34: {
    chamber: 'CVD 증착 챔버 1호기',
    title: 'CVD 증착 챔버 가스 공급 라인 MFC 밸브 유량 편차 점검',
    reason: '가스 공급 유량 센서 표준편차 폭증 (+166.8% 변동성)',
    items: ['SiH4 / N2O 주입 MFC 밸브 오리피스 막힘 검사 및 유량 압력 센서 재영점 조정.'],
    sampleNotes: 'MFC 밸브 오리피스 퍼지 세정 후 가스 유량 표준편차 허용치(±2%) 이내 복구 완료.'
  },
  feature_29: {
    chamber: 'CMP 연마 설비 3호기',
    title: 'CMP 화학기계적 연마 패드 마모 및 슬러리 공급 라인 노즐 점검',
    reason: '연마 헤드 압력 센서 드리프트 (+0.20σ 이탈)',
    items: ['연마 헤드 리테이너 링 마모도 측정(허용공차 0.05mm) 및 슬러리 디스펜서 노즐 막힘 제거.'],
    sampleNotes: '리테이너 링 마모 한계 도달 확인되어 신규 부품 교체 완료. 연마 압력 균일도 99.4% 확인.'
  }
};

async function renderPdm() {
  let d = await api(`/api/dashboard/${state.datasetId}/inspections`);
  
  // 만약 등록된 점검 지시가 0건이면 두 번째 그림의 기본 지침(Dry Etch 포커스링 마모)을 자동 등록
  if (!d.tasks || d.tasks.length === 0) {
    try {
      const defaultTask = await post(`/api/dashboard/${state.datasetId}/inspections`, {
        title: PDM_SENSOR_KNOWLEDGE.feature_104.title,
        chamber: PDM_SENSOR_KNOWLEDGE.feature_104.chamber,
        urgency: '긴급',
        reason: PDM_SENSOR_KNOWLEDGE.feature_104.reason,
        items: PDM_SENSOR_KNOWLEDGE.feature_104.items,
        period: state.period || 'all'
      });
      d.tasks = [defaultTask];
    } catch (err) {
      console.warn('초기 시드 점검 지시 자동 생성 실패:', err);
    }
  }

  // 상단 역할 모드 뱃지 및 관리자 전용 버튼 제어 (실무자 모드에서는 발령/관리자 버튼 완전 숨김)
  const roleBadge = $('pdm-role-badge');
  const adminOnlyActions = $('pdm-admin-only-actions');
  if (roleBadge) {
    if (state.role === 'admin') {
      roleBadge.textContent = '👨‍💼 공정 관리자 모드';
      roleBadge.style.background = '#eff6ff';
      roleBadge.style.color = '#2563eb';
      roleBadge.style.borderColor = '#bfdbfe';
      if (adminOnlyActions) adminOnlyActions.style.display = 'inline-flex';
    } else {
      roleBadge.textContent = '👷 현장 실무자 모드';
      roleBadge.style.background = '#ecfdf5';
      roleBadge.style.color = '#059669';
      roleBadge.style.borderColor = '#a7f3d0';
      if (adminOnlyActions) adminOnlyActions.style.display = 'none';
    }
  }

  // 실시간 설비 노후화 점검 스케줄 파이프라인 렌더링
  renderPdmSchedule(d.tasks || []);

  const openTasks = (d.tasks || []).filter(t => t.status !== 'approved');
  const container = $('tasks-container');

  if (!openTasks.length) {
    container.innerHTML = `
      <div class="card" style="padding:36px; text-align:center; background:#ffffff; border-radius:12px; border:1px solid #e2e8f0;">
        <span style="font-size:2rem; display:block; margin-bottom:8px;">✅</span>
        <div style="font-size:1.05rem; font-weight:700; color:#0f172a; margin-bottom:6px;">현재 진행 대기 중인 점검 지시가 없습니다.</div>
        <p style="font-size:0.86rem; color:#64748b; margin:0;">
          공정 관리자 화면(3대 다면 통계 센서 드리프트 관제)에서 설비 이상 센서의 <b>[🛠️ 점검 발령]</b> 버튼을 누르면 실시간으로 전달됩니다.
        </p>
      </div>`;
  } else {
    container.replaceChildren(...openTasks.map(task => renderTaskCard(task)));
  }

  // 최종 승인 완료 이력 보관함
  const historyContainer = $('task-history-container');
  const approvedTasks = (d.tasks || []).filter(t => t.status === 'approved');
  if (!approvedTasks.length) {
    historyContainer.innerHTML = '<p style="color:#64748b; font-size:0.86rem; margin:0; padding:10px 0;">승인 완료된 이력이 없습니다.</p>';
  } else {
    historyContainer.replaceChildren(...approvedTasks.map(task => renderTaskCard(task)));
  }
}

// 📅 실시간 설비 노후화 점검 스케줄 파이프라인 위젯
function renderPdmSchedule(tasks) {
  const container = $('pdm-schedule-pipeline');
  if (!container) return;

  const total = tasks.length;
  const countOpen = tasks.filter(t => t.status === 'open').length;
  const countReported = tasks.filter(t => t.status === 'reported').length;
  const countApproved = tasks.filter(t => t.status === 'approved').length;

  const steps = [
    {
      step: 1,
      name: '1. 긴급 점검 발령',
      count: countOpen,
      icon: '🚨',
      color: '#dc2626',
      bg: '#fef2f2',
      border: '#fca5a5',
      desc: '관리자 센서 드리프트 지시 접수',
      active: countOpen > 0
    },
    {
      step: 2,
      name: '2. 현장 실사 & 점검',
      count: countOpen,
      icon: '🛠️',
      color: '#d97706',
      bg: '#fffbeb',
      border: '#fde68a',
      desc: '실무자 체크리스트 실측 중',
      active: countOpen > 0
    },
    {
      step: 3,
      name: '3. 관리자 승인 대기',
      count: countReported,
      icon: '📋',
      color: '#2563eb',
      bg: '#eff6ff',
      border: '#bfdbfe',
      desc: '조치 소견서 제출 완료',
      active: countReported > 0
    },
    {
      step: 4,
      name: '4. 최종 승인 & 가동',
      count: countApproved,
      icon: '✅',
      color: '#059669',
      bg: '#ecfdf5',
      border: '#a7f3d0',
      desc: '설비 가동 승인 완료',
      active: countApproved > 0
    }
  ];

  container.replaceChildren(...steps.map(s => {
    const card = el('div', null, `pipeline-step-card ${s.active ? 'active' : ''}`);
    card.style.background = s.active ? s.bg : '#f8fafc';
    card.style.borderColor = s.active ? s.border : '#e2e8f0';

    card.innerHTML = `
      <div class="pipeline-step-header">
        <span class="pipeline-step-title" style="color:${s.color};">
          ${s.icon} ${s.name}
        </span>
        <span class="pipeline-step-count" style="color:${s.color};">${s.count}건</span>
      </div>
      <div class="pipeline-step-desc">${s.desc}</div>
      <div style="margin-top:8px; height:4px; background:#e2e8f0; border-radius:2px; overflow:hidden;">
        <div style="height:100%; width:${total ? (s.count / total * 100) : 0}%; background:${s.color};"></div>
      </div>
    `;
    return card;
  }));
}

// 🛠️ 점검 카드 렌더링 (두 번째 그림과 100% 동일한 비주얼 구조)
function renderTaskCard(task) {
  const card = el('div', null, 'pdm-task-card');

  // 1. 카드 상단 뱃지 및 타이틀 헤더
  const topHeader = el('div');
  const dateStr = task.created_at ? task.created_at.slice(0, 10) : '2026-10-15';

  const badgeUrgent = el('div', null, 'pdm-task-badge-urgent');
  badgeUrgent.innerHTML = `<span>🚨 [긴급] 센서 드리프트 기반 점검 발령</span>`;

  const titleEl = el('h3', task.title, 'pdm-task-title');
  const metaEl = el('div', `발령: ${dateStr} | 관리자: 공정 관리자 (센서 드리프트 실시간 연계)`, 'pdm-task-meta');

  topHeader.append(badgeUrgent, titleEl, metaEl);
  card.append(topHeader);

  // 2. 2열 정보 박스 (대상 설비/챔버 & AI 진단 사유)
  const grid2Col = el('div', null, 'pdm-grid-2col');

  // 좌측 박스: 대상 설비/챔버
  const chamberBox = el('div', null, 'pdm-info-box');
  chamberBox.innerHTML = `
    <div class="pdm-info-label">대상 설비/챔버</div>
    <div class="pdm-info-value-chamber">⚙️ ${task.chamber}</div>
  `;

  // 우측 박스: AI 진단 사유 및 이상 징후
  const reasonBox = el('div', null, 'pdm-info-box');
  reasonBox.innerHTML = `
    <div class="pdm-info-label">AI 진단 사유 및 이상 징후</div>
    <div class="pdm-info-value-reason">🔍 센서 드리프트 연계 (${task.reason})</div>
  `;

  grid2Col.append(chamberBox, reasonBox);
  card.append(grid2Col);

  // 3. 현장 실무자 점검 체크리스트
  const checklistSection = el('div');
  checklistSection.style.marginBottom = '20px';

  const checklistHeading = el('div', '📋 현장 실무자 점검 체크리스트 (점검 후 체크하여 주십시오)', 'pdm-section-heading');
  checklistSection.append(checklistHeading);

  const checkboxes = [];
  (task.items || []).forEach((item, idx) => {
    const checkRow = el('div', null, 'pdm-check-item');
    const ch = el('input');
    ch.type = 'checkbox';
    ch.id = `check-${task.id}-${idx}`;
    ch.checked = Boolean(task.checked && task.checked[idx]);
    ch.disabled = task.status !== 'open';

    const lbl = el('label', item, 'pdm-check-text');
    lbl.htmlFor = ch.id;
    lbl.style.cursor = task.status === 'open' ? 'pointer' : 'default';

    checkRow.append(ch, lbl);
    checklistSection.append(checkRow);
    checkboxes.push(ch);
  });
  card.append(checklistSection);

  // 4. 실무자 현장 조치 소견 입력 및 관리자 승인 영역
  if (task.status === 'open') {
    // [현장 실무자 점검 진행 중]
    const notesSection = el('div');

    const notesHeading = el('div', null, 'pdm-section-heading');
    notesHeading.innerHTML = `
      <span>✍️ 실무자 현장 조치 소견 및 세부 결과 기록 (관리자 보고용)</span>
    `;

    // 예시 소견 자동 완성 버튼
    const autoFillBtn = button('💡 추천 소견 채우기', () => {
      const match = Object.values(PDM_SENSOR_KNOWLEDGE).find(k => task.title.includes(k.chamber) || task.reason.includes(k.reason) || task.chamber.includes(k.chamber));
      textarea.value = match ? match.sampleNotes : '포커스링 마모 두께 0.95mm 확인되어 예비품(새 링)으로 긴급 교체 완료함. RF Matcher 영점 튜닝 후 센서 전압 정상 복귀 확인.';
      checkboxes.forEach(c => c.checked = true);
    }, 'action-btn');
    autoFillBtn.style.fontSize = '0.76rem';
    autoFillBtn.style.padding = '3px 10px';
    notesHeading.append(autoFillBtn);
    notesSection.append(notesHeading);

    const textarea = el('textarea', null, 'pdm-notes-textarea');
    textarea.placeholder = '예: 포커스링 마모 두께 0.95mm 확인되어 예비품(새 링)으로 긴급 교체 완료함. RF Matcher 영점 튜닝 후 센서 전압 정상 복귀 확인.';
    textarea.value = task.notes || '';
    notesSection.append(textarea);

    // 하단 푸터 (안내 문구 + 제출 버튼)
    const footer = el('div', null, 'pdm-card-footer');
    const noticeEl = el('span', '※ 제출 시 관리자 승인 대기 상태로 전환되며, 관리자 승인 완료 시 실무자 화면에서 정리됩니다.', 'pdm-footer-notice');

    const submitBtn = el('button', null, 'pdm-submit-btn');
    submitBtn.innerHTML = `<span>💾 점검 완료 보고서 제출 (관리자 승인 요청) ➔</span>`;
    submitBtn.onclick = async () => {
      // 체크박스 검증
      const allChecked = checkboxes.every(c => c.checked);
      if (!allChecked) {
        showToast('⚠️ 점검 체크리스트의 모든 항목을 확인하고 체크해 주십시오.', true);
        return;
      }
      const noteVal = textarea.value.trim();
      if (!noteVal) {
        showToast('⚠️ 실무자 현장 조치 소견 및 세부 결과를 입력해 주십시오.', true);
        return;
      }

      await busy(submitBtn, async () => {
        await post(`/api/dashboard/inspections/${task.id}/submit`, {
          checked: checkboxes.map(c => c.checked),
          notes: noteVal
        });
        showToast('✅ 점검 완료 보고서가 성공적으로 제출되었습니다! 공정 관리자 승인 대기 상태로 전환됩니다.');
        await renderPdm();
      });
    };

    footer.append(noticeEl, submitBtn);
    notesSection.append(footer);
    card.append(notesSection);

  } else if (task.status === 'reported') {
    // [관리자 승인 대기 중]
    const reportBox = el('div');
    reportBox.style.background = '#f0f9ff';
    reportBox.style.border = '1px solid #bae6fd';
    reportBox.style.borderRadius = '10px';
    reportBox.style.padding = '18px 20px';
    reportBox.style.marginTop = '10px';

    reportBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-size:0.88rem; font-weight:800; color:#0369a1;">📋 실무자 현장 조치 완료 보고서 (승인 대기)</span>
        <span class="brand-tag" style="background:#eff6ff; color:#2563eb; border-color:#93c5fd; font-weight:700;">승인 대기</span>
      </div>
      <div style="font-size:0.9rem; color:#1e293b; line-height:1.6; background:#ffffff; padding:12px 14px; border-radius:6px; border:1px solid #e2e8f0;">
        <b>현장 조치 소견:</b> ${task.notes || '소견 없음'}
      </div>
    `;

    // 관리자 모드인 경우 승인/보완 버튼 노출
    if (state.taskMode === 'admin') {
      const adminActions = el('div');
      adminActions.style.display = 'flex';
      adminActions.style.gap = '12px';
      adminActions.style.marginTop = '14px';
      adminActions.style.justifyContent = 'flex-end';

      const approveBtn = button('✅ 최종 승인 완료 (설비 가동 승인)', async () => {
        await busy(approveBtn, async () => {
          await post(`/api/dashboard/inspections/${task.id}/approve`, {});
          showToast('✅ 점검 보고서가 최종 승인되었습니다! 설비 가동이 정상 허가되었습니다.');
          await renderPdm();
        });
      }, 'action-btn primary');
      approveBtn.style.padding = '10px 20px';
      approveBtn.style.fontWeight = '700';

      const reopenBtn = button('↩️ 재실사/보완 요청', async () => {
        await busy(reopenBtn, async () => {
          await post(`/api/dashboard/inspections/${task.id}/reopen`, {
            review_note: '실측 센서 수치 및 영점 재점검 요망'
          });
          showToast('점검 지시가 보완 요청으로 실무자에게 재발령되었습니다.');
          await renderPdm();
        });
      }, 'action-btn');
      reopenBtn.style.padding = '10px 16px';

      adminActions.append(reopenBtn, approveBtn);
      reportBox.append(adminActions);
    } else {
      const waitNotice = el('div', '⌛ 공정 관리자가 조치 소견을 검토 중입니다. 관리자 승인 완료 시 보관함으로 이동합니다.', 'muted');
      waitNotice.style.marginTop = '10px';
      waitNotice.style.fontSize = '0.82rem';
      reportBox.append(waitNotice);
    }
    card.append(reportBox);

  } else if (task.status === 'approved') {
    // [최종 승인 완료]
    const approvedBox = el('div');
    approvedBox.style.background = '#f0fdf4';
    approvedBox.style.border = '1px solid #bbf7d0';
    approvedBox.style.borderRadius = '10px';
    approvedBox.style.padding = '16px 20px';
    approvedBox.style.marginTop = '10px';

    approvedBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-size:0.88rem; font-weight:800; color:#15803d;">✅ 관리자 최종 승인 완료 (설비 정상 가동)</span>
        <span class="brand-tag" style="background:#ecfdf5; color:#059669; border-color:#a7f3d0; font-weight:700;">승인 완료</span>
      </div>
      <div style="font-size:0.86rem; color:#166534; line-height:1.5;">
        <b>최종 소견:</b> ${task.notes || '정상 처리'}
      </div>
    `;
    card.append(approvedBox);
  }

  return card;
}

// Modal: New Task
function openNewTaskDialog(initial = null) {
  if (initial) {
    if (initial.sensor && PDM_SENSOR_KNOWLEDGE[initial.sensor]) {
      const k = PDM_SENSOR_KNOWLEDGE[initial.sensor];
      $('task-title-input').value = k.title;
      $('task-chamber-input').value = k.chamber;
      $('task-urgency-select').value = '긴급';
      $('task-reason-textarea').value = `${k.reason} (${initial.sensor} 평균 이동: ${format(initial.shift_std)}σ)`;
      $('task-items-textarea').value = k.items.join('\n');
    } else if (initial.recommendation) {
      $('task-title-input').value = initial.recommendation.title || `${initial.sensor || '센서'} 정밀 점검 지침`;
      $('task-chamber-input').value = initial.chamber || 'Dry Etch 식각 챔버';
      $('task-urgency-select').value = '긴급';
      $('task-reason-textarea').value = initial.summary || `${initial.sensor || '공정 센서'} 이상 편차 발생`;
      $('task-items-textarea').value = (initial.recommendation.checks || []).join('\n');
    } else if (initial.summary) {
      $('task-title-input').value = `설비 노후화 이상 점검 지침`;
      $('task-chamber-input').value = 'Dry Etch 식각 챔버';
      $('task-urgency-select').value = '긴급';
      $('task-reason-textarea').value = initial.summary;
      $('task-items-textarea').value = '설비 주요 센서 전압 및 영점 캘리브레이션 수행\n커넥터 접촉 저항 및 이물질 오염 상태 점검';
    }
  }
  $('new-task-dialog').showModal();
}

$('btn-open-new-task').onclick = () => openNewTaskDialog();
$('btn-close-new-task').onclick = () => $('new-task-dialog').close();

$('new-task-form').onsubmit = e => {
  e.preventDefault();
  busy(e.submitter, async () => {
    const chamberName = $('task-chamber-input').value.trim() || 'Dry Etch 식각 챔버';
    await post(`/api/dashboard/${state.datasetId}/inspections`, {
      title: $('task-title-input').value.trim(),
      chamber: chamberName,
      urgency: $('task-urgency-select').value,
      reason: $('task-reason-textarea').value.trim(),
      items: $('task-items-textarea').value.split('\n').map(s => s.trim()).filter(Boolean),
      period: state.period || 'all'
    });
    $('new-task-dialog').close();
    showToast(`🚨 [${chamberName}] 점검 지시가 성공적으로 발령되었습니다! 현장 실무자 점검표로 즉시 전달되었습니다.`);
    if (state.currentView === 'view-admin-drift') {
      await renderAdminPdmReview();
    } else {
      navigateTo('view-pdm');
      await renderPdm();
    }
  });
};

// SCREEN 5: 📈 7일 롤링 이동평균 & 월별 수율 트렌드
function renderYield() {
  const d = state.overviewData;
  const container = $('yield-charts-container');
  container.replaceChildren();

  const rolling = d.rolling.rows || [];
  const monthly = d.time_summary.rows || [];

  const chartRolling = graphCard(
    '7일 롤링 이동평균 불량률 (%)',
    rolling.map(r => r.day),
    rolling.map(r => r.rolling_failure_rate == null ? null : r.rolling_failure_rate * 100),
    true
  );
  chartRolling.append(table(rolling, ['day', 'count', 'known', 'failures', 'rolling_failure_rate']));

  const chartMonthly = graphCard(
    '월별 확인 라벨 불량률 (%)',
    monthly.map(r => r.period),
    monthly.map(r => r.confirmed_failure_rate == null ? null : r.confirmed_failure_rate * 100),
    true
  );
  chartMonthly.append(table(monthly, ['period', 'count', 'known_label_count', 'confirmed_failures', 'confirmed_failure_rate'], r => {
    return button('이 월 관제', () => {
      state.period = r.period;
      $('period-select').value = r.period;
      refreshGlobalData();
    }, 'action-btn');
  }));

  container.append(chartRolling, chartMonthly);
}

// SCREEN 6: 🎯 AI 모델 종합 성과 (우선검토 성과곡선)
function renderPerf() {
  const d = state.overviewData;
  const metricsBox = $('perf-metrics-container');
  metricsBox.replaceChildren(metricsCard([
    ['Average Precision', format(d.metrics.average_precision), '실제 정답 및 위험 점수 기준'],
    ['전체 관제 표본', format(d.profile.row_count) + '매', '선택된 관제 기간'],
    ['확인 불량 표본', format(d.profile.confirmed_failures) + '매', `라벨 확인: ${d.profile.known_label_count}매`],
    ['우선 검토 비율', pct(state.ratio), `선정: ${d.metrics.selected_count || 0}매`]
  ]));

  const matrixBox = $('perf-matrix-container');
  matrixBox.replaceChildren(renderMatrixCard(d.metrics));

  const curveBox = $('perf-curve-container');
  const cardCurve = el('div', null, 'card');
  cardCurve.style.padding = '20px';
  cardCurve.style.background = '#ffffff';
  cardCurve.style.borderRadius = '12px';
  cardCurve.style.border = '1px solid var(--border-color)';
  cardCurve.append(
    el('h3', '📊 우선 검토 비율별 (5% ~ 50%) 불량 검출 시뮬레이션 성과표', 'card-title'),
    table(d.review_curve.filter(m => m.status === 'available').map(m => ({
      '검토 비율': pct(m.review_ratio),
      '선정 표본': m.selected_count,
      '발견 불량': m.TP,
      Recall: pct(m.recall),
      Precision: pct(m.precision),
      Lift: m.lift
    })))
  );
  curveBox.replaceChildren(cardCurve);
}

function renderMatrixCard(m) {
  const c = el('div', null, 'card');
  c.style.padding = '20px';
  c.style.background = '#ffffff';
  c.style.borderRadius = '12px';
  c.style.border = '1px solid var(--border-color)';
  c.append(el('h3', '🔲 선택 기간 혼동행렬 (Confusion Matrix)', 'card-title'));

  if (m.status !== 'available') {
    c.append(el('p', m.reason || '라벨이 부족하여 혼동행렬을 계산할 수 없습니다.', 'muted'));
    return c;
  }

  c.append(
    metricsCard([
      ['우선 검토 선정', format(m.selected_count) + '매', `전체 ${m.total_count}매 중`],
      ['Recall (적발률)', pct(m.recall), `TP ${m.TP}매 / 전체 불량 ${m.TP + m.FN}매`],
      ['Precision (정밀도)', pct(m.precision), `FP ${m.FP}매 가양성`],
      ['Lift (검출 배수)', `${format(m.lift)}배`, '무작위 검사 대비 향상 배수']
    ]),
    table([
      { '실제 상태': '불량 1 (Positive)', '검토 대상 (Pred 1)': m.TP, '검토 제외 (Pred 0)': m.FN, '합계': m.TP + m.FN },
      { '실제 상태': '정상 0 (Negative)', '검토 대상 (Pred 1)': m.FP, '검토 제외 (Pred 0)': m.TN, '합계': m.FP + m.TN }
    ])
  );
  return c;
}

// SCREEN 7: 🔲 혼동행렬 전수 대시보드 & 표본 탐색
function renderConfusion() {
  const d = state.overviewData;
  $('confusion-matrix-box').replaceChildren(renderMatrixCard(d.metrics));

  const filterTabs = $('confusion-filter-tabs');
  filterTabs.replaceChildren(...['all', 'TP', 'FP', 'FN', 'TN', '미확인'].map(cat => {
    const count = cat === 'all' ? d.rows.length : d.rows.filter(r => r.category === cat).length;
    const b = button(`${cat === 'all' ? '전체' : cat} (${count})`, () => {
      state.confusionFilter = cat;
      state.confusionPage = 0;
      renderConfusionTable();
    });
    b.classList.toggle('active', state.confusionFilter === cat);
    return b;
  }));

  renderConfusionTable();
}

function renderConfusionTable() {
  const d = state.overviewData;
  const filtered = state.confusionFilter === 'all' ? d.rows : d.rows.filter(r => r.category === state.confusionFilter);
  const total = filtered.length;
  state.confusionPage = Math.min(state.confusionPage, Math.max(0, Math.ceil(total / 50) - 1));
  const pageRows = filtered.slice(state.confusionPage * 50, state.confusionPage * 50 + 50);

  const container = $('confusion-sample-table-wrapper');
  container.replaceChildren(table(pageRows, ['risk_rank', 'sample_id', 'risk_score', 'actual_label', 'category'], r => {
    return button('🔍 진단', () => {
      navigateTo('view-triage');
      diagnoseWafer(r.sample_id);
    }, 'action-btn');
  }));

  $('conf-page-info').textContent = total ? `${state.confusionPage * 50 + 1}–${Math.min((state.confusionPage + 1) * 50, total)} / 총 ${total}행` : '0행';
  $('conf-prev-btn').disabled = state.confusionPage === 0;
  $('conf-next-btn').disabled = (state.confusionPage + 1) * 50 >= total;
}

$('conf-prev-btn').onclick = () => { state.confusionPage--; renderConfusionTable(); };
$('conf-next-btn').onclick = () => { state.confusionPage++; renderConfusionTable(); };

// SCREEN 8: 🔬 센서 드리프트 정밀 관제 & 점검 발령
async function renderDrift() {
  const epoch = state.epoch;
  const d = await api(url('drift'));
  if (epoch !== state.epoch) return;
  state.temporalData = d.temporal;

  const threshold = Number($('drift-threshold-select').value);
  const flagged = d.rows.filter(r => r.shift_std != null && Math.abs(r.shift_std) >= threshold);

  $('drift-summary-metrics').replaceChildren(metricsCard([
    ['비교 센서 수', `${d.rows.length}개`, '저장 모델의 232개 피처'],
    [`기준 초과 센서 (≥${threshold}σ)`, `${flagged.length}개`, '공정 이상 의심'],
    ['현재 분석 표본', `${d.scope_count}매`, '선택된 관제 기간'],
    ['학습 정상 참고군', `${d.reference_count}매`, '고정 레퍼런스']
  ]));

  $('drift-table-container').replaceChildren(table(d.rows.slice(0, 30), ['sensor', 'input_mean', 'reference_mean', 'shift_std', 'std_ratio', 'ks_distance'], r => {
    return button('🛠️ 점검 발령', () => {
      const known = PDM_SENSOR_KNOWLEDGE[r.sensor];
      if (known) {
        openNewTaskDialog({
          sensor: r.sensor,
          chamber: known.chamber,
          shift_std: r.shift_std,
          recommendation: { title: known.title, checks: known.items },
          summary: `${known.reason} (${r.sensor} 평균이동: ${format(r.shift_std)}σ, KS거리: ${format(r.ks_distance)})`
        });
      } else {
        openNewTaskDialog({
          sensor: r.sensor,
          chamber: `${r.sensor} 연계 공정 챔버`,
          shift_std: r.shift_std,
          recommendation: {
            title: `${r.sensor} 공정 센서 이상 편차 점검 지침`,
            checks: [
              `${r.sensor} 신호 배선 커넥터 접촉 불량 및 아날로그 변환 모듈 점검`,
              `정상군 기준치 대비 편차(${format(r.shift_std)}σ) 교정 및 영점 캘리브레이션 수행`
            ]
          },
          summary: `학습 정상군 대비 평균 이동 ${format(r.shift_std)}σ, 표준편차비 ${pct(r.std_ratio)} 이탈`
        });
      }
    }, 'action-btn primary');
  }));

  await renderAdminPdmReview();
  renderTemporalDrift();
}

// 📋 관리자 센서 드리프트 화면 전용: 실시간 현장 실무자 점검 현황 & 조치 보고서 승인 검토
async function renderAdminPdmReview() {
  const container = $('admin-pdm-review-container');
  if (!container) return;

  let d;
  try {
    d = await api(`/api/dashboard/${state.datasetId}/inspections`);
  } catch (err) {
    console.error('점검 현황 로드 실패:', err);
    return;
  }

  const tasks = d.tasks || [];
  const reportedTasks = tasks.filter(t => t.status === 'reported');
  const openTasks = tasks.filter(t => t.status === 'open');
  const approvedTasks = tasks.filter(t => t.status === 'approved');

  container.replaceChildren();

  const card = el('div', null, 'card');
  card.style.padding = '22px 26px';
  card.style.background = '#ffffff';
  card.style.borderRadius = '14px';
  card.style.border = reportedTasks.length > 0 ? '2px solid #3b82f6' : '1px solid var(--border-color)';
  card.style.boxShadow = reportedTasks.length > 0 ? '0 6px 16px rgba(59, 130, 246, 0.1)' : 'var(--shadow-sm)';

  const topRow = el('div');
  topRow.style.display = 'flex';
  topRow.style.justifyContent = 'space-between';
  topRow.style.alignItems = 'center';
  topRow.style.flexWrap = 'wrap';
  topRow.style.gap = '12px';
  topRow.style.marginBottom = '16px';

  topRow.innerHTML = `
    <div>
      <div style="display:flex; align-items:center; gap:8px;">
        <h3 style="font-size:1.15rem; font-weight:800; color:#0f172a; margin:0;">📋 실시간 현장 실무자 점검 현황 & 조치 보고서 승인 검토</h3>
        <span class="brand-tag" style="background:#eff6ff; color:#2563eb; border-color:#93c5fd; font-weight:700;">공정 관리자</span>
      </div>
      <p style="font-size:0.85rem; color:#64748b; margin:4px 0 0 0;">
        관리자가 발령한 챔버 점검 지시를 현장 실무자가 수행하고 제출한 조치 소견을 확인하고 최종 승인(설비 가동)합니다.
      </p>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
      <span class="risk-badge ${reportedTasks.length > 0 ? 'danger' : 'success'}" style="font-size:0.82rem; font-weight:700;">
        ${reportedTasks.length > 0 ? `🚨 승인 대기 ${reportedTasks.length}건` : '✅ 승인 대기 없음'}
      </span>
      <button class="action-btn" style="font-size:0.82rem; padding:6px 14px;" onclick="navigateTo('view-pdm')">
        <span>🛠️ 점검표 전체 관리 화면 ➔</span>
      </button>
    </div>
  `;
  card.append(topRow);

  // 미니 파이프라인 4단계 바
  const statusSummary = el('div', null, 'pdm-mini-pipeline');
  statusSummary.style.display = 'grid';
  statusSummary.style.gridTemplateColumns = 'repeat(auto-fit, minmax(130px, 1fr))';
  statusSummary.style.gap = '10px';
  statusSummary.style.marginBottom = '20px';
  statusSummary.style.width = '100%';
  statusSummary.style.boxSizing = 'border-box';
  statusSummary.innerHTML = `
    <div style="background:#fef2f2; border:1px solid #fca5a5; border-radius:8px; padding:10px 14px;">
      <div style="font-size:0.76rem; color:#dc2626; font-weight:700;">1. 점검 발령 접수</div>
      <div style="font-size:1.1rem; font-weight:900; color:#dc2626;">${openTasks.length}건</div>
    </div>
    <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:10px 14px;">
      <div style="font-size:0.76rem; color:#d97706; font-weight:700;">2. 현장 실사 진행</div>
      <div style="font-size:1.1rem; font-weight:900; color:#d97706;">${openTasks.length}건</div>
    </div>
    <div style="background:#eff6ff; border:1.5px solid #60a5fa; border-radius:8px; padding:10px 14px; box-shadow:${reportedTasks.length > 0 ? '0 2px 6px rgba(37,99,235,0.15)' : 'none'};">
      <div style="font-size:0.76rem; color:#2563eb; font-weight:800;">3. 관리자 승인 대기</div>
      <div style="font-size:1.1rem; font-weight:900; color:#2563eb;">${reportedTasks.length}건</div>
    </div>
    <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-radius:8px; padding:10px 14px;">
      <div style="font-size:0.76rem; color:#059669; font-weight:700;">4. 최종 승인 완료</div>
      <div style="font-size:1.1rem; font-weight:900; color:#059669;">${approvedTasks.length}건</div>
    </div>
  `;
  card.append(statusSummary);

  // 실무자가 제출한 보고서 목록 (우선순위 최고)
  if (reportedTasks.length > 0) {
    const reportedWrap = el('div');
    reportedWrap.style.display = 'flex';
    reportedWrap.style.flexDirection = 'column';
    reportedWrap.style.gap = '14px';

    reportedTasks.forEach(task => {
      const itemBox = el('div');
      itemBox.style.background = '#f0f9ff';
      itemBox.style.border = '1.5px solid #38bdf8';
      itemBox.style.borderRadius = '10px';
      itemBox.style.padding = '18px 20px';

      const head = el('div');
      head.style.display = 'flex';
      head.style.justifyContent = 'space-between';
      head.style.alignItems = 'flex-start';
      head.style.marginBottom = '12px';
      head.innerHTML = `
        <div>
          <span class="pdm-task-badge-urgent" style="margin-bottom:6px;">🚨 [승인 대기] 실무자 현장 조치 보고서 제출 완료</span>
          <h4 style="font-size:1.15rem; font-weight:800; color:#0f172a; margin:4px 0;">${task.title}</h4>
          <div style="font-size:0.82rem; color:#475569;">
            대상 설비: <b style="color:#0284c7;">⚙️ ${task.chamber}</b> · 이상 징후: <b style="color:#dc2626;">${task.reason}</b>
          </div>
        </div>
        <span class="brand-tag" style="background:#2563eb; color:#ffffff; font-weight:800; font-size:0.8rem; padding:4px 12px;">승인 요청</span>
      `;
      itemBox.append(head);

      // 실무자 체크 완료 항목
      const checkListEl = el('div');
      checkListEl.style.background = '#ffffff';
      checkListEl.style.border = '1px solid #e2e8f0';
      checkListEl.style.borderRadius = '8px';
      checkListEl.style.padding = '12px 16px';
      checkListEl.style.marginBottom = '12px';
      checkListEl.innerHTML = `
        <div style="font-size:0.78rem; font-weight:700; color:#64748b; margin-bottom:6px;">현장 실무자 점검 확인 항목:</div>
        ${(task.items || []).map(it => `
          <div style="display:flex; align-items:center; gap:8px; font-size:0.84rem; color:#0f172a; margin-bottom:4px;">
            <span style="color:#059669; font-weight:900;">✔</span>
            <span>${it}</span>
          </div>
        `).join('')}
      `;
      itemBox.append(checkListEl);

      // 실무자 현장 조치 소견 박스 (눈에 띄게 강조)
      const notesBox = el('div');
      notesBox.style.background = '#ffffff';
      notesBox.style.border = '2px solid #0284c7';
      notesBox.style.borderRadius = '8px';
      notesBox.style.padding = '14px 18px';
      notesBox.style.marginBottom = '16px';
      notesBox.innerHTML = `
        <div style="font-size:0.82rem; font-weight:800; color:#0284c7; margin-bottom:4px;">✍️ 실무자 현장 조치 소견 및 세부 결과:</div>
        <div style="font-size:0.94rem; color:#0f172a; line-height:1.6; font-weight:700;">
          ${task.notes || '작성된 소견이 없습니다.'}
        </div>
      `;
      itemBox.append(notesBox);

      // 액션 버튼
      const actRow = el('div');
      actRow.style.display = 'flex';
      actRow.style.justifyContent = 'flex-end';
      actRow.style.gap = '12px';

      const approveBtn = button('✅ 최종 승인 완료 (설비 정상 가동 허가)', async () => {
        await busy(approveBtn, async () => {
          await post(`/api/dashboard/inspections/${task.id}/approve`, {});
          showToast(`✅ [${task.chamber}] 점검 보고서가 최종 승인되었습니다! 설비 가동이 정상 허가되었습니다.`);
          await renderAdminPdmReview();
        });
      }, 'action-btn primary');
      approveBtn.style.padding = '10px 22px';
      approveBtn.style.fontWeight = '700';
      approveBtn.style.background = '#2563eb';

      const reopenBtn = button('↩️ 재실사/보완 요청', async () => {
        await busy(reopenBtn, async () => {
          await post(`/api/dashboard/inspections/${task.id}/reopen`, {
            review_note: '실측 센서 수치 및 영점 재점검 요망'
          });
          showToast(`점검 지시가 보완 요청으로 실무자에게 재발령되었습니다.`);
          await renderAdminPdmReview();
        });
      }, 'action-btn');
      reopenBtn.style.padding = '10px 16px';

      actRow.append(reopenBtn, approveBtn);
      itemBox.append(actRow);
      reportedWrap.append(itemBox);
    });

    card.append(reportedWrap);
  } else {
    // 승인 대기 보고서가 없을 때
    const emptyBox = el('div');
    emptyBox.style.padding = '24px';
    emptyBox.style.textAlign = 'center';
    emptyBox.style.background = '#f8fafc';
    emptyBox.style.borderRadius = '8px';
    emptyBox.style.border = '1px solid #e2e8f0';

    if (openTasks.length > 0) {
      emptyBox.innerHTML = `
        <div style="font-size:0.92rem; font-weight:700; color:#334155; margin-bottom:4px;">
          🛠️ 현재 현장 실무자가 ${openTasks.length}건의 점검 지시를 확인 및 실사 진행 중입니다.
        </div>
        <p style="font-size:0.82rem; color:#64748b; margin:0;">
          실무자가 현장에서 점검 체크리스트를 확인하고 조치 소견서를 제출하면 즉시 이곳에 승인 요청 카드가 표시됩니다.
        </p>
      `;
    } else {
      emptyBox.innerHTML = `
        <div style="font-size:0.92rem; font-weight:700; color:#334155; margin-bottom:4px;">
          ✅ 현재 승인 대기 중이거나 진행 중인 점검 지시가 없습니다.
        </div>
        <p style="font-size:0.82rem; color:#64748b; margin:0;">
          위의 센서 드리프트 관제 표에서 이상 센서의 <b>[🛠️ 점검 발령]</b> 버튼을 누르면 현장 실무자에게 점검 지시가 즉시 발송됩니다.
        </p>
      `;
    }
    card.append(emptyBox);
  }

  container.replaceChildren(card);
}

$('btn-refresh-drift').onclick = () => busy($('btn-refresh-drift'), renderDrift);
$('drift-threshold-select').onchange = () => renderDrift();

function renderTemporalDrift() {
  const d = state.temporalData;
  const container = $('temporal-drift-container');
  if (!d) { container.innerHTML = '<p class="muted">시계열 드리프트 데이터가 없습니다.</p>'; return; }

  const mode = $('drift-direction-select').value;
  const rows = d.rows.filter(r => mode === 'all' || (mode === 'both' ? r.direction !== 'flat' : r.direction === mode));

  const wrap = el('div');
  wrap.append(
    metricsCard([
      ['분석 센서 수', `${d.analyzed_sensors}개`, '결측 제외 유효 센서'],
      ['상승 드리프트', `${d.direction_counts.upward}개`, 'Pearson r > 0'],
      ['하강 드리프트', `${d.direction_counts.downward}개`, 'Pearson r < 0'],
      ['평탄 센서', `${d.direction_counts.flat}개`, '유의차 없음']
    ])
  );

  for (const series of d.time_series || []) {
    wrap.append(graphCard(`${series.sensor} 월별 원본 평균 추이`, series.rows.map(r => r.period), series.rows.map(r => r.mean), true));
  }

  wrap.append(table(rows, ['sensor', 'direction', 'drift_index', 'normalized_drift_sigma', 'pearson_r', 'kendall_tau', 'start_mean', 'end_mean']));
  container.replaceChildren(wrap);
}

$('drift-direction-select').onchange = async () => {
  const r = await post(`/api/dashboard/${state.datasetId}/tools/sensor_drift`, {
    period: state.period,
    ratio: state.ratio,
    arguments: { direction: $('drift-direction-select').value, limit: 30 }
  });
  state.temporalData = r.data;
  renderTemporalDrift();
};

// SCREEN 9: 📂 공정 CSV 데이터 관리 & 품질 요약
function renderDataQuality() {
  const p = state.overviewData.profile;
  const container = $('dataset-quality-container');
  container.replaceChildren(metricsCard([
    ['총 표본 수', `${format(p.row_count)}매`, '현재 선택 데이터셋'],
    ['원본 센서 수', `${format(p.sensor_count)}개`, '공정 관제 필수 센서'],
    ['결측치 비율', pct(p.missing_ratio), `${format(p.missing_cells)}개 결측 셀`],
    ['정답 라벨 확인', `${format(p.known_label_count)}매`, `미확인: ${format(p.unknown_label_count)}매`]
  ]));
}

// Upload & Simulation Ingestion
$('csv-upload-form').onsubmit = e => {
  e.preventDefault();
  busy(e.submitter, async () => {
    const file = $('csv-file-input').files[0];
    if (!file) return;
    showToast(`📁 ${file.name} 업로드 및 모델 추론을 시작합니다...`);
    const formData = new FormData();
    formData.append('file', file);
    const res = await api('/api/predict-batch', { method: 'POST', body: formData });
    await loadDatasetList(res.dataset_id);
    await refreshGlobalData(true);
    navigateTo('view-admin-wiki');
    renderDataQuality();
    showToast(`✅ ${file.name} 업로드 및 배치 추론이 완료되었습니다. 현재 공정 데이터셋으로 반영되었습니다.`);
    $('csv-file-input').value = '';
  });
};

$('sim-data-form').onsubmit = e => {
  e.preventDefault();
  busy(e.submitter, async () => {
    const filename = $('sim-data-select').value;
    if (!filename) return;
    showToast(`📁 ${filename} 분석 및 모델 추론을 시작합니다...`);
    const res = await post(`/api/simulation/${encodeURIComponent(filename)}/analyze`, {});
    await loadDatasetList(res.dataset_id);
    await refreshGlobalData(true);
    navigateTo('view-admin-wiki');
    renderDataQuality();
    showToast(`✅ ${filename} 시뮬레이션 파일 분석 완료! 현재 공정 데이터셋으로 반영되었습니다.`);
  });
};

$('btn-load-default-sim').onclick = () => busy($('btn-load-default-sim'), async () => {
  showToast('기본 관제 시뮬레이션 배치(300행)를 저장 모델로 추론하여 초기화합니다...');
  const res = await post('/api/dashboard/initial', {});
  await loadDatasetList(res.dataset_id);
  await refreshGlobalData(true);
  showToast('✅ 기본 관제 시뮬레이션 데이터가 초기화되었습니다.');
});

// Controls: Dataset, Period, Ratio
$('dataset-select').onchange = () => {
  state.datasetId = $('dataset-select').value;
  refreshGlobalData(true);
};

$('period-select').onchange = () => {
  state.period = $('period-select').value;
  state.confusionFilter = 'all';
  state.confusionPage = 0;
  refreshGlobalData();
};

$('review-ratio-slider').oninput = () => {
  $('ratio-display').textContent = $('review-ratio-slider').value + '%';
};

$('review-ratio-slider').onchange = () => {
  state.ratio = Number($('review-ratio-slider').value) / 100;
  state.confusionFilter = 'all';
  state.confusionPage = 0;
  refreshGlobalData();
};

// Assistant Drawer (SEMI-AI)
function toggleAssistant(open = null) {
  const drawer = $('assistant-drawer');
  if (open === null) open = drawer.style.display === 'none';
  drawer.style.display = open ? 'flex' : 'none';
}

function openAssistant(prefilledQuery = '') {
  toggleAssistant(true);
  if (prefilledQuery) {
    $('chat-input-textarea').value = prefilledQuery;
    $('chat-input-textarea').focus();
  }
}

$('btn-open-assistant').onclick = () => toggleAssistant();
$('btn-close-assistant').onclick = () => toggleAssistant(false);

document.querySelectorAll('.assistant-preset-btn').forEach(btn => {
  btn.onclick = () => {
    openAssistant(btn.dataset.question);
  };
});

$('chat-input-form').onsubmit = e => {
  e.preventDefault();
  const q = $('chat-input-textarea').value.trim();
  if (!q) return;

  busy($('btn-send-chat'), async () => {
    const key = `${state.datasetId}:${state.period}:${state.ratio}`;
    const messages = $('chat-messages');

    // User message bubble
    const userBubble = el('div', q, 'message user');
    userBubble.style.background = '#2563eb';
    userBubble.style.color = '#ffffff';
    userBubble.style.padding = '12px 16px';
    userBubble.style.borderRadius = '12px';
    userBubble.style.alignSelf = 'flex-end';
    userBubble.style.maxWidth = '85%';
    userBubble.style.fontSize = '0.88rem';
    messages.append(userBubble);
    $('chat-input-textarea').value = '';
    messages.scrollTop = messages.scrollHeight;

    const res = await post(`/api/dashboard/${state.datasetId}/chat`, {
      query: q,
      period: state.period,
      ratio: state.ratio,
      conversation_id: state.conversations[key] || null
    });

    state.conversations[key] = res.conversation_id;

    // Assistant message bubble
    const aiBubble = el('div', null, 'message assistant');
    aiBubble.style.background = '#f1f5f9';
    aiBubble.style.padding = '14px 16px';
    aiBubble.style.borderRadius = '12px';
    aiBubble.style.alignSelf = 'flex-start';
    aiBubble.style.maxWidth = '90%';
    aiBubble.style.fontSize = '0.88rem';
    aiBubble.style.lineHeight = '1.5';

    aiBubble.append(el('div', res.answer));

    if (res.tool_results && res.tool_results.length > 0) {
      const details = el('details');
      details.style.marginTop = '10px';
      details.style.fontSize = '0.78rem';
      details.style.color = '#64748b';
      details.append(el('summary', `🛠️ Python Tool 계산 근거 (${res.tool_results.length}회 호출)`));
      details.append(el('pre', JSON.stringify(res.tool_results, null, 2)));
      aiBubble.append(details);
    }

    messages.append(aiBubble);
    messages.scrollTop = messages.scrollHeight;
  });
};

// Modal: Mobile QR
$('open-qr-btn').onclick = () => {
  $('qr-modal-image').src = '/api/dashboard-qr';
  $('qr-modal-url').textContent = location.origin + '/';
  $('qr-modal-dialog').showModal();
};

$('btn-close-qr-modal').onclick = () => $('qr-modal-dialog').close();

// Reset All Datasets Handler
async function resetAllDatasets() {
  if (!confirm('현재 등록된 모든 데이터셋을 초기화하시겠습니까?\n초기화 후에는 깨끗한 대기 상태에서 시뮬레이션 CSV를 업로드하실 수 있습니다.')) return;
  try {
    showToast('모든 데이터셋을 초기화하고 있습니다...');
    await post('/api/datasets/reset', {});
    await loadDatasetList();
    await refreshGlobalData(true);
    showToast('✅ 모든 데이터셋이 초기화되었습니다. CSV 업로드 화면으로 이동합니다.');
    navigateTo('view-admin-wiki');
  } catch (err) {
    showToast(`초기화 실패: ${err.message}`, true);
  }
}

if ($('btn-top-reset')) $('btn-top-reset').onclick = resetAllDatasets;
if ($('btn-reset-datasets')) $('btn-reset-datasets').onclick = resetAllDatasets;

// Entry & Authentication
async function enterApp(role, name = '로컬 엔지니어', isDemo = true) {
  state.authDemo = isDemo;
  $('auth-gate-screen').style.display = 'none';
  $('main-app-wrapper').style.display = 'flex';
  $('user-display-email').textContent = name + (isDemo ? ' · 데모' : '');
  // Role-specific top header switcher isolation
  const engBtn = $('role-btn-engineer');
  const admBtn = $('role-btn-admin');
  if (role === 'engineer') {
    if (engBtn) engBtn.style.display = 'inline-flex';
    if (admBtn) admBtn.style.display = 'none';
  } else {
    if (engBtn) engBtn.style.display = 'none';
    if (admBtn) admBtn.style.display = 'inline-flex';
  }

  switchRole(role);

  const datasets = await loadDatasetList();

  // Populate simulation selectors
  try {
    const simData = await api('/api/simulation');
    $('sim-file-select').replaceChildren(...simData.files.map(f => new Option(`${f.filename} (${(f.bytes / 1024).toFixed(0)} KB)`, f.filename)));
    $('sim-data-select').replaceChildren(...simData.files.map(f => new Option(`${f.filename} (${(f.bytes / 1024).toFixed(0)} KB)`, f.filename)));
  } catch (err) {
    console.warn(err);
  }

  await refreshGlobalData(true);

  if (!datasets.length) {
    showToast('현재 등록된 공정 데이터셋이 없습니다. 아래에서 시뮬레이션 CSV를 업로드하거나 선택해 주세요.');
    navigateTo('view-admin-wiki');
  } else {
    navigateTo('view-hub');
  }
}

$('gate-demo-eng').onclick = () => enterApp('engineer', '👷 박주형 현장 엔지니어', true);
$('gate-demo-adm').onclick = () => enterApp('admin', '👨‍💼 박주형 공정 관리자', true);

$('header-logout-btn').onclick = async () => {
  if (!state.authDemo && typeof firebaseAuth !== 'undefined' && firebaseAuth) {
    await firebaseAuth.signOut();
  }
  const engBtn = $('role-btn-engineer');
  const admBtn = $('role-btn-admin');
  if (engBtn) engBtn.style.display = 'inline-flex';
  if (admBtn) admBtn.style.display = 'inline-flex';
  $('main-app-wrapper').style.display = 'none';
  $('auth-gate-screen').style.display = 'flex';
};

// Firebase Form Handlers & Admin Approval System
let isSignup = false;
$('gate-tab-signup').onclick = () => {
  isSignup = true;
  $('gate-tab-signup').classList.add('active');
  $('gate-tab-login').classList.remove('active');
  $('gate-name-group').style.display = 'block';
  $('gate-submit-btn').querySelector('span').textContent = '신규 회원가입 (승인 요청)';
  if ($('gate-success-box')) $('gate-success-box').style.display = 'none';
  if ($('gate-error-msg')) $('gate-error-msg').style.display = 'none';
};

$('gate-tab-login').onclick = () => {
  isSignup = false;
  $('gate-tab-login').classList.add('active');
  $('gate-tab-signup').classList.remove('active');
  $('gate-name-group').style.display = 'none';
  $('gate-submit-btn').querySelector('span').textContent = '로그인';
  if ($('gate-error-msg')) $('gate-error-msg').style.display = 'none';
};

$('gate-auth-form').onsubmit = e => {
  e.preventDefault();
  const errBox = $('gate-error-msg');
  const successBox = $('gate-success-box');
  if (errBox) errBox.style.display = 'none';
  if (successBox && !isSignup) successBox.style.display = 'none';

  busy($('gate-submit-btn'), async () => {
    if (typeof firebaseAuth === 'undefined' || !firebaseAuth) {
      throw Error('Firebase SDK를 로드할 수 없습니다. 위의 [빠른 테스트 데모 입장] 버튼을 이용하십시오.');
    }
    const email = $('gate-email').value.trim();
    const pw = $('gate-password').value;
    const role = $('gate-role').value;
    const nameInput = $('gate-name') ? $('gate-name').value.trim() : '';

    try {
      if (isSignup) {
        // Sign Up: Requires Admin Approval
        const signupRes = await handleFirebaseSignUp(email, pw, role, nameInput);
        $('gate-password').value = '';
        if (errBox) errBox.style.display = 'none';
        
        if (signupRes.status === 'pending' || !signupRes.isApproved) {
          if (successBox) successBox.style.display = 'block';
          $('gate-tab-login').click();
          showToast('🎉 회원가입 신청이 안전하게 접수되었습니다. 공정 관리자(Admin) 승인 후 로그인해 주세요.');
          return;
        } else {
          // Pre-approved admin account
          await enterApp(role, signupRes.displayName || email, false);
          return;
        }
      } else {
        // Sign In: Validates Admin Approval
        const signinRes = await handleFirebaseSignIn(email, pw, role);
        $('gate-password').value = '';
        if (errBox) errBox.style.display = 'none';
        await enterApp(signinRes.role, signinRes.displayName || email, false);
      }
    } catch (authErr) {
      console.error('Firebase Auth Error:', authErr);
      let msg = authErr.message;
      if (authErr.code === 'auth/approval-pending') {
        msg = '⏳ [가입 승인 대기 중] 관리자의 승인이 아직 완료되지 않은 계정입니다. 사내 공정 관리자(Admin)에게 승인을 요청해 주세요.';
      } else if (authErr.code === 'auth/approval-rejected') {
        msg = '❌ [가입 반려] 회원가입 신청이 반려된 계정입니다. 공정 관리자에게 문의해 주세요.';
      } else if (authErr.code === 'auth/invalid-credential' || authErr.code === 'auth/wrong-password') {
        msg = '비밀번호가 일치하지 않거나 유효하지 않은 로그인 정보입니다. 비밀번호를 다시 확인해 주세요.';
      } else if (authErr.code === 'auth/user-not-found') {
        msg = '등록되지 않은 사내 이메일 계정입니다. [신규 회원가입] 탭을 눌러 가입해 주세요.';
      } else if (authErr.code === 'auth/email-already-in-use') {
        msg = '이미 가입된 이메일 계정입니다. [Firebase 로그인] 탭을 이용해 주세요.';
      } else if (authErr.code === 'auth/weak-password') {
        msg = '비밀번호는 최소 6자 이상이어야 합니다.';
      } else if (authErr.code === 'auth/invalid-email') {
        msg = '올바른 이메일 주소 형식을 입력해 주세요.';
      } else if (authErr.message && authErr.message.includes('signup-are-blocked')) {
        msg = 'Google Cloud API 키 제한으로 인해 계정 생성이 차단되었습니다. 방금 API 키 설정이 복구되었으니 잠시 후 다시 시도해 주세요.';
      }
      if (errBox) {
        errBox.textContent = `⚠️ ${msg}`;
        errBox.style.display = 'block';
      }
      throw authErr;
    }
  });
};

// Automatic login if active Firebase session exists & is approved
if (typeof setupFirebaseAuthObserver === 'function') {
  setupFirebaseAuthObserver(async (authData) => {
    if (authData && authData.isLoggedIn && authData.email) {
      console.log('Firebase active approved session:', authData.email);
      const role = authData.role || 'engineer';
      const name = authData.name || authData.email;
      const gateScreen = $('auth-gate-screen');
      if (gateScreen && gateScreen.style.display !== 'none') {
        await enterApp(role, name, false);
      }
    } else if (authData && authData.isPending) {
      const errBox = $('gate-error-msg');
      if (errBox) {
        errBox.textContent = `⚠️ ⏳ [가입 승인 대기 중] 관리자 승인 대기 중인 계정(${authData.email})입니다. 사내 공정 관리자 승인 완료 후 이용 가능합니다.`;
        errBox.style.display = 'block';
      }
    }
  });
}

// ============================================================================
// ADMIN USER APPROVAL MANAGEMENT MODAL LOGIC
// ============================================================================
let currentApprovalFilter = 'all';

async function updatePendingBadge() {
  try {
    const data = await fetchAdminUserList();
    const count = data.pendingCount || 0;
    const topBadge = $('top-pending-badge');
    const hubBadge = $('hub-pending-badge');
    if (topBadge) {
      topBadge.textContent = count;
      topBadge.style.display = count > 0 ? 'inline-block' : 'none';
    }
    if (hubBadge) {
      hubBadge.textContent = `대기 ${count}명`;
      hubBadge.style.display = count > 0 ? 'inline-block' : 'none';
    }
  } catch(e) {}
}

window.openUserApprovalModal = async function() {
  const dialog = $('user-approval-dialog');
  if (!dialog) return;
  dialog.showModal();
  await loadUserApprovalList(currentApprovalFilter);
};

window.loadUserApprovalList = async function(filter = 'all') {
  currentApprovalFilter = filter;
  const tbody = $('user-approval-table-body');
  if (!tbody) return;

  // Filter tab buttons active style
  ['all', 'pending', 'approved'].forEach(f => {
    const btn = $(`filter-user-${f}`);
    if (btn) {
      btn.style.background = f === filter ? '#eff6ff' : '#ffffff';
      btn.style.borderColor = f === filter ? '#93c5fd' : '#cbd5e1';
      btn.style.color = f === filter ? '#1d4ed8' : '#475569';
      btn.style.fontWeight = f === filter ? '700' : '600';
    }
  });

  tbody.innerHTML = `<tr><td colspan="6" style="padding:28px; text-align:center; color:#64748b;">⏳ 사용자 목록 조회 중...</td></tr>`;

  try {
    const data = await fetchAdminUserList();
    const allUsers = data.users || [];
    
    // Update counters
    const countAll = $('count-all-users');
    const countPending = $('count-pending-users');
    const countApproved = $('count-approved-users');
    if (countAll) countAll.textContent = allUsers.length;
    if (countPending) countPending.textContent = data.pendingCount || 0;
    if (countApproved) countApproved.textContent = allUsers.filter(u => u.status === 'approved').length;

    updatePendingBadge();

    let filtered = allUsers;
    if (filter === 'pending') {
      filtered = allUsers.filter(u => u.status === 'pending');
    } else if (filter === 'approved') {
      filtered = allUsers.filter(u => u.status === 'approved');
    }

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="padding:32px; text-align:center; color:#94a3b8; font-size:0.9rem;">해당 상태의 사용자가 없습니다.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(u => {
      const isPend = u.status === 'pending';
      const isAppr = u.status === 'approved';
      const statusBadge = isPend 
        ? `<span style="background:#fef3c7; color:#92400e; padding:3px 9px; border-radius:99px; font-size:0.75rem; font-weight:700; border:1px solid #fde68a;">⏳ 승인 대기</span>`
        : isAppr 
        ? `<span style="background:#ecfdf5; color:#065f46; padding:3px 9px; border-radius:99px; font-size:0.75rem; font-weight:700; border:1px solid #a7f3d0;">✅ 승인 완료</span>`
        : `<span style="background:#fee2e2; color:#991b1b; padding:3px 9px; border-radius:99px; font-size:0.75rem; font-weight:700; border:1px solid #fca5a5;">❌ 반려됨</span>`;
      
      const roleBadge = u.role === 'admin'
        ? `<span style="background:#eff6ff; color:#1e40af; font-size:0.76rem; padding:2px 8px; border-radius:4px; font-weight:600;">👨‍💼 공정 관리자</span>`
        : `<span style="background:#f1f5f9; color:#334155; font-size:0.76rem; padding:2px 8px; border-radius:4px; font-weight:600;">👷 현장 엔지니어</span>`;

      const reqDate = u.requestedAt ? new Date(u.requestedAt).toLocaleString('ko-KR', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '-';

      const actions = isPend 
        ? `<div style="display:flex; gap:6px; justify-content:center;">
             <button type="button" class="action-btn" style="padding:4px 10px; font-size:0.78rem; background:#10b981; color:#fff; border:none; font-weight:700;" onclick="handleUserApproval('${u.uid}', true, '${u.email}')">승인</button>
             <button type="button" class="action-btn" style="padding:4px 10px; font-size:0.78rem; background:#fee2e2; color:#b91c1c; border-color:#fca5a5;" onclick="handleUserApproval('${u.uid}', false, '${u.email}')">반려</button>
           </div>`
        : `<div style="display:flex; gap:6px; justify-content:center;">
             <button type="button" class="action-btn" style="padding:3px 8px; font-size:0.75rem; color:#64748b;" onclick="handleUserApproval('${u.uid}', ${!isAppr}, '${u.email}')">${isAppr ? '반려로 변경' : '재승인'}</button>
           </div>`;

      return `
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:12px 14px; font-weight:700; color:#0f172a;">${u.name || '-'}</td>
          <td style="padding:12px 14px; font-family:monospace; color:#334155;">${u.email}</td>
          <td style="padding:12px 14px;">${roleBadge}</td>
          <td style="padding:12px 14px; font-size:0.78rem; color:#64748b;">${reqDate}</td>
          <td style="padding:12px 14px; text-align:center;">${statusBadge}</td>
          <td style="padding:12px 14px; text-align:center;">${actions}</td>
        </tr>
      `;
    }).join('');

  } catch(err) {
    tbody.innerHTML = `<tr><td colspan="6" style="padding:24px; text-align:center; color:#ef4444;">오류 발생: ${err.message}</td></tr>`;
  }
};

window.handleUserApproval = async function(uid, approve, email) {
  const actionName = approve ? '가입 승인' : '가입 반려';
  if (!confirm(`[${email}] 사용자의 ${actionName} 처리를 진행하시겠습니까?`)) return;
  try {
    const currentAdmin = (typeof firebaseAuth !== 'undefined' && firebaseAuth && firebaseAuth.currentUser && firebaseAuth.currentUser.email) || 'admin@semiguard.fab';
    await approveUserAccount(uid, approve, currentAdmin);
    showToast(`✅ [${email}] 사원의 ${actionName}이 완료되었습니다.`);
    await loadUserApprovalList(currentApprovalFilter);
    updatePendingBadge();
  } catch(err) {
    showToast(`❌ ${actionName} 실패: ` + err.message, true);
  }
};

// Event listeners for approval modal
$('btn-close-approval-modal')?.addEventListener('click', () => $('user-approval-dialog')?.close());
$('filter-user-all')?.addEventListener('click', () => loadUserApprovalList('all'));
$('filter-user-pending')?.addEventListener('click', () => loadUserApprovalList('pending'));
$('filter-user-approved')?.addEventListener('click', () => loadUserApprovalList('approved'));
$('btn-refresh-users')?.addEventListener('click', () => loadUserApprovalList(currentApprovalFilter));

