"""Embedded HTML page for the CCE dashboard.

Single-file SPA. Fetches data from /api/* on tab switch.
Polls /api/status every 5 seconds for live updates.
No external dependencies — all CSS and JS inline.
Grafana-inspired dark theme.
"""

PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CCE Dashboard</title>
<style>
:root {
  --bg:        #111217;
  --bg2:       #0d0f13;
  --panel:     #181b1f;
  --panel2:    #1e2128;
  --panel3:    #23272e;
  --border:    #2d3035;
  --border2:   #3a3f47;
  --text:      #d8dce2;
  --text2:     #8e97a5;
  --text3:     #555d6b;
  --blue:      #5794f2;
  --blue-bg:   rgba(87,148,242,.1);
  --green:     #73bf69;
  --green-bg:  rgba(115,191,105,.1);
  --yellow:    #f2cc0c;
  --yellow-bg: rgba(242,204,12,.1);
  --red:       #f15f5f;
  --red-bg:    rgba(241,95,95,.1);
  --orange:    #ff9830;
  --orange-bg: rgba(255,152,48,.1);
  --purple:    #b877d9;
  --purple-bg: rgba(184,119,217,.1);
  --mono: "JetBrains Mono","Fira Code","Cascadia Code","SF Mono",monospace;
  --sans: Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  --r: 3px;
  --r2: 5px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; }
body { background: var(--bg2); color: var(--text); font-family: var(--sans); font-size: 13px; display: flex; flex-direction: column; }

/* ── Top bar ─────────────────────────────────────── */

.topbar {
  height: 41px;
  min-height: 41px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 0;
  z-index: 10;
}

.topbar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 16px;
  border-right: 1px solid var(--border);
  margin-right: 16px;
  flex-shrink: 0;
}

.logo-icon {
  width: 22px;
  height: 22px;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  border-radius: var(--r);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 900;
  color: #fff;
  letter-spacing: -.5px;
  font-family: var(--mono);
}

.topbar-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: .1px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text2);
}

.breadcrumb-sep { color: var(--text3); }

.breadcrumb-project {
  font-family: var(--mono);
  font-size: 11.5px;
  color: var(--blue);
  background: var(--blue-bg);
  padding: 2px 8px;
  border-radius: var(--r);
  border: 1px solid rgba(87,148,242,.2);
}

.topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text3);
  font-family: var(--mono);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 0 0 rgba(115,191,105,.5);
  animation: livepulse 2s ease-in-out infinite;
}

@keyframes livepulse {
  0%   { box-shadow: 0 0 0 0 rgba(115,191,105,.5); }
  70%  { box-shadow: 0 0 0 5px rgba(115,191,105,0); }
  100% { box-shadow: 0 0 0 0 rgba(115,191,105,0); }
}

/* ── Layout ──────────────────────────────────────── */

.layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── Sidebar ─────────────────────────────────────── */

.sidebar {
  width: 200px;
  min-width: 200px;
  background: var(--panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-section-label {
  padding: 14px 14px 5px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text3);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 14px;
  color: var(--text2);
  font-size: 13px;
  cursor: pointer;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  transition: background .1s, color .1s;
  border-left: 3px solid transparent;
  position: relative;
}

.nav-item svg { flex-shrink: 0; opacity: .6; }
.nav-item:hover { background: var(--panel2); color: var(--text); }
.nav-item:hover svg { opacity: .85; }

.nav-item.active {
  background: var(--panel2);
  color: var(--text);
  border-left-color: var(--blue);
  font-weight: 500;
}

.nav-item.active svg { opacity: 1; color: var(--blue); }

.nav-count {
  margin-left: auto;
  font-size: 10.5px;
  font-family: var(--mono);
  color: var(--text3);
  background: var(--panel3);
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 22px;
  text-align: center;
}

.nav-item.active .nav-count { color: var(--blue); background: var(--blue-bg); }

.sidebar-spacer { flex: 1; }

/* ── Main ────────────────────────────────────────── */

.main {
  flex: 1;
  overflow-y: auto;
  background: var(--bg);
}

.page { display: none; padding: 20px 24px; }
.page.active { display: block; }

/* ── Page header ─────────────────────────────────── */

.page-hdr {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
}

.page-hdr-left {}
.page-hdr-title { font-size: 17px; font-weight: 700; color: var(--text); letter-spacing: -.2px; }
.page-hdr-sub   { font-size: 12px; color: var(--text2); margin-top: 2px; }

/* ── Stat row ────────────────────────────────────── */

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stat-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--r2);
  padding: 14px 16px;
  border-top: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.stat-card.blue   { border-top-color: var(--blue);   }
