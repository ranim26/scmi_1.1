"""
SysMon Server - Serveur de surveillance
Reçoit les données des agents et les affiche sur le dashboard
"""

from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone
import json
import threading
import time
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "sysmon_secret_2024"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ─── STOCKAGE EN MEMOIRE ──────────────────────────────────────────────────────
agents = {}  # agent_id -> dernières données
agents_lock = threading.Lock()

OFFLINE_TIMEOUT = 120  # secondes sans nouvelles = hors ligne

# ─── DASHBOARD HTML ───────────────────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SysMon Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<style>
  :root {
    --bg: #0f1117;
    --card: #1a1d27;
    --card2: #22263a;
    --border: #2e3250;
    --accent: #4f8ef7;
    --green: #22c55e;
    --yellow: #f59e0b;
    --red: #ef4444;
    --orange: #f97316;
    --text: #e2e8f0;
    --muted: #64748b;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; min-height: 100vh; }

  /* HEADER */
  .header {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
  }
  .header h1 { font-size: 20px; font-weight: 700; color: var(--accent); letter-spacing: 1px; }
  .header-right { display: flex; align-items: center; gap: 16px; }
  .live-dot { width: 10px; height: 10px; background: var(--green); border-radius: 50%; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
  .last-update { font-size: 12px; color: var(--muted); }

  /* STATS GLOBALES */
  .global-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding: 24px 32px 0;
  }
  .gstat {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
  }
  .gstat-val { font-size: 28px; font-weight: 700; color: var(--accent); }
  .gstat-label { font-size: 12px; color: var(--muted); margin-top: 4px; }

  /* GRILLE AGENTS */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
    gap: 20px;
    padding: 24px 32px;
  }

  /* CARTE AGENT */
  .agent-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
    transition: border-color .2s;
  }
  .agent-card:hover { border-color: var(--accent); }
  .agent-card.offline { border-color: var(--red); opacity: .7; }

  /* HEADER CARTE */
  .agent-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    background: var(--card2);
    border-bottom: 1px solid var(--border);
  }
  .agent-name { font-size: 15px; font-weight: 700; }
  .agent-os { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
  }
  .status-online { background: rgba(34,197,94,.15); color: var(--green); }
  .status-offline { background: rgba(239,68,68,.15); color: var(--red); }

  /* BODY CARTE */
  .agent-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 14px; }

  /* METRIQUE */
  .metric-row { display: flex; flex-direction: column; gap: 4px; }
  .metric-header { display: flex; justify-content: space-between; align-items: center; }
  .metric-label { font-size: 12px; color: var(--muted); }
  .metric-val { font-size: 13px; font-weight: 600; }
  .bar-bg { height: 8px; background: rgba(255,255,255,.06); border-radius: 4px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width .5s ease; }
  .bar-green { background: var(--green); }
  .bar-yellow { background: var(--yellow); }
  .bar-red { background: var(--red); }

  /* GRILLE 2 COLONNES */
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

  /* MINI STAT */
  .mini-stat {
    background: rgba(255,255,255,.03);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
  }
  .mini-stat-label { font-size: 11px; color: var(--muted); }
  .mini-stat-val { font-size: 15px; font-weight: 700; margin-top: 2px; }

  /* DISQUES */
  .disks { display: flex; flex-direction: column; gap: 8px; }
  .disk-row { display: flex; flex-direction: column; gap: 4px; }
  .disk-info { display: flex; justify-content: space-between; font-size: 12px; }
  .disk-name { color: var(--muted); }

  /* RÉSEAU */
  .net-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }

  /* PROCESSUS */
  .proc-list { display: flex; flex-direction: column; gap: 4px; }
  .proc-row {
    display: grid;
    grid-template-columns: 1fr 70px 70px;
    font-size: 11px;
    padding: 4px 8px;
    background: rgba(255,255,255,.02);
    border-radius: 6px;
    gap: 8px;
    align-items: center;
  }
  .proc-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .proc-val { text-align: right; color: var(--muted); }
  .proc-header { color: var(--muted); font-weight: 600; }

  /* TEMPÉRATURE */
  .temp-grid { display: flex; flex-wrap: wrap; gap: 8px; }
  .temp-badge {
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    background: rgba(249,115,22,.15);
    color: var(--orange);
  }
  .temp-badge.hot { background: rgba(239,68,68,.15); color: var(--red); }

  /* ALERTE */
  .alert-banner {
    background: rgba(239,68,68,.1);
    border: 1px solid rgba(239,68,68,.3);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    color: var(--red);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* PIED CARTE */
  .agent-footer {
    padding: 8px 20px;
    background: var(--card2);
    border-top: 1px solid var(--border);
    font-size: 11px;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
  }

  /* VIDE */
  .empty {
    grid-column: 1/-1;
    text-align: center;
    padding: 80px 20px;
    color: var(--muted);
  }
  .empty h2 { font-size: 22px; margin-bottom: 8px; }

  /* SECTION TITRE */
  .section-title {
    font-size: 11px;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }

  /* BOUTON APPLICATIONS */
  .btn-apps {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    background: rgba(79,142,247,.1);
    border: 1px solid rgba(79,142,247,.3);
    border-radius: 8px;
    padding: 8px 14px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background .2s;
  }
  .btn-apps:hover { background: rgba(79,142,247,.2); }
  .apps-panel { display: none; margin-top: 8px; }
  .apps-panel.open { display: block; }

  @media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; padding: 12px; }
    .global-stats { grid-template-columns: repeat(2,1fr); padding: 12px; }
    .header { padding: 12px 16px; }
  }

  /* STAT CLIQUABLE */
  .gstat.clickable { cursor: pointer; transition: border-color .2s; }
  .gstat.clickable:hover { border-color: var(--yellow); }

  /* APPS OBLIGATOIRES */
  .required-badge {
    background: rgba(239,68,68,.15);
    border: 1px solid rgba(239,68,68,.3);
    color: var(--red);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
  }
  .btn-add-required {
    background: rgba(249,115,22,.15);
    border: 1px solid rgba(249,115,22,.3);
    color: var(--orange);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;
  }
  .btn-add-required:hover { background: rgba(249,115,22,.3); }
  .btn-remove-required {
    background: rgba(100,116,139,.15);
    border: 1px solid rgba(100,116,139,.3);
    color: var(--muted);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;
  }
  .required-list { margin-bottom: 16px; }
  .required-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(239,68,68,.05);
    border: 1px solid rgba(239,68,68,.2);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 12px;
  }
  .required-item-name { font-weight: 600; color: var(--text); }
  .alert-item.required-app {
    background: rgba(249,115,22,.08);
    border-color: rgba(249,115,22,.3);
  }

  /* FILTRE APPLICATIONS */
  .filter-input {
    width: 100%;
    background: rgba(255,255,255,.05);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    color: var(--text);
    font-size: 13px;
    margin-bottom: 12px;
  }
  .filter-input:focus { outline: none; border-color: var(--accent); }
  .app-filter-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    border-radius: 8px;
    background: rgba(255,255,255,.03);
    border: 1px solid var(--border);
    margin-bottom: 6px;
    font-size: 12px;
  }
  .app-filter-row.hidden-app { opacity: .4; }
  .btn-hide-app {
    background: rgba(239,68,68,.15);
    border: 1px solid rgba(239,68,68,.3);
    color: var(--red);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;
  }
  .btn-hide-app:hover { background: rgba(239,68,68,.3); }
  .btn-show-app {
    background: rgba(34,197,94,.15);
    border: 1px solid rgba(34,197,94,.3);
    color: var(--green);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;
  }
  .btn-reset {
    background: rgba(79,142,247,.15);
    border: 1px solid rgba(79,142,247,.3);
    color: var(--accent);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    cursor: pointer;
    margin-top: 8px;
  }

  /* MODAL ALERTES */
  .modal-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,.7);
    z-index: 1000;
    align-items: center;
    justify-content: center;
  }
  .modal-overlay.open { display: flex; }
  .modal {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    padding: 24px;
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  .modal-title { font-size: 18px; font-weight: 700; color: var(--yellow); }
  .modal-close {
    background: none;
    border: none;
    color: var(--muted);
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
  }
  .modal-close:hover { background: rgba(255,255,255,.1); color: var(--text); }
  .alert-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    background: rgba(239,68,68,.08);
    border: 1px solid rgba(239,68,68,.2);
    border-radius: 10px;
    margin-bottom: 10px;
  }
  .alert-item.offline {
    background: rgba(100,116,139,.08);
    border-color: rgba(100,116,139,.2);
  }
  .alert-icon { font-size: 20px; }
  .alert-info { flex: 1; }
  .alert-machine { font-size: 13px; font-weight: 700; margin-bottom: 3px; }
  .alert-msg { font-size: 12px; color: var(--muted); }
  .alert-time { font-size: 11px; color: var(--muted); margin-top: 4px; }
  .no-alerts {
    text-align: center;
    padding: 40px;
    color: var(--green);
    font-size: 15px;
  }
