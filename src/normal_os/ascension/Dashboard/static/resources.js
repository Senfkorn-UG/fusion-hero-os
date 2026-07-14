<<<<<<< HEAD
// resources.js — Vanilla JS fuer /resources (Layered Resource Guardian REST-API)
=======
// resources.js — Vanilla JS fuer /resources (local_infrastructure_kernel REST-API)
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
// Kein neues Frontend-Framework, konsistent mit dashboard.js / ascension.js.
(function () {
  const $ = (id) => document.getElementById(id);

<<<<<<< HEAD
=======
  const LEVEL_COLORS = {
    ok: '#00d4aa',
    warn: '#f59e0b',
    alert: '#fb7185',
    critical: '#ef4444',
  };

>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
  async function getJSON(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

<<<<<<< HEAD
  async function refreshStatus() {
    const s = await getJSON('/api/resources/status');
    if (s.status && s.status.includes('nicht verfuegbar')) {
      $('rg-status-banner').textContent =
        `⚠ ${s.status} — erwartet: ${s.expected_module || '?'} (siehe ${s.spec || '?'})`;
      return;
    }
    $('rg-status-banner').textContent =
      `running=${s.running}  tick=${s.tick_count}`;
  }

  async function refreshLayer(layer) {
    const s = await getJSON(`/api/resources/layer/${layer}`);
    $(`layer-${layer}-out`).textContent = JSON.stringify(s, null, 2);
  }

  async function refreshEscalations() {
    const e = await getJSON('/api/resources/escalations?last_n=10');
    $('rg-escalations-out').textContent = JSON.stringify(e.escalations || e, null, 2);
  }

  async function refreshHistory() {
    const h = await getJSON('/api/resources/history?last_n=15');
    $('rg-history-out').textContent = JSON.stringify(h.history || h, null, 2);
  }

  async function refreshAll() {
    await Promise.all([
      refreshStatus(),
      refreshLayer('sofort'),
      refreshLayer('kurzfristig'),
      refreshLayer('mittelfristig'),
      refreshEscalations(),
      refreshHistory(),
    ]);
  }

  function bindControls() {
    $('rg-start-btn').addEventListener('click', async () => {
      await getJSON('/api/resources/start', { method: 'POST' });
      await refreshAll();
    });
    $('rg-stop-btn').addEventListener('click', async () => {
      await getJSON('/api/resources/stop', { method: 'POST' });
      await refreshAll();
    });
    document.querySelectorAll('.rg-trigger-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const layer = btn.dataset.layer;
        await getJSON('/api/resources/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ layer }),
        });
        await refreshAll();
      });
=======
  function isUnavailable(data) {
    return data && data.available === false;
  }

  async function refreshStatus() {
    const s = await getJSON('/api/resources/status');
    if (isUnavailable(s)) {
      $('rg-status-banner').textContent =
        `⚠ ${s.reason || 'nicht verfügbar'} — erwartet: ${s.expected_module || '?'} ` +
        `(Contract: ${s.spec || '?'})`;
      return;
    }
    $('rg-status-banner').textContent =
      `enabled=${s.enabled}  platform=${s.platform}  ` +
      `letzter Zyklus=${s.last_cycle_at ? new Date(s.last_cycle_at * 1000).toLocaleString() : '--'}  ` +
      `letzte Eskalation=${s.last_escalation || '--'}`;
  }

  function renderLevel(level, actions) {
    const el = $('rg-level');
    el.textContent = (level || '--').toUpperCase();
    el.style.color = LEVEL_COLORS[level] || '#e2e8f0';
    $('rg-actions').textContent = 'Aktionen: ' + (actions && actions.length ? actions.join(', ') : '–');
  }

  async function refreshEvaluate() {
    const e = await getJSON('/api/resources/evaluate');
    if (isUnavailable(e)) {
      renderLevel(null, []);
      $('rg-findings-out').textContent = 'nicht verfügbar';
      return;
    }
    const esc = e.escalation || {};
    renderLevel(esc.level, esc.actions);
    $('rg-findings-out').textContent = JSON.stringify(esc.findings || [], null, 2);
  }

  async function refreshProbe() {
    const p = await getJSON('/api/resources/probe');
    if (isUnavailable(p)) {
      $('rg-substrate-out').textContent = 'nicht verfügbar';
      $('rg-services-out').textContent = 'nicht verfügbar';
      return;
    }
    $('rg-substrate-out').textContent = JSON.stringify(p.substrate || {}, null, 2);
    $('rg-services-out').textContent = JSON.stringify(p.services || {}, null, 2);
  }

  async function refreshThresholds() {
    const t = await getJSON('/api/resources/thresholds');
    $('rg-thresholds-out').textContent = isUnavailable(t) ? 'nicht verfügbar' : JSON.stringify(t, null, 2);
  }

  async function refreshAll() {
    await Promise.all([refreshStatus(), refreshEvaluate(), refreshProbe(), refreshThresholds()]);
  }

  function bindControls() {
    $('rg-cycle-btn').addEventListener('click', async () => {
      const apply_actions = $('rg-apply-actions').checked;
      await getJSON('/api/resources/run-cycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeout: 4.0, apply_actions }),
      });
      await refreshAll();
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    refreshAll();
    bindControls();
<<<<<<< HEAD
    setInterval(refreshAll, 15000);
=======
    setInterval(refreshAll, 20000);
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
  });
})();