.stat-card.green  { border-top-color: var(--green);  }
.stat-card.yellow { border-top-color: var(--yellow); }
.stat-card.purple { border-top-color: var(--purple); }

.stat-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--text2);
  margin-bottom: 8px;
}

.stat-num {
  font-size: 30px;
  font-weight: 800;
  font-family: var(--mono);
  letter-spacing: -1.5px;
  line-height: 1;
  color: var(--text);
}

.stat-num.blue   { color: var(--blue);   }
.stat-num.green  { color: var(--green);  }
.stat-num.yellow { color: var(--yellow); }
.stat-num.purple { color: var(--purple); }

/* ── Panel grid ─────────────────────────────────── */

.panel-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--r2);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--panel2);
}

.panel-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--text2);
  display: flex;
  align-items: center;
  gap: 6px;
}

.panel-title svg { opacity: .5; }

.panel-body { padding: 12px 14px; }

/* ── Health rows ─────────────────────────────────── */

.health-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}

.health-row:last-child { border-bottom: none; }

.health-left {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  color: var(--text);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.ok      { background: var(--green);  box-shadow: 0 0 6px rgba(115,191,105,.5); }
.status-dot.stale   { background: var(--yellow); box-shadow: 0 0 6px rgba(242,204,12,.4); }
.status-dot.missing { background: var(--red);    box-shadow: 0 0 6px rgba(241,95,95,.4); }

/* ── Badges ──────────────────────────────────────── */

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--r);
  font-size: 11px;
  font-weight: 600;
  font-family: var(--mono);
  border: 1px solid transparent;
}

.badge::before {
  content: '';
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.badge-ok      { background: var(--green-bg);  color: var(--green);  border-color: rgba(115,191,105,.2); }
.badge-ok::before { background: var(--green); }
.badge-stale   { background: var(--yellow-bg); color: var(--yellow); border-color: rgba(242,204,12,.2); }
.badge-stale::before { background: var(--yellow); }
.badge-missing { background: var(--red-bg);    color: var(--red);    border-color: rgba(241,95,95,.2); }
.badge-missing::before { background: var(--red); }
.badge-active  { background: var(--blue-bg);   color: var(--blue);   border-color: rgba(87,148,242,.2); }
.badge-active::before { background: var(--blue); }
.badge-closed  { background: var(--panel3);    color: var(--text2);  border-color: var(--border); }
.badge-closed::before { background: var(--text3); }
.badge-num     { background: var(--panel3);    color: var(--text2);  border-color: var(--border); font-family: var(--mono); }
.badge-num::before { display: none; }

/* ── Buttons ─────────────────────────────────────── */

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--r2);
  font-size: 12.5px;
  font-weight: 500;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all .12s;
  font-family: var(--sans);
  white-space: nowrap;
}

.btn-primary {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
  box-shadow: 0 1px 4px rgba(87,148,242,.3);
}
.btn-primary:hover { background: #6aa3f5; box-shadow: 0 2px 8px rgba(87,148,242,.4); }

.btn-ghost {
  background: transparent;
  color: var(--text2);
  border-color: var(--border2);
}
.btn-ghost:hover { background: var(--panel2); color: var(--text); border-color: var(--border2); }

.btn-danger {
  background: transparent;
  color: var(--red);
  border-color: rgba(241,95,95,.3);
}
.btn-danger:hover { background: var(--red-bg); border-color: rgba(241,95,95,.5); }

.btn-row {
  display: flex;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid var(--border);
  background: var(--panel2);
}

.btn-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: var(--r);
  color: var(--text2);
  cursor: pointer;
  transition: all .12s;
  font-size: 11px;
  padding: 0;
}