</style>
</head>
<body>

<div class="header">
  <h1>⚡ SysMon Dashboard</h1>
  <div class="header-right">
    <button onclick="openRequiredModal()" style="background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);color:var(--red);border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer;">
      🔴 Apps obligatoires
    </button>
    <button onclick="openFilterModal()" style="background:rgba(79,142,247,.15);border:1px solid rgba(79,142,247,.3);color:var(--accent);border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer;">
      📱 Filtrer apps
    </button>
    <div class="live-dot"></div>
    <span class="last-update" id="lastUpdate">En attente...</span>
  </div>
</div>

<div class="global-stats">
  <div class="gstat">
    <div class="gstat-val" id="g-total">0</div>
    <div class="gstat-label">Machines totales</div>
  </div>
  <div class="gstat">
    <div class="gstat-val" style="color:var(--green)" id="g-online">0</div>
    <div class="gstat-label">En ligne</div>
  </div>
  <div class="gstat">
    <div class="gstat-val" style="color:var(--red)" id="g-offline">0</div>
    <div class="gstat-label">Hors ligne</div>
  </div>
  <div class="gstat clickable" onclick="openAlertsModal()">
    <div class="gstat-val" style="color:var(--yellow)" id="g-alerts">0</div>
    <div class="gstat-label">Alertes &#x1F514;</div>
  </div>
