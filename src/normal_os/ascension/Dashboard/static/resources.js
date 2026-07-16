// resources.js — Vanilla JS fuer /resources (Layered Resource Guardian REST-API)
// Kein neues Frontend-Framework, konsistent mit dashboard.js / ascension.js.
(function () {
  const $ = (id) => document.getElementById(id);

  async function getJSON(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

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
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    refreshAll();
    bindControls();
    setInterval(refreshAll, 15000);
  });
})();