.btn-icon:hover { background: var(--panel3); color: var(--text); border-color: var(--border2); }
.btn-icon.del:hover { background: var(--red-bg); color: var(--red); border-color: rgba(241,95,95,.3); }

/* ── Toolbar ─────────────────────────────────────── */

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.search-wrap { position: relative; flex: 1; max-width: 260px; }

.search-wrap .ico {
  position: absolute;
  left: 9px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text3);
  pointer-events: none;
  display: flex;
}

.search-input {
  width: 100%;
  background: var(--panel);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 7px 10px 7px 30px;
  border-radius: var(--r2);
  font-size: 12.5px;
  font-family: var(--sans);
  outline: none;
  transition: border-color .15s;
}

.search-input:focus { border-color: var(--blue); }
.search-input::placeholder { color: var(--text3); }

/* ── Data table ──────────────────────────────────── */

.data-table {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--r2);
  overflow: hidden;
}

.table-head {
  display: grid;
  grid-template-columns: minmax(0,1fr) 80px 110px 72px;
  padding: 8px 14px;
  background: var(--panel2);
  border-bottom: 1px solid var(--border);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: .7px;
  text-transform: uppercase;
  color: var(--text3);
  gap: 12px;
}

.table-row {
  display: grid;
  grid-template-columns: minmax(0,1fr) 80px 110px 72px;
  padding: 9px 14px;
  border-top: 1px solid var(--border);
  align-items: center;
  gap: 12px;
  transition: background .1s;
}

.table-row:nth-child(even) { background: rgba(255,255,255,.012); }
.table-row:hover { background: var(--panel2); }

.file-path {
  font-family: var(--mono);
  font-size: 11.5px;
  color: var(--blue);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chunk-num {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text2);
}

.row-acts { display: flex; gap: 4px; align-items: center; }

/* ── Empty state ─────────────────────────────────── */

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 8px;
  color: var(--text3);
}

.empty-icon { opacity: .25; }
.empty-title { font-size: 13px; font-weight: 600; color: var(--text2); }
.empty-hint  { font-size: 11.5px; color: var(--text3); }

/* ── Sessions ────────────────────────────────────── */

.session-list { display: flex; flex-direction: column; gap: 8px; }

.session-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--r2);
  overflow: hidden;
  transition: border-color .15s;
}

.session-card:hover { border-color: var(--border2); }

.session-header {
  display: flex;
  align-items: center;
  padding: 11px 14px;
  cursor: pointer;
  gap: 10px;
}

.session-header:hover { background: var(--panel2); }

.session-info { flex: 1; min-width: 0; }

.session-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  font-size: 11.5px;
  color: var(--text2);
  margin-top: 2px;
  font-family: var(--mono);
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.session-meta span { color: var(--text3); }
.session-meta b { color: var(--text2); font-weight: 400; }

.chevron {
  color: var(--text3);
  transition: transform .2s;
  flex-shrink: 0;
}

.chevron.open { transform: rotate(90deg); }

.session-body {
  display: none;
  border-top: 1px solid var(--border);
  padding: 12px 14px;
  background: var(--bg2);
}

.session-body.open { display: block; }

.decisions-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .8px;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: 8px;
}

.decision-item {
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--blue);
  border-radius: var(--r);
  padding: 7px 11px;
  font-size: 12.5px;
  color: var(--text);
  margin-bottom: 5px;
  line-height: 1.55;
}

/* ── Savings ─────────────────────────────────────── */

.bar-row { margin-bottom: 14px; }

.bar-meta {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 5px;
}