</div>

<!-- MODAL ALERTES -->
<div class="modal-overlay" id="alertsModal" onclick="closeAlertsModal(event)">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title">🔔 Alertes et Pannes</span>
      <button class="modal-close" onclick="document.getElementById('alertsModal').classList.remove('open')">✕</button>
    </div>
    <div id="alertsList"></div>
  </div>
</div>

<!-- MODAL APPS OBLIGATOIRES -->
<div class="modal-overlay" id="requiredModal" onclick="closeRequiredModal(event)">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title">🔴 Applications Obligatoires</span>
      <button class="modal-close" onclick="document.getElementById('requiredModal').classList.remove('open')">✕</button>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:12px">
      Définissez les applications qui doivent toujours tourner. Une alerte apparaîtra si l'une s'arrête.
    </p>
    <div class="required-list" id="requiredList"></div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <input class="filter-input" id="requiredInput" placeholder="Nom de l'application (ex: chrome.exe)" style="margin:0;flex:1">
      <button onclick="addRequired()" style="background:rgba(239,68,68,.2);border:1px solid rgba(239,68,68,.4);color:var(--red);border-radius:8px;padding:8px 14px;font-size:12px;cursor:pointer;white-space:nowrap">
        ➕ Ajouter
      </button>
    </div>
    <p style="font-size:11px;color:var(--muted);margin-top:8px">
      💡 Cliquez sur "⭐ Surveiller" dans la liste des applications pour l'ajouter directement.
    </p>
  </div>
</div>

<!-- MODAL FILTRE APPLICATIONS -->
<div class="modal-overlay" id="filterModal" onclick="closeFilterModal(event)">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title">📱 Filtrer les Applications</span>
      <button class="modal-close" onclick="document.getElementById('filterModal').classList.remove('open')">✕</button>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:12px">
      Masquez les applications que vous ne voulez pas voir sur le dashboard.
    </p>
    <input class="filter-input" id="filterSearch" placeholder="🔍 Rechercher une application..." oninput="renderFilterList()">
    <div id="filterList"></div>
    <button class="btn-reset" onclick="resetFilters()">🔄 Réinitialiser tous les filtres</button>
  </div>
</div>

<div class="grid" id="agentGrid">
  <div class="empty">
    <h2>🔌 En attente des agents...</h2>
    <p>Installez l'agent sur les machines cibles</p>
  </div>
</div>

<script>
// Garde en memoire les panneaux ouverts
let openPanels = new Set();

function toggleApps(panelId, btn) {
  const panel = document.getElementById(panelId);
  const cardId = panelId.replace('apps-','');
  const arrow  = document.getElementById('arrow-' + cardId);
  if (panel.classList.contains('open')) {
    panel.classList.remove('open');
    arrow.textContent = '▼ Afficher';
    openPanels.delete(panelId);
  } else {
    panel.classList.add('open');
    arrow.textContent = '▲ Masquer';
    openPanels.add(panelId);
  }
}

