// ascension.js — Vanilla JS fuer /ascension (AscensionCore v9.5/v9.6 REST-API)
// Kein neues Frontend-Framework: fetch() + DOM, konsistent mit dashboard.js.
(function () {
  const $ = (id) => document.getElementById(id);

  async function getJSON(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

  function parseVector(text) {
    return text.split(',').map((s) => parseFloat(s.trim())).filter((n) => !Number.isNaN(n));
  }

  async function refreshStatus() {
    const status = await getJSON('/api/ascension/status');
    $('status-out').textContent = JSON.stringify(status, null, 2);
  }

  async function refreshStage9() {
    const s = await getJSON('/api/ascension/stage9');
    if (s.stage_estimate === undefined) {
      $('stage9-value').textContent = '--/9';
      $('stage9-label').textContent = s.status || 'nicht verfuegbar';
      return;
    }
    $('stage9-value').textContent = `${s.stage_estimate}/9`;
    $('stage9-label').textContent = s.label;
    $('stage9-honest').textContent = s.honest_status;
  }

  async function refreshOscillation() {
    const o = await getJSON('/api/ascension/oscillation');
    $('oscillation-svg').src = '/api/ascension/oscillation.svg?ts=' + Date.now();
    if (o.n_points !== undefined) {
      $('oscillation-stats').textContent =
        `n=${o.n_points}  amplitude=${o.amplitude}  reversals=${o.reversal_count}  within<7=${o.within_threshold}`;
    }
  }

  async function refreshPsycholyse() {
    const p = await getJSON('/api/ascension/psycholyse/entries');
    $('psycholyse-canary').textContent = p.coal_canary || '--';
    const list = $('psycholyse-entries');
    list.innerHTML = '';
    (p.entries || []).slice().reverse().forEach((e) => {
      const li = document.createElement('li');
      li.textContent = `#${e.session_id} [${e.status}] ${e.protocol_type}`;
      list.appendChild(li);
    });
  }

  function bindSisyphosForm() {
    $('sisyphos-step-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const load = parseFloat($('sisyphos-load').value);
      if (Number.isNaN(load)) return;
      await getJSON('/api/ascension/sisyphos/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ load, notes: 'manual dashboard step' }),
      });
      await Promise.all([refreshOscillation(), refreshStage9(), refreshStatus()]);
    });
  }

  function bindPsycholyseForm() {
    $('psycholyse-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const protocol_type = $('psy-protocol').value || 'unbenannt';
      const status = $('psy-status').value;
      await getJSON('/api/ascension/psycholyse/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ protocol_type, status }),
      });
      await refreshPsycholyse();
    });
  }

  function bindQuboButton() {
    $('qubo-solve-btn').addEventListener('click', async () => {
      $('qubo-out').textContent = 'loest...';
      const r = await getJSON('/api/ascension/qubo/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n_checkpoints: 12, steps: 4000 }),
      });
      if (r.checkpoints) {
        const lines = r.checkpoints.map((c) => `  [${c.index}] ${c.phase_label}`);
        $('qubo-out').textContent = `energy=${r.energy}\n` + lines.join('\n');
      } else {
        $('qubo-out').textContent = JSON.stringify(r);
      }
    });
  }

  function bindHarmonizeForm() {
    $('harmonize-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const state_a = parseVector($('harmonize-a').value || '0.2,0.8,0.3');
      const state_b = parseVector($('harmonize-b').value || '0.9,0.2,0.7');
      const r = await getJSON('/api/ascension/harmonize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state_a, state_b, label_a: 'A', label_b: 'B' }),
      });
      $('harmonize-out').textContent = JSON.stringify(r, null, 2);
    });
  }

  function bindGeisterjagdForm() {
    $('geisterjagd-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const latent_state = parseVector($('geist-latent').value || '10,-10');
      const r = await getJSON('/api/ascension/geisterjagd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latent_state,
          A: [[0.5, 0.1], [0.0, 0.4]],
          c: [1.0, -0.5],
        }),
      });
      $('geisterjagd-out').textContent = JSON.stringify(r, null, 2);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    refreshStatus();
    refreshStage9();
    refreshOscillation();
    refreshPsycholyse();
    bindSisyphosForm();
    bindPsycholyseForm();
    bindQuboButton();
    bindHarmonizeForm();
    bindGeisterjagdForm();
  });
})();