.bar-lbl { font-size: 12px; color: var(--text2); }
.bar-val { font-size: 12px; font-family: var(--mono); font-weight: 600; }
.bar-val.blue   { color: var(--blue);  }
.bar-val.muted  { color: var(--text3); }

.bar-track {
  height: 5px;
  background: var(--panel3);
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 5px;
  border-radius: 3px;
  transition: width .6s cubic-bezier(.4,0,.2,1);
}

.savings-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding: 12px 14px;
  background: var(--green-bg);
  border: 1px solid rgba(115,191,105,.2);
  border-radius: var(--r2);
}

.savings-summary-lbl { font-size: 12px; color: var(--text2); }

.savings-summary-val {
  font-size: 20px;
  font-weight: 800;
  font-family: var(--mono);
  color: var(--green);
  letter-spacing: -1px;
}

.savings-summary-pct {
  font-size: 12px;
  color: var(--green);
  opacity: .7;
  margin-left: 4px;
}

/* Compression */
.comp-label {
  font-size: 12px;
  color: var(--text2);
  margin-bottom: 10px;
  line-height: 1.6;
}

.comp-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.comp-btn {
  padding: 9px 4px;
  border-radius: var(--r);
  font-size: 11.5px;
  font-weight: 600;
  font-family: var(--mono);
  background: var(--panel2);
  border: 1px solid var(--border);
  color: var(--text2);
  cursor: pointer;
  text-align: center;
  transition: all .12s;
  letter-spacing: .3px;
}

.comp-btn:hover { border-color: var(--border2); color: var(--text); background: var(--panel3); }
.comp-btn.active { background: var(--blue-bg); border-color: rgba(87,148,242,.4); color: var(--blue); }

/* ── Banner ──────────────────────────────────────── */

.banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--blue-bg);
  border: 1px solid rgba(87,148,242,.25);
  border-radius: var(--r2);
  padding: 10px 14px;
  font-size: 12.5px;
  color: #7eb8ff;
  margin-bottom: 16px;
}

.banner code {
  font-family: var(--mono);
  background: rgba(87,148,242,.15);
  padding: 1px 6px;
  border-radius: var(--r);
  font-size: 11.5px;
}

/* ── Toast ───────────────────────────────────────── */

.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: var(--panel2);
  border: 1px solid var(--border2);
  border-left: 3px solid var(--blue);
  border-radius: var(--r2);
  padding: 10px 14px;
  font-size: 12.5px;
  color: var(--text);
  box-shadow: 0 4px 20px rgba(0,0,0,.5);
  opacity: 0;
  transform: translateX(12px);
  transition: opacity .18s, transform .18s;
  pointer-events: none;
  z-index: 200;
  max-width: 300px;
}

.toast.show { opacity: 1; transform: translateX(0); }

/* ── Spinner ─────────────────────────────────────── */

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 1.5px solid var(--border2);
  border-top-color: var(--blue);
  border-radius: 50%;
  animation: spin .6s linear infinite;
  vertical-align: middle;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Scrollbar ───────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--panel3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border2); }
</style>
</head>
<body>

<!-- Top bar -->
<div class="topbar">
  <div class="topbar-logo">
    <div class="logo-icon">CCE</div>
    <span class="topbar-title">Context Engine</span>
  </div>
  <div class="breadcrumb">
    <span>Dashboards</span>
    <span class="breadcrumb-sep">/</span>
    <span class="breadcrumb-project" id="nav-project">loading…</span>
  </div>
  <div class="topbar-right">
    <div class="live-badge">
      <div class="live-dot"></div>
      LIVE&nbsp;&nbsp;5s
    </div>
  </div>
</div>