// Restaure les panneaux ouverts apres chaque re-render
function restoreOpenPanels() {
  openPanels.forEach(panelId => {
    const panel = document.getElementById(panelId);
    const cardId = panelId.replace('apps-','');
    const arrow  = document.getElementById('arrow-' + cardId);
    if (panel) {
      panel.classList.add('open');
      if (arrow) arrow.textContent = '▲ Masquer';
    }
  });
}

function openAlertsModal() {
  const list = document.getElementById('alertsList');
  const items = [];

  Object.values(agentsData).forEach(agent => {
    const online = agent.online !== false;
    const p = agent.payload || {};
    const name = agent.agent_name;
    const ts = agent.last_seen ? new Date(agent.last_seen).toLocaleTimeString("fr-FR") : "—";

    if (!online) {
      items.push(`
        <div class="alert-item offline">
          <span class="alert-icon">🔴</span>
          <div class="alert-info">
            <div class="alert-machine">${name}</div>
            <div class="alert-msg">Machine hors ligne — aucune donnée reçue</div>
            <div class="alert-time">Dernière connexion : ${ts}</div>
          </div>
        </div>`);
    }

    const cpu = p.cpu?.usage_percent ?? 0;
    const ram = p.memory?.ram_percent ?? 0;

    if (cpu >= 90) items.push(`
      <div class="alert-item">
        <span class="alert-icon">🖥️</span>
        <div class="alert-info">
          <div class="alert-machine">${name}</div>
          <div class="alert-msg">CPU critique : ${cpu.toFixed(1)}% (seuil 90%)</div>
          <div class="alert-time">${ts}</div>
        </div>
      </div>`);

    if (ram >= 90) items.push(`
      <div class="alert-item">
        <span class="alert-icon">🧠</span>
        <div class="alert-info">
          <div class="alert-machine">${name}</div>
          <div class="alert-msg">RAM critique : ${ram.toFixed(1)}% (seuil 90%)</div>
          <div class="alert-time">${ts}</div>
        </div>
      </div>`);

    (p.disks || []).forEach(d => {
      if (d.percent >= 90) items.push(`
        <div class="alert-item">
          <span class="alert-icon">💾</span>
          <div class="alert-info">
            <div class="alert-machine">${name}</div>
            <div class="alert-msg">Disque ${d.device} presque plein : ${d.percent}% utilisé</div>
            <div class="alert-time">${ts}</div>
          </div>
        </div>`);
    });

    Object.values(p.temps || {}).flat().forEach(t => {
      if (t.current >= 80) items.push(`
        <div class="alert-item">
          <span class="alert-icon">🌡️</span>
          <div class="alert-info">
            <div class="alert-machine">${name}</div>
            <div class="alert-msg">Température critique : ${t.current}°C — ${t.label || "capteur"}</div>
            <div class="alert-time">${ts}</div>
          </div>
        </div>`);
    });

    // Apps obligatoires manquantes
    getMissingApps(agent).forEach(missing => {
      items.push(`
        <div class="alert-item required-app">
          <span class="alert-icon">🔴</span>
          <div class="alert-info">
            <div class="alert-machine">${name}</div>
            <div class="alert-msg">Application obligatoire arrêtée : <strong>${missing}</strong></div>
            <div class="alert-time">${ts}</div>
          </div>
        </div>`);
    });
  });

  list.innerHTML = items.length > 0
    ? items.join("")
    : `<div class="no-alerts">✅ Aucune alerte — toutes les machines fonctionnent normalement</div>`;

  document.getElementById('alertsModal').classList.add('open');
}

function closeAlertsModal(event) {
  if (event.target.id === 'alertsModal') {
    document.getElementById('alertsModal').classList.remove('open');
  }
}

// ─── FILTRE APPLICATIONS ──────────────────────────────────────────
let hiddenApps = JSON.parse(localStorage.getItem('hiddenApps') || '[]');

function saveHidden() {
  localStorage.setItem('hiddenApps', JSON.stringify(hiddenApps));
}

function isHidden(name) {
  return hiddenApps.includes(name.toLowerCase());
}

function hideApp(name) {
  const key = name.toLowerCase();
  if (!hiddenApps.includes(key)) hiddenApps.push(key);
  saveHidden();
  renderAll();
  renderFilterList();
}

function showApp(name) {
  hiddenApps = hiddenApps.filter(k => k !== name.toLowerCase());
  saveHidden();
  renderAll();
  renderFilterList();
}

