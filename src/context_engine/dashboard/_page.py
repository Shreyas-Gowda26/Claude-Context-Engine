"""Embedded HTML page for the CCE dashboard.

Single-file SPA. Fetches data from /api/* on tab switch.
Polls /api/status every 5 seconds for live updates.
No external dependencies — all CSS and JS inline.
"""

PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CCE Dashboard</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; color: #c9d1d9; font-family: system-ui, -apple-system, sans-serif; font-size: 14px; }
a { color: #58a6ff; text-decoration: none; }
button { cursor: pointer; }

.nav { background: #161b22; border-bottom: 1px solid #30363d; padding: 0 20px; display: flex; align-items: center; gap: 24px; }
.nav-brand { color: #e2eeff; font-weight: 700; font-size: 15px; padding: 12px 0; letter-spacing: 2px; }
.nav-project { color: #8b949e; font-size: 12px; }
.tabs { display: flex; margin-left: auto; }
.tab { padding: 12px 16px; font-size: 13px; color: #8b949e; background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; }
.tab.active { color: #58a6ff; border-bottom-color: #58a6ff; }
.tab:hover:not(.active) { color: #c9d1d9; }
.main { padding: 24px 20px; max-width: 1100px; }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
.stat-value { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
.stat-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.4px; }
.green { color: #3fb950; } .blue { color: #58a6ff; } .yellow { color: #e3b341; } .purple { color: #a5d6ff; }

.panel-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
.panel-title { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #8b949e; margin-bottom: 12px; }

.badge { display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: 11px; font-weight: 500; }
.badge-ok { background: #1a3a1a; color: #3fb950; }
.badge-stale { background: #3a2e1a; color: #e3b341; }
.badge-missing { background: #2a1a1a; color: #f85149; }
.badge-active { background: #1a2e3a; color: #58a6ff; }
.badge-closed { background: #21262d; color: #8b949e; }

.health-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid #21262d; }
.health-row:last-child { border-bottom: none; }

.btn { padding: 6px 14px; border-radius: 6px; font-size: 12px; border: none; }
.btn-primary { background: #1f6feb; color: #fff; }
.btn-primary:hover { background: #388bfd; }
.btn-secondary { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
.btn-secondary:hover { background: #30363d; }
.btn-danger { background: #da3633; color: #fff; }
.btn-danger:hover { background: #f85149; }
.btn-icon { background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 3px 8px; border-radius: 5px; font-size: 12px; }
.btn-icon:hover { color: #c9d1d9; }
.btn-row { display: flex; gap: 8px; margin-top: 14px; padding-top: 12px; border-top: 1px solid #21262d; }

.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.search-input { background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 7px 12px; border-radius: 6px; font-size: 13px; outline: none; flex: 1; max-width: 280px; }
.search-input:focus { border-color: #58a6ff; }
.table { background: #161b22; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }
.table-head { display: grid; grid-template-columns: 3fr 80px 90px 80px; padding: 8px 14px; background: #21262d; font-size: 10px; text-transform: uppercase; letter-spacing: 0.4px; color: #8b949e; gap: 10px; }
.table-row { display: grid; grid-template-columns: 3fr 80px 90px 80px; padding: 9px 14px; border-top: 1px solid #21262d; align-items: center; gap: 10px; font-size: 13px; }
.table-row:hover { background: #21262d22; }
.file-path { color: #58a6ff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; }
.row-actions { display: flex; gap: 5px; }
.no-data { color: #8b949e; text-align: center; padding: 32px; font-size: 13px; }

.session-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; margin-bottom: 10px; }
.session-header { display: flex; justify-content: space-between; align-items: flex-start; cursor: pointer; }
.session-name { font-size: 14px; font-weight: 600; color: #c9d1d9; }
.session-meta { font-size: 11px; color: #8b949e; margin-top: 3px; }
.session-body { display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid #21262d; }
.session-body.open { display: block; }
.decision-item { background: #21262d; border-radius: 5px; padding: 6px 10px; font-size: 12px; margin-bottom: 5px; }

.savings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.bar-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }
.bar-track { background: #21262d; border-radius: 4px; height: 8px; margin-bottom: 12px; }
.bar-fill { height: 8px; border-radius: 4px; }
.comp-buttons { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.comp-btn { padding: 5px 12px; border-radius: 5px; font-size: 12px; background: #21262d; border: 1px solid #30363d; color: #8b949e; }
.comp-btn.active { background: #1f6feb; border-color: #1f6feb; color: #fff; }

.toast { position: fixed; bottom: 20px; right: 20px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px 16px; font-size: 13px; opacity: 0; transition: opacity 0.2s; pointer-events: none; z-index: 100; }
.toast.show { opacity: 1; }

.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #30363d; border-top-color: #58a6ff; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.banner { background: #1c2d40; border: 1px solid #1f6feb; border-radius: 8px; padding: 14px 18px; color: #79c0ff; font-size: 13px; margin-bottom: 20px; }
</style>
</head>
<body>

<div class="nav">
  <span class="nav-brand">CCE</span>
  <span class="nav-project" id="nav-project">loading...</span>
  <div class="tabs">
    <button class="tab active" onclick="showTab('overview')">Overview</button>
    <button class="tab" onclick="showTab('files')">Files</button>
    <button class="tab" onclick="showTab('sessions')">Sessions</button>
    <button class="tab" onclick="showTab('savings')">Savings</button>
  </div>
</div>

<div class="main">

  <div id="tab-overview">
    <div id="uninit-banner" class="banner" style="display:none">
      Index not initialised — run <code>cce init</code> in your project first.
    </div>
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-value green" id="stat-chunks">&#8212;</div><div class="stat-label">Chunks indexed</div></div>
      <div class="stat-card"><div class="stat-value blue" id="stat-files">&#8212;</div><div class="stat-label">Files indexed</div></div>
      <div class="stat-card"><div class="stat-value yellow" id="stat-queries">&#8212;</div><div class="stat-label">Queries run</div></div>
      <div class="stat-card"><div class="stat-value purple" id="stat-saved">&#8212;</div><div class="stat-label">Tokens saved</div></div>
    </div>
    <div class="panel-row">
      <div class="panel">
        <div class="panel-title">Index Health</div>
        <div id="health-rows"><div class="no-data">Loading...</div></div>
        <div class="btn-row">
          <button class="btn btn-primary" onclick="doReindex(false)" id="btn-reindex-changed">Reindex changed</button>
          <button class="btn btn-secondary" onclick="doReindex(true)" id="btn-reindex-full">Full reindex</button>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">Recent Sessions</div>
        <div id="recent-sessions"><div class="no-data">Loading...</div></div>
      </div>
    </div>
  </div>

  <div id="tab-files" style="display:none">
    <div class="toolbar">
      <input class="search-input" placeholder="Filter files..." oninput="filterFiles(this.value)" id="file-filter">
      <button class="btn btn-secondary" onclick="doExport()">Export JSON</button>
      <button class="btn btn-danger" onclick="doClear()">Clear index</button>
    </div>
    <div class="table">
      <div class="table-head"><div>File</div><div>Chunks</div><div>Status</div><div></div></div>
      <div id="file-rows"><div class="no-data">Loading...</div></div>
    </div>
  </div>

  <div id="tab-sessions" style="display:none">
    <div id="session-list"><div class="no-data">Loading...</div></div>
  </div>

  <div id="tab-savings" style="display:none">
    <div class="savings-grid">
      <div class="panel">
        <div class="panel-title">Token Usage</div>
        <div id="savings-detail"><div class="no-data">Loading...</div></div>
      </div>
      <div class="panel">
        <div class="panel-title">Output Compression</div>
        <div style="font-size:12px;color:#8b949e;margin-bottom:8px;">Controls how Claude formats responses</div>
        <div class="comp-buttons" id="comp-buttons">
          <button class="comp-btn" onclick="setCompression('off')">off</button>
          <button class="comp-btn" onclick="setCompression('lite')">lite</button>
          <button class="comp-btn" onclick="setCompression('standard')">standard</button>
          <button class="comp-btn" onclick="setCompression('max')">max</button>
        </div>
      </div>
    </div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
const API = '';
let allFiles = [];
let currentOutputLevel = 'standard';

function showTab(name) {
  ['overview','files','sessions','savings'].forEach(t => {
    document.getElementById('tab-' + t).style.display = t === name ? 'block' : 'none';
  });
  document.querySelectorAll('.tab').forEach((el, i) => {
    const names = ['overview','files','sessions','savings'];
    el.classList.toggle('active', names[i] === name);
  });
  if (name === 'files') loadFiles();
  if (name === 'sessions') loadSessions();
  if (name === 'savings') loadSavings();
}

function toast(msg, duration) {
  duration = duration || 2500;
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(function() { el.classList.remove('show'); }, duration);
}

function reltime(ts) {
  const diff = Math.floor((Date.now() / 1000) - ts);
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  return Math.floor(diff / 86400) + 'd ago';
}

async function loadStatus() {
  try {
    const r = await fetch(API + '/api/status');
    const d = await r.json();
    document.getElementById('nav-project').textContent = d.project || '';
    document.getElementById('stat-chunks').textContent = d.chunks.toLocaleString();
    document.getElementById('stat-files').textContent = d.files.toLocaleString();
    document.getElementById('stat-queries').textContent = d.queries.toLocaleString();
    document.getElementById('stat-saved').textContent = d.tokens_saved_pct + '%';
    document.getElementById('uninit-banner').style.display = d.initialized ? 'none' : 'block';
    currentOutputLevel = d.output_level;
    updateCompButtons(d.output_level);
    loadHealthAndSessions();
  } catch (e) {}
}

async function loadHealthAndSessions() {
  try {
    const r = await fetch(API + '/api/files');
    const files = await r.json();
    const ok = files.filter(function(f) { return f.status === 'ok'; }).length;
    const stale = files.filter(function(f) { return f.status === 'stale'; }).length;
    const missing = files.filter(function(f) { return f.status === 'missing'; }).length;
    const hr = document.getElementById('health-rows');
    hr.innerHTML = [
      ['Up to date', ok, 'ok'],
      ['Stale', stale, 'stale'],
      ['Missing', missing, 'missing'],
    ].map(function(item) {
      return '<div class="health-row"><span>' + item[0] + '</span>' +
        '<span class="badge badge-' + item[2] + '">' + item[1] + ' files</span></div>';
    }).join('');
  } catch (e) {}

  try {
    const r = await fetch(API + '/api/sessions');
    const sessions = await r.json();
    const el = document.getElementById('recent-sessions');
    if (!sessions.length) { el.innerHTML = '<div class="no-data">No sessions yet</div>'; return; }
    el.innerHTML = sessions.slice(0, 5).map(function(s) {
      return '<div style="border-bottom:1px solid #21262d;padding:6px 0;">' +
        '<div style="font-size:13px;color:#c9d1d9;">' + (s.project || s.id) + '</div>' +
        '<div style="font-size:11px;color:#8b949e;">' +
        (s.decisions || []).length + ' decisions \u00b7 ' +
        (s.code_areas || []).length + ' code areas' +
        (s.started_at ? ' \u00b7 ' + reltime(s.started_at) : '') +
        '</div></div>';
    }).join('');
  } catch (e) {}
}

async function loadFiles() {
  const el = document.getElementById('file-rows');
  el.innerHTML = '<div class="no-data"><div class="spinner"></div></div>';
  try {
    const r = await fetch(API + '/api/files');
    allFiles = await r.json();
    renderFiles(allFiles);
  } catch (e) {
    el.innerHTML = '<div class="no-data">Failed to load files</div>';
  }
}

function renderFiles(files) {
  const el = document.getElementById('file-rows');
  if (!files.length) { el.innerHTML = '<div class="no-data">No files indexed yet</div>'; return; }
  el.innerHTML = files.map(function(f) {
    return '<div class="table-row">' +
      '<div class="file-path" title="' + f.path + '">' + f.path + '</div>' +
      '<div style="color:#8b949e">' + f.chunks + '</div>' +
      '<div><span class="badge badge-' + f.status + '">' + f.status + '</span></div>' +
      '<div class="row-actions">' +
      '<button class="btn-icon" title="Reindex" onclick="reindexFile(' + JSON.stringify(f.path) + ')">&#8635;</button>' +
      '<button class="btn-icon" style="color:#f85149" title="Delete" onclick="deleteFile(' + JSON.stringify(f.path) + ')">&#10005;</button>' +
      '</div></div>';
  }).join('');
}

function filterFiles(query) {
  const q = query.toLowerCase();
  renderFiles(q ? allFiles.filter(function(f) { return f.path.toLowerCase().includes(q); }) : allFiles);
}

async function loadSessions() {
  const el = document.getElementById('session-list');
  el.innerHTML = '<div class="no-data"><div class="spinner"></div></div>';
  try {
    const r = await fetch(API + '/api/sessions');
    const sessions = await r.json();
    if (!sessions.length) { el.innerHTML = '<div class="no-data">No sessions recorded yet</div>'; return; }
    el.innerHTML = sessions.map(function(s, i) {
      const isActive = !s.ended_at;
      const decisions = s.decisions || [];
      const codeAreas = s.code_areas || [];
      return '<div class="session-card">' +
        '<div class="session-header" onclick="toggleSession(' + i + ')">' +
        '<div><div class="session-name">' + (s.project || s.id) + '</div>' +
        '<div class="session-meta">' + decisions.length + ' decisions \u00b7 ' + codeAreas.length + ' code areas' +
        (s.started_at ? ' \u00b7 ' + reltime(s.started_at) : '') + '</div></div>' +
        '<span class="badge ' + (isActive ? 'badge-active' : 'badge-closed') + '">' + (isActive ? 'active' : 'closed') + '</span>' +
        '</div>' +
        (decisions.length ? '<div class="session-body" id="sb-' + i + '">' +
          '<div style="font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:#8b949e;margin-bottom:6px;">Decisions</div>' +
          decisions.map(function(d) { return '<div class="decision-item">' + d.decision + '</div>'; }).join('') +
          '</div>' : '') +
        '</div>';
    }).join('');
  } catch (e) {
    el.innerHTML = '<div class="no-data">Failed to load sessions</div>';
  }
}

function toggleSession(i) {
  const el = document.getElementById('sb-' + i);
  if (el) el.classList.toggle('open');
}

async function loadSavings() {
  try {
    const r = await fetch(API + '/api/savings');
    const d = await r.json();
    const el = document.getElementById('savings-detail');
    const usedPct = d.baseline_tokens > 0 ? Math.round(d.served_tokens / d.baseline_tokens * 100) : 0;
    el.innerHTML =
      '<div class="bar-label"><span style="color:#c9d1d9">With CCE</span><span style="color:#58a6ff">' + (d.served_tokens || 0).toLocaleString() + '</span></div>' +
      '<div class="bar-track"><div class="bar-fill" style="background:#58a6ff;width:' + usedPct + '%"></div></div>' +
      '<div class="bar-label"><span style="color:#8b949e">Without CCE</span><span style="color:#8b949e">' + (d.baseline_tokens || 0).toLocaleString() + '</span></div>' +
      '<div class="bar-track"><div class="bar-fill" style="background:#30363d;width:100%"></div></div>' +
      '<div style="display:flex;justify-content:space-between;padding-top:10px;border-top:1px solid #21262d;font-size:13px;">' +
      '<span style="color:#8b949e">Saved</span>' +
      '<span style="color:#3fb950;font-weight:600">' + (d.tokens_saved || 0).toLocaleString() + ' tokens (' + (d.savings_pct || 0) + '%)</span>' +
      '</div>';
  } catch (e) {}
  updateCompButtons(currentOutputLevel);
}

function updateCompButtons(level) {
  document.querySelectorAll('.comp-btn').forEach(function(btn) {
    btn.classList.toggle('active', btn.textContent === level);
  });
}

async function doReindex(full) {
  const btn = document.getElementById(full ? 'btn-reindex-full' : 'btn-reindex-changed');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';
  try {
    const r = await fetch(API + '/api/reindex', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({full: full})
    });
    const d = await r.json();
    if (d.errors && d.errors.length) toast('Reindex errors: ' + d.errors[0]);
    else toast('Reindexed ' + d.indexed_files.length + ' files (' + d.total_chunks + ' chunks)');
    loadStatus();
  } catch (e) {
    toast('Reindex failed');
  } finally {
    btn.disabled = false;
    btn.textContent = full ? 'Full reindex' : 'Reindex changed';
  }
}

async function reindexFile(path) {
  try {
    await fetch(API + '/api/reindex/' + encodeURIComponent(path), {method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}'});
    toast('Reindexed ' + path);
    loadFiles();
    loadStatus();
  } catch (e) { toast('Failed'); }
}

async function deleteFile(path) {
  if (!confirm('Remove ' + path + ' from the index?')) return;
  try {
    await fetch(API + '/api/files/' + encodeURIComponent(path), {method: 'DELETE'});
    toast('Deleted ' + path);
    loadFiles();
    loadStatus();
  } catch (e) { toast('Failed'); }
}

async function doClear() {
  if (!confirm('Clear the entire index? This cannot be undone.')) return;
  try {
    await fetch(API + '/api/clear', {method: 'POST'});
    toast('Index cleared');
    loadStatus();
    loadFiles();
  } catch (e) { toast('Failed'); }
}

async function doExport() {
  window.location.href = API + '/api/export';
}

async function setCompression(level) {
  try {
    await fetch(API + '/api/compression', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({level: level})
    });
    currentOutputLevel = level;
    updateCompButtons(level);
    toast('Compression set to ' + level);
  } catch (e) { toast('Failed'); }
}

loadStatus();
setInterval(loadStatus, 5000);
</script>
</body>
</html>"""