<!-- Layout -->
<div class="layout">

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="nav-section-label">General</div>

    <button class="nav-item active" onclick="showPage('overview')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
      Overview
    </button>

    <button class="nav-item" onclick="showPage('files')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      Files
      <span class="nav-count" id="nav-files-count">—</span>
    </button>

    <button class="nav-item" onclick="showPage('sessions')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Sessions
      <span class="nav-count" id="nav-sessions-count">—</span>
    </button>

    <div class="nav-section-label" style="margin-top:4px">Analytics</div>

    <button class="nav-item" onclick="showPage('savings')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      Savings
    </button>

    <div class="sidebar-spacer"></div>
  </aside>

  <!-- Main content -->
  <main class="main">

    <!-- Overview -->
    <div class="page active" id="page-overview">
      <div class="page-hdr">
        <div class="page-hdr-left">
          <div class="page-hdr-title">Overview</div>
          <div class="page-hdr-sub">Index health, chunk metrics and recent activity</div>
        </div>
      </div>

      <div id="uninit-banner" class="banner" style="display:none">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        Index not initialised — run <code>cce init</code> then <code>cce index</code> in your project directory.
      </div>

      <div class="stat-row">
        <div class="stat-card blue">
          <div class="stat-label">Chunks indexed</div>
          <div class="stat-num blue" id="stat-chunks">—</div>
        </div>
        <div class="stat-card green">
          <div class="stat-label">Files indexed</div>
          <div class="stat-num green" id="stat-files">—</div>
        </div>
        <div class="stat-card yellow">
          <div class="stat-label">Queries run</div>
          <div class="stat-num yellow" id="stat-queries">—</div>
        </div>
        <div class="stat-card purple">
          <div class="stat-label">Tokens saved</div>
          <div class="stat-num purple" id="stat-saved">—</div>
        </div>
      </div>

      <div class="panel-row">
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              Index Health
            </div>
          </div>
          <div class="panel-body">
            <div id="health-rows"><div class="empty"><div class="spinner"></div></div></div>
          </div>
          <div class="btn-row">
            <button class="btn btn-primary" onclick="doReindex(false)" id="btn-reindex-changed">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              Reindex changed
            </button>
            <button class="btn btn-ghost" onclick="doReindex(true)" id="btn-reindex-full">Full reindex</button>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              Recent Sessions
            </div>
          </div>
          <div class="panel-body">
            <div id="recent-sessions"><div class="empty"><div class="spinner"></div></div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Files -->
    <div class="page" id="page-files">
      <div class="page-hdr">
        <div class="page-hdr-left">
          <div class="page-hdr-title">Files</div>
          <div class="page-hdr-sub">Indexed files with staleness status and chunk counts</div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-ghost" onclick="doExport()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Export
          </button>
          <button class="btn btn-danger" onclick="doClear()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
            Clear index
          </button>
        </div>
      </div>
      <div class="toolbar">
        <div class="search-wrap">
          <span class="ico">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </span>
          <input class="search-input" placeholder="Filter by path…" oninput="filterFiles(this.value)">
        </div>
      </div>
      <div class="data-table">
        <div class="table-head"><div>Path</div><div>Chunks</div><div>Status</div><div>Actions</div></div>
        <div id="file-rows"><div class="empty"><div class="spinner"></div></div></div>
      </div>
    </div>

    <!-- Sessions -->
    <div class="page" id="page-sessions">
      <div class="page-hdr">
        <div class="page-hdr-left">
          <div class="page-hdr-title">Sessions</div>
          <div class="page-hdr-sub">Captured Claude coding sessions and architectural decisions</div>
        </div>
      </div>
      <div id="session-list"><div class="empty"><div class="spinner"></div></div></div>
    </div>

    <!-- Savings -->
    <div class="page" id="page-savings">
      <div class="page-hdr">
        <div class="page-hdr-left">
          <div class="page-hdr-title">Savings</div>
          <div class="page-hdr-sub">Token reduction metrics and output compression settings</div>
        </div>
      </div>
      <div class="panel-row">
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Token Usage
            </div>
          </div>
          <div class="panel-body">
            <div id="savings-detail"><div class="empty"><div class="spinner"></div></div></div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
              Output Compression
            </div>
          </div>
          <div class="panel-body">
            <p class="comp-label">Controls how Claude compresses its responses. Higher levels reduce output token usage at the cost of verbosity.</p>
            <div class="comp-grid" id="comp-buttons">
              <button class="comp-btn" onclick="setCompression('off')">off</button>
              <button class="comp-btn" onclick="setCompression('lite')">lite</button>
              <button class="comp-btn" onclick="setCompression('standard')">standard</button>
              <button class="comp-btn" onclick="setCompression('max')">max</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </main>