function resetFilters() {
  hiddenApps = [];
  saveHidden();
  renderAll();
  renderFilterList();
}

function getAllApps() {
  const all = new Set();
  Object.values(agentsData).forEach(agent => {
    (agent.payload?.applications || []).forEach(a => all.add(a.name));
  });
  return Array.from(all).sort((a,b) => a.toLowerCase().localeCompare(b.toLowerCase()));
}

function renderFilterList() {
  const search = (document.getElementById('filterSearch')?.value || '').toLowerCase();
  const apps = getAllApps().filter(a => a.toLowerCase().includes(search));
  const list = document.getElementById('filterList');
  if (!list) return;

  if (apps.length === 0) {
    list.innerHTML = '<div style="text-align:center;color:var(--muted);padding:20px">Aucune application détectée</div>';
    return;
  }

  list.innerHTML = apps.map(name => `
    <div class="app-filter-row ${isHidden(name) ? 'hidden-app' : ''}">
      <span>${name}</span>
      ${isHidden(name)
        ? `<button class="btn-show-app" onclick="showApp('${name}')">✅ Afficher</button>`
        : `<button class="btn-hide-app" onclick="hideApp('${name}')">🚫 Masquer</button>`
      }
    </div>
  `).join('');
}

// ─── APPS OBLIGATOIRES ────────────────────────────────────────────
let requiredApps = JSON.parse(localStorage.getItem('requiredApps') || '[]');

function saveRequired() {
  localStorage.setItem('requiredApps', JSON.stringify(requiredApps));
}

function isRequired(name) {
  return requiredApps.includes(name.toLowerCase());
}

function addRequired(name) {
  const input = document.getElementById('requiredInput');
  const val = name || (input ? input.value.trim() : '');
  if (!val) return;
  const key = val.toLowerCase();
  if (!requiredApps.includes(key)) {
    requiredApps.push(key);
    saveRequired();
    renderAll();
    renderRequiredList();
    if (input) input.value = '';
  }
}

function removeRequired(name) {
  requiredApps = requiredApps.filter(k => k !== name.toLowerCase());
  saveRequired();
  renderAll();
  renderRequiredList();
}

function getMissingApps(agent) {
  const running = (agent.payload?.applications || []).map(a => a.name.toLowerCase());
  return requiredApps.filter(r => !running.includes(r));
}

function renderRequiredList() {
  const list = document.getElementById('requiredList');
  if (!list) return;
  if (requiredApps.length === 0) {
    list.innerHTML = '<div style="text-align:center;color:var(--muted);padding:16px;font-size:12px">Aucune application obligatoire définie</div>';
    return;
  }
  list.innerHTML = requiredApps.map(name => `
    <div class="required-item">
      <span class="required-item-name">🔴 ${name}</span>
      <button class="btn-remove-required" onclick="removeRequired('${name}')">🗑️ Supprimer</button>
    </div>
  `).join('');
}

function openRequiredModal() {
  renderRequiredList();
  document.getElementById('requiredModal').classList.add('open');
}

function closeRequiredModal(event) {
  if (event.target.id === 'requiredModal') {
    document.getElementById('requiredModal').classList.remove('open');
  }
}

function openFilterModal() {
  renderFilterList();
  document.getElementById('filterModal').classList.add('open');
}

function closeFilterModal(event) {
  if (event.target.id === 'filterModal') {
    document.getElementById('filterModal').classList.remove('open');
  }
}

const socket = io();
let agentsData = {};

socket.on("connect", () => {
  console.log("Connecté au serveur");
  fetch("/api/agents").then(r => r.json()).then(data => {
    agentsData = data;
    renderAll();
  });
});

socket.on("agent_update", (data) => {
  agentsData[data.agent_id] = data;
  renderAll();
  document.getElementById("lastUpdate").textContent =
    "Mise à jour : " + new Date().toLocaleTimeString("fr-FR");
});

socket.on("agent_offline", (data) => {
  if (agentsData[data.agent_id]) {
    agentsData[data.agent_id].online = false;
    renderAll();
  }
});

function barColor(pct) {
  if (pct >= 90) return "bar-red";
  if (pct >= 70) return "bar-yellow";
  return "bar-green";
}

function fmtBytes(mb) {
  if (mb === null || mb === undefined) return "—";
  if (mb > 1024) return (mb/1024).toFixed(1) + " GB";
  return mb.toFixed(1) + " MB";
}