</div>

<div class="toast" id="toast"></div>

<script>
var API = '';
var allFiles = [];
var currentLevel = 'standard';
var PAGES = ['overview','files','sessions','savings'];

function showPage(name) {
  PAGES.forEach(function(p) {
    document.getElementById('page-' + p).classList.toggle('active', p === name);
  });
  document.querySelectorAll('.nav-item').forEach(function(el, i) {
    el.classList.toggle('active', PAGES[i] === name);
  });
  if (name === 'files')    loadFiles();
  if (name === 'sessions') loadSessions();
  if (name === 'savings')  loadSavings();
}

function toast(msg) {
  var el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(function() { el.classList.remove('show'); }, 3000);
}

function reltime(ts) {
  var d = Math.floor(Date.now()/1000 - ts);
  if (d < 60)    return 'just now';
  if (d < 3600)  return Math.floor(d/60) + 'm ago';
  if (d < 86400) return Math.floor(d/3600) + 'h ago';
  return Math.floor(d/86400) + 'd ago';
}

function fmt(n) { return Number(n).toLocaleString(); }

var SVG = {
  refresh: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
  trash:   '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>',
  chevron: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
};

async function loadStatus() {
  try {
    var r = await fetch(API + '/api/status');
    var d = await r.json();
    document.getElementById('nav-project').textContent   = d.project || '';
    document.getElementById('stat-chunks').textContent   = fmt(d.chunks);
    document.getElementById('stat-files').textContent    = fmt(d.files);
    document.getElementById('stat-queries').textContent  = fmt(d.queries);
    document.getElementById('stat-saved').textContent    = d.tokens_saved_pct + '%';
    document.getElementById('uninit-banner').style.display = d.initialized ? 'none' : 'flex';
    currentLevel = d.output_level;
    refreshCompButtons(d.output_level);
    loadOverviewPanels();
  } catch(e) {}
}

async function loadOverviewPanels() {
  try {
    var r = await fetch(API + '/api/files');
    var files = await r.json();
    document.getElementById('nav-files-count').textContent = files.length;
    var ok      = files.filter(function(f){ return f.status==='ok';      }).length;
    var stale   = files.filter(function(f){ return f.status==='stale';   }).length;
    var missing = files.filter(function(f){ return f.status==='missing'; }).length;
    document.getElementById('health-rows').innerHTML =
      [['ok','Up to date',ok],['stale','Stale',stale],['missing','Missing',missing]].map(function(row) {
        return '<div class="health-row">' +
          '<div class="health-left"><span class="status-dot '+row[0]+'"></span>'+row[1]+'</div>' +
          '<span class="badge badge-num">'+row[2]+'</span>' +
          '</div>';
      }).join('');
  } catch(e) {}

  try {
    var r2 = await fetch(API + '/api/sessions');
    var sessions = await r2.json();
    document.getElementById('nav-sessions-count').textContent = sessions.length;
    var el = document.getElementById('recent-sessions');
    if (!sessions.length) {
      el.innerHTML = '<div class="empty"><span class="empty-title">No sessions yet</span></div>';
      return;
    }
    el.innerHTML = sessions.slice(0,5).map(function(s) {
      var decs  = (s.decisions||[]).length;
      var areas = (s.code_areas||[]).length;
      var isActive = !s.ended_at;
      return '<div class="health-row">' +
        '<div>' +
          '<div style="font-size:12.5px;font-weight:600;color:var(--text)">'+(s.project||s.id)+'</div>' +
          '<div style="font-size:11px;color:var(--text2);font-family:var(--mono);margin-top:2px">'+
            decs+' dec &middot; '+areas+' areas'+(s.started_at?' &middot; '+reltime(s.started_at):'')+
          '</div>'+
        '</div>' +
        '<span class="badge '+(isActive?'badge-active':'badge-closed')+'">'+(isActive?'active':'closed')+'</span>' +
        '</div>';
    }).join('');
  } catch(e) {}
}

async function loadFiles() {
  var el = document.getElementById('file-rows');
  el.innerHTML = '<div class="empty"><div class="spinner"></div></div>';
  try {
    var r = await fetch(API + '/api/files');
    allFiles = await r.json();
    renderFiles(allFiles);
  } catch(e) {
    el.innerHTML = '<div class="empty"><span class="empty-title">Failed to load</span></div>';
  }
}

function renderFiles(files) {
  var el = document.getElementById('file-rows');
  if (!files.length) {
    el.innerHTML = '<div class="empty">' +
      '<svg class="empty-icon" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' +
      '<span class="empty-title">No files indexed</span>' +
      '<span class="empty-hint">Run <code style="font-family:var(--mono)">cce index</code> to index your project</span>' +
      '</div>';
    return;
  }
  el.innerHTML = files.map(function(f) {
    return '<div class="table-row">' +
      '<div class="file-path" title="'+f.path+'">'+f.path+'</div>' +
      '<div class="chunk-num">'+f.chunks+'</div>' +
      '<div><span class="badge badge-'+f.status+'">'+f.status+'</span></div>' +
      '<div class="row-acts">' +
        '<button class="btn-icon" title="Reindex" onclick="reindexFile('+JSON.stringify(f.path)+')">'+SVG.refresh+'</button>' +
        '<button class="btn-icon del" title="Remove" onclick="deleteFile('+JSON.stringify(f.path)+')">'+SVG.trash+'</button>' +
      '</div>' +
    '</div>';
  }).join('');
}

function filterFiles(q) {
  q = q.toLowerCase();
  renderFiles(q ? allFiles.filter(function(f){ return f.path.toLowerCase().includes(q); }) : allFiles);
}

async function loadSessions() {
  var el = document.getElementById('session-list');
  el.innerHTML = '<div class="empty"><div class="spinner"></div></div>';
  try {
    var r = await fetch(API + '/api/sessions');
    var sessions = await r.json();
    if (!sessions.length) {
      el.innerHTML = '<div class="empty">' +
        '<svg class="empty-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
        '<span class="empty-title">No sessions recorded</span>' +
        '<span class="empty-hint">Sessions are captured during Claude coding sessions</span>' +
        '</div>';
      return;
    }
    el.innerHTML = '<div class="session-list">' + sessions.map(function(s, i) {
      var isActive = !s.ended_at;
      var decs  = s.decisions || [];
      var areas = s.code_areas || [];
      return '<div class="session-card">' +
        '<div class="session-header" onclick="toggleSession('+i+')">' +
          '<div class="chevron" id="chev-'+i+'">'+SVG.chevron+'</div>' +
          '<div class="session-info">' +
            '<div class="session-name">'+(s.project||s.id)+'</div>' +
            '<div class="session-meta">' +
              '<b>'+decs.length+'</b><span>decisions</span>' +
              '<b>'+areas.length+'</b><span>code areas</span>' +
              (s.started_at ? '<b>'+reltime(s.started_at)+'</b>' : '') +
            '</div>' +
          '</div>' +
          '<span class="badge '+(isActive?'badge-active':'badge-closed')+'">'+(isActive?'active':'closed')+'</span>' +
        '</div>' +
        (decs.length ?
          '<div class="session-body" id="sb-'+i+'">' +
            '<div class="decisions-label">Decisions</div>' +
            decs.map(function(d){ return '<div class="decision-item">'+d.decision+'</div>'; }).join('') +
          '</div>'
        : '') +
      '</div>';
    }).join('') + '</div>';
  } catch(e) {
    el.innerHTML = '<div class="empty"><span class="empty-title">Failed to load</span></div>';
  }
}