function renderBar(pct) {
  const p = Math.min(pct || 0, 100);
  return `<div class="bar-bg"><div class="bar-fill ${barColor(p)}" style="width:${p}%"></div></div>`;
}

function renderAlerts(agent) {
  const alerts = [];
  const cpu = agent.payload?.cpu?.usage_percent;
  const ram = agent.payload?.memory?.ram_percent;
  if (cpu >= 90) alerts.push("⚠️ CPU critique : " + cpu + "%");
  if (ram >= 90) alerts.push("⚠️ RAM critique : " + ram + "%");
  (agent.payload?.disks || []).forEach(d => {
    if (d.percent >= 90) alerts.push("⚠️ Disque " + d.device + " presque plein : " + d.percent + "%");
  });
  const temps = agent.payload?.temps || {};
  Object.values(temps).flat().forEach(t => {
    if (t.current >= 80) alerts.push("🌡️ Température critique : " + t.current + "°C");
  });
  // Apps obligatoires manquantes
  getMissingApps(agent).forEach(name => {
    alerts.push("🔴 Application arrêtée : " + name);
  });
  return alerts;
}

function renderAgent(agent) {
  const online = agent.online !== false;
  const p = agent.payload || {};
  const cpu = p.cpu || {};
  const mem = p.memory || {};
  const net = p.network || {};
  const disks = p.disks || [];
  const procs = p.processes || [];
  const temps = p.temps || {};
  const sys = p.system || {};
  const alerts = renderAlerts(agent);

  // CPU
  const cpuPct = cpu.usage_percent ?? 0;
  // RAM
  const ramPct = mem.ram_percent ?? 0;
  const ramUsed = mem.ram_used_gb ?? "—";
  const ramTotal = mem.ram_total_gb ?? "—";

  // Températures
  let tempHtml = "";
  const allTemps = Object.values(temps).flat();
  if (allTemps.length > 0) {
    tempHtml = `
      <div>
        <div class="section-title">🌡️ Températures</div>
        <div class="temp-grid">
          ${allTemps.map(t => `
            <div class="temp-badge ${t.current >= 80 ? 'hot' : ''}">
              ${t.label || "—"} : ${t.current}°C
            </div>
          `).join("")}
        </div>
      </div>`;
  }

  // Disques
  const disksHtml = disks.length > 0 ? `
    <div>
      <div class="section-title">💾 Disques</div>
      <div class="disks">
        ${disks.map(d => `
          <div class="disk-row">
            <div class="disk-info">
              <span class="disk-name">${d.device} (${d.fstype || "—"})</span>
              <span>${d.used_gb} GB / ${d.total_gb} GB — ${d.percent}%</span>
            </div>
            ${renderBar(d.percent)}
          </div>
        `).join("")}
      </div>
    </div>` : "";

  // Réseau
  const netHtml = `
    <div>
      <div class="section-title">🌐 Réseau</div>
      <div class="net-grid">
        <div class="mini-stat">
          <div class="mini-stat-label">↑ Envoyé</div>
          <div class="mini-stat-val">${fmtBytes(net.bytes_sent_mb)}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-stat-label">↓ Reçu</div>
          <div class="mini-stat-val">${fmtBytes(net.bytes_recv_mb)}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-stat-label">Paquets envoyés</div>
          <div class="mini-stat-val">${net.packets_sent?.toLocaleString() ?? "—"}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-stat-label">Erreurs</div>
          <div class="mini-stat-val" style="color:${(net.errors_in+net.errors_out)>0?'var(--red)':'var(--green)'}">
            ${(net.errors_in ?? 0) + (net.errors_out ?? 0)}
          </div>
        </div>
      </div>
    </div>`;

  // Processus
  const procsHtml = procs.length > 0 ? `
    <div>
      <div class="section-title">⚙️ Processus (top CPU)</div>
      <div class="proc-list">
        <div class="proc-row proc-header">
          <span>Nom</span><span class="proc-val">CPU%</span><span class="proc-val">RAM%</span>
        </div>
        ${procs.map(pr => `
          <div class="proc-row">
            <span class="proc-name">${pr.name}</span>
            <span class="proc-val" style="color:${pr.cpu_pct>50?'var(--red)':pr.cpu_pct>20?'var(--yellow)':'var(--text)'}">${pr.cpu_pct}%</span>
            <span class="proc-val">${pr.mem_pct}%</span>
          </div>
        `).join("")}
      </div>
    </div>` : "";

  // Applications actives (avec filtre)
  const allApps = p.applications || [];
  const apps = allApps.filter(a => !isHidden(a.name));
  const cardId = agent.agent_id.replace(/-/g,"").substring(0,8);
  const appsHtml = apps.length > 0 ? `
    <div>
      <button class="btn-apps" onclick="toggleApps('apps-${cardId}', this)">
        <span>📱 Applications actives (${apps.length}${allApps.length !== apps.length ? ' / ' + allApps.length : ''})</span>
        <span id="arrow-${cardId}">▼ Afficher</span>
      </button>
      <div class="apps-panel proc-list" id="apps-${cardId}">
        <div style="height:8px"></div>
        <div class="proc-row proc-header" style="grid-template-columns:1fr 80px 80px 60px 60px">
          <span>Application</span>
          <span class="proc-val">Statut</span>
          <span class="proc-val">Durée</span>
          <span class="proc-val">RAM%</span>
          <span class="proc-val">Action</span>
        </div>
        ${apps.map(a => `
          <div class="proc-row" style="grid-template-columns:1fr 80px 80px 60px 60px">
            <span class="proc-name" title="${a.exe}">${a.name}</span>
            <span class="proc-val" style="color:${a.status==='running'?'var(--green)':'var(--muted)'}">
              ${a.status === 'running' ? '● actif' : '○ veille'}
            </span>
            <span class="proc-val">${a.uptime}</span>
            <span class="proc-val">${a.mem_pct}%</span>
            <span class="proc-val" style="display:flex;gap:4px">
              <button class="btn-hide-app" onclick="hideApp('${a.name}')" title="Masquer">🚫</button>
              <button class="btn-add-required" onclick="addRequired('${a.name}')" title="Surveiller" style="${isRequired('${a.name}') ? 'opacity:.4;cursor:default' : ''}">⭐</button>
            </span>
          </div>
        `).join("")}
      </div>
    </div>` : "";

  // Alertes
  const alertsHtml = alerts.map(a =>
    `<div class="alert-banner">${a}</div>`
  ).join("");

  // Timestamp
  const ts = agent.last_seen
    ? new Date(agent.last_seen).toLocaleTimeString("fr-FR")
    : "—";

  return `
    <div class="agent-card ${online ? "" : "offline"}" id="card-${agent.agent_id}">
      <div class="agent-header">
        <div>
          <div class="agent-name">${agent.agent_name}</div>
          <div class="agent-os">${sys.os || ""} ${sys.os_release || ""} — ${sys.hostname || ""}</div>
        </div>
        <span class="status-badge ${online ? "status-online" : "status-offline"}">
          ${online ? "● EN LIGNE" : "● HORS LIGNE"}
        </span>
      </div>
      <div class="agent-body">
        ${alertsHtml}

        <div class="two-col">
          <div>
            <div class="metric-row">
              <div class="metric-header">
                <span class="metric-label">🖥️ CPU</span>
                <span class="metric-val">${cpuPct.toFixed(1)}%</span>
              </div>
              ${renderBar(cpuPct)}
            </div>
          </div>
          <div>
            <div class="metric-row">
              <div class="metric-header">
                <span class="metric-label">🧠 RAM</span>
                <span class="metric-val">${ramPct.toFixed(1)}%</span>
              </div>
              ${renderBar(ramPct)}
              <div style="font-size:11px;color:var(--muted)">${ramUsed} / ${ramTotal} GB</div>
            </div>
          </div>
        </div>

        ${tempHtml}
        ${disksHtml}
        ${netHtml}
        ${procsHtml}
        ${appsHtml}
      </div>
      <div class="agent-footer">
        <span>ID: ${agent.agent_id.substring(0,8)}...</span>
        <span>Dernière mise à jour: ${ts}</span>
      </div>
    </div>`;
}

function renderAll() {
  const grid = document.getElementById("agentGrid");
  const keys = Object.keys(agentsData);

  // Stats globales
  const total = keys.length;
  const online = keys.filter(k => agentsData[k].online !== false).length;
  const offline = total - online;
  let alerts = 0;
  keys.forEach(k => { alerts += renderAlerts(agentsData[k]).length; });

  document.getElementById("g-total").textContent = total;
  document.getElementById("g-online").textContent = online;
  document.getElementById("g-offline").textContent = offline;
  document.getElementById("g-alerts").textContent = alerts;

  if (keys.length === 0) {
    grid.innerHTML = `<div class="empty"><h2>🔌 En attente des agents...</h2><p>Installez l'agent sur les machines cibles</p></div>`;
    return;
  }

  // Trier : en ligne d'abord, puis par nom
  keys.sort((a, b) => {
    const ao = agentsData[a].online !== false;
    const bo = agentsData[b].online !== false;
    if (ao !== bo) return ao ? -1 : 1;
    return agentsData[a].agent_name.localeCompare(agentsData[b].agent_name);
  });

  grid.innerHTML = keys.map(k => renderAgent(agentsData[k])).join("");
  restoreOpenPanels();
}

// Rafraichir toutes les 5s pour détecter les machines hors ligne
setInterval(() => {
  fetch("/api/agents").then(r => r.json()).then(data => {
    agentsData = data;
    renderAll();
  });
}, 5000);
</script>
</body>
</html>
"""

# ─── API ROUTES ───────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route("/api/handshake", methods=["POST"])
def handshake():
    data = request.get_json(force=True, silent=True) or {}
    agent_id   = data.get("agent_id", "unknown")
    agent_name = data.get("agent_name", "unknown")
    action     = data.get("action", "HELLO")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] HANDSHAKE {action} — {agent_name} ({agent_id[:8]})")

    if action == "BYE":
        with agents_lock:
            if agent_id in agents:
                agents[agent_id]["online"] = False
        socketio.emit("agent_offline", {"agent_id": agent_id})
    else:
        with agents_lock:
            if agent_id not in agents:
                agents[agent_id] = {
                    "agent_id":   agent_id,
                    "agent_name": agent_name,
                    "online":     True,
                    "last_seen":  datetime.now(timezone.utc).isoformat(),
                    "payload":    {}
                }

    return jsonify({"status": "ok", "action": action})

@app.route("/api/report", methods=["POST"])
def report():
    data = request.get_json(force=True, silent=True) or {}
    agent_id   = data.get("agent_id", "unknown")
    agent_name = data.get("agent_name", "unknown")
    payload    = data.get("payload", {})
    seq        = data.get("sequence", 0)

    now = datetime.now(timezone.utc).isoformat()

    with agents_lock:
        agents[agent_id] = {
            "agent_id":   agent_id,
            "agent_name": agent_name,
            "online":     True,
            "last_seen":  now,
            "sequence":   seq,
            "payload":    payload,
        }

    # Envoyer au dashboard en temps réel
    socketio.emit("agent_update", agents[agent_id])

    cpu = payload.get("cpu", {}).get("usage_percent", "?")
    ram = payload.get("memory", {}).get("ram_percent", "?")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] #{seq:04d} {agent_name} — CPU:{cpu}% RAM:{ram}%")

    return jsonify({"status": "ok", "sequence": seq})

@app.route("/api/agents")
def get_agents():
    with agents_lock:
        # Marquer hors ligne si pas de nouvelles depuis OFFLINE_TIMEOUT
        now = datetime.now(timezone.utc)
        for aid, agent in agents.items():
            try:
                last = datetime.fromisoformat(agent["last_seen"].replace("Z", "+00:00"))
                delta = (now - last).total_seconds()
                if delta > OFFLINE_TIMEOUT:
                    agent["online"] = False
            except Exception:
                pass
        return jsonify(dict(agents))

# ─── THREAD SURVEILLANCE HORS LIGNE ──────────────────────────────────────────
def check_offline():
    while True:
        time.sleep(30)
        now = datetime.now(timezone.utc)
        with agents_lock:
            for aid, agent in agents.items():
                if not agent.get("online"):
                    continue
                try:
                    last = datetime.fromisoformat(agent["last_seen"].replace("Z", "+00:00"))
                    if (now - last).total_seconds() > OFFLINE_TIMEOUT:
                        agent["online"] = False
                        print(f"[!] {agent['agent_name']} hors ligne")
                        socketio.emit("agent_offline", {"agent_id": aid})
                except Exception:
                    pass

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    t = threading.Thread(target=check_offline, daemon=True)
    t.start()

    print("""
╔══════════════════════════════════════════════╗
║         SysMon Server - Démarré             ║
╠══════════════════════════════════════════════╣
║  Dashboard : http://localhost:8888           ║
║  Réseau    : http://0.0.0.0:8888            ║
║  Arrêt     : Ctrl+C                         ║
╚══════════════════════════════════════════════╝
    """)

    socketio.run(app, host="0.0.0.0", port=8888, debug=False, allow_unsafe_werkzeug=True)