function toggleSession(i) {
  var body = document.getElementById('sb-' + i);
  var chev = document.getElementById('chev-' + i);
  if (body) { body.classList.toggle('open'); }
  if (chev) { chev.classList.toggle('open'); }
}

async function loadSavings() {
  try {
    var r = await fetch(API + '/api/savings');
    var d = await r.json();
    var el = document.getElementById('savings-detail');
    var usedPct = d.baseline_tokens > 0 ? Math.round(d.served_tokens / d.baseline_tokens * 100) : 0;
    el.innerHTML =
      '<div class="bar-row">' +
        '<div class="bar-meta"><span class="bar-lbl">With CCE</span><span class="bar-val blue">'+fmt(d.served_tokens||0)+' tokens</span></div>' +
        '<div class="bar-track"><div class="bar-fill" style="background:var(--blue);width:'+usedPct+'%"></div></div>' +
      '</div>' +
      '<div class="bar-row">' +
        '<div class="bar-meta"><span class="bar-lbl">Without CCE</span><span class="bar-val muted">'+fmt(d.baseline_tokens||0)+' tokens</span></div>' +
        '<div class="bar-track"><div class="bar-fill" style="background:var(--panel3);width:100%"></div></div>' +
      '</div>' +
      '<div class="savings-summary">' +
        '<div>' +
          '<div class="savings-summary-lbl">Total tokens saved</div>' +
          '<div style="font-size:11px;color:var(--text3);margin-top:2px;font-family:var(--mono)">'+fmt(d.queries||0)+' queries processed</div>' +
        '</div>' +
        '<div>' +
          '<span class="savings-summary-val">'+fmt(d.tokens_saved||0)+'</span>' +
          '<span class="savings-summary-pct">('+( d.savings_pct||0)+'%)</span>' +
        '</div>' +
      '</div>';
  } catch(e) {}
  refreshCompButtons(currentLevel);
}

function refreshCompButtons(level) {
  document.querySelectorAll('.comp-btn').forEach(function(btn) {
    btn.classList.toggle('active', btn.textContent.trim() === level);
  });
}

async function doReindex(full) {
  var id = full ? 'btn-reindex-full' : 'btn-reindex-changed';
  var btn = document.getElementById(id);
  var orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Indexing…';
  try {
    var r = await fetch(API + '/api/reindex', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({full: full})
    });
    var d = await r.json();
    if (d.errors && d.errors.length) toast('Error: ' + d.errors[0]);
    else toast('Indexed ' + d.indexed_files.length + ' files — ' + fmt(d.total_chunks) + ' chunks');
    loadStatus();
  } catch(e) { toast('Reindex failed'); }
  finally { btn.disabled = false; btn.innerHTML = orig; }
}

async function reindexFile(path) {
  try {
    await fetch(API + '/api/reindex/' + encodeURIComponent(path), {method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    toast('Reindexed ' + path);
    loadFiles(); loadStatus();
  } catch(e) { toast('Failed'); }
}

async function deleteFile(path) {
  if (!confirm('Remove "' + path + '" from index?')) return;
  try {
    await fetch(API + '/api/files/' + encodeURIComponent(path), {method:'DELETE'});
    toast('Removed ' + path);
    loadFiles(); loadStatus();
  } catch(e) { toast('Failed'); }
}

async function doClear() {
  if (!confirm('Clear entire index? This cannot be undone.')) return;
  try {
    await fetch(API + '/api/clear', {method:'POST'});
    toast('Index cleared');
    loadStatus(); loadFiles();
  } catch(e) { toast('Failed'); }
}

async function doExport() { window.location.href = API + '/api/export'; }

async function setCompression(level) {
  try {
    await fetch(API + '/api/compression', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({level: level})
    });
    currentLevel = level;
    refreshCompButtons(level);
    toast('Compression: ' + level);
  } catch(e) { toast('Failed'); }
}

loadStatus();
setInterval(loadStatus, 5000);
</script>
</body>
</html>"""
