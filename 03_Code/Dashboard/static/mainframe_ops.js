/* Mainframe Ops — live cost + energy + repo mirror dashboard */
(function () {
  const costChart = echarts.init(document.getElementById('cost-chart'));
  const energyChart = echarts.init(document.getElementById('energy-chart'));
  const breakdownChart = echarts.init(document.getElementById('breakdown-chart'));
  const repoChart = echarts.init(document.getElementById('repo-chart'));

  const fmtEur = (n) => (n == null || isNaN(n) ? '—' : `${Number(n).toFixed(2)} €`);
  const fmtNum = (n, d = 2) => (n == null || isNaN(n) ? '—' : Number(n).toFixed(d));

  function renderCostHistory(history) {
    const times = (history || []).map((h) => new Date(h.ts * 1000).toLocaleTimeString('de-DE'));
    const month = (history || []).map((h) => h.total_eur_month_est);
    const hour = (history || []).map((h) => h.total_eur_hour_burn);
    costChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: ['Monat est.', 'EUR/h'], textStyle: { color: '#94a3b8' } },
      grid: { left: 48, right: 24, top: 40, bottom: 32 },
      xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 10 } },
      yAxis: [
        { type: 'value', name: 'EUR/M', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e293b' } } },
        { type: 'value', name: 'EUR/h', axisLabel: { color: '#64748b' }, splitLine: { show: false } },
      ],
      series: [
        { name: 'Monat est.', type: 'line', smooth: true, data: month, areaStyle: { opacity: 0.15 }, itemStyle: { color: '#2dd4bf' } },
        { name: 'EUR/h', type: 'line', yAxisIndex: 1, smooth: true, data: hour, itemStyle: { color: '#fbbf24' } },
      ],
    });
  }

  function renderEnergyHistory(history) {
    const times = (history || []).map((h) => new Date(h.ts * 1000).toLocaleTimeString('de-DE'));
    const kwh = (history || []).map((h) => h.energy_kwh_equivalent);
    const feu = (history || []).map((h) => h.feu_per_hour);
    const eurH = (history || []).map((h) => h.eur_hour_real);
    energyChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: ['kWh-Äq/h', 'FEU/h', 'EUR/h real'], textStyle: { color: '#94a3b8' } },
      grid: { left: 48, right: 24, top: 40, bottom: 32 },
      xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 10 } },
      yAxis: [
        { type: 'value', name: 'kWh', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e293b' } } },
        { type: 'value', name: 'FEU/EUR', axisLabel: { color: '#64748b' }, splitLine: { show: false } },
      ],
      series: [
        { name: 'kWh-Äq/h', type: 'line', smooth: true, data: kwh, areaStyle: { opacity: 0.12 }, itemStyle: { color: '#34d399' } },
        { name: 'FEU/h', type: 'line', yAxisIndex: 1, smooth: true, data: feu, itemStyle: { color: '#22d3ee' } },
        { name: 'EUR/h real', type: 'line', yAxisIndex: 1, smooth: true, data: eurH, itemStyle: { color: '#fbbf24' } },
      ],
    });
  }

  function renderPricingTable(pricing, bp) {
    const el = document.getElementById('pricing-table');
    const tiers = pricing?.tiers || {};
    const rows = Object.entries(tiers).map(([id, t]) => `
      <tr class="border-b border-slate-800/80">
        <td class="py-2 pr-3 text-teal-300/90">${t.label || id}</td>
        <td class="py-2 pr-3 text-right text-lime-300">${fmtEur(t.api_price_eur_per_1k_tokens)}</td>
        <td class="py-2 pr-3 text-right text-slate-400">${fmtEur(t.real_cost_eur_per_1k_tokens)}</td>
        <td class="py-2 pr-3 text-right ${t.competitive ? 'text-emerald-400' : 'text-amber-400'}">${((t.margin_pct || 0) * 100).toFixed(0)}%</td>
        <td class="py-2 text-right text-slate-500">${t.competitive ? '✓' : 'cap'}</td>
      </tr>`).join('');
    const mode = pricing?.margin_pct_applied_mode === 'competitive_150' ? '150% kompetitiv' : 'gemischt (Marktdecke)';
    el.innerHTML = `
      <table class="w-full">
        <thead><tr class="text-slate-500 border-b border-slate-700">
          <th class="text-left py-1">Tier</th>
          <th class="text-right py-1">API/1k</th>
          <th class="text-right py-1">Real/1k</th>
          <th class="text-right py-1">Marge</th>
          <th class="text-right py-1">OK</th>
        </tr></thead>
        <tbody>${rows || '<tr><td colspan="5" class="text-slate-500 py-4">Keine Preisdaten</td></tr>'}</tbody>
      </table>
      <p class="text-slate-600 mt-2">Basis EUR/h: ${fmtEur(pricing?.eur_hour_basis)} · Ziel ${((pricing?.margin_pct || 0) * 100).toFixed(0)}% · ${mode}</p>`;
    const ver = document.getElementById('bp-version');
    if (ver) ver.textContent = bp?.businessplan_version || pricing?.company || '—';
  }

  function renderBreakdown(snap) {
    if (!snap?.breakdown) return;
    const gke = snap.breakdown.gke || {};
    const fixed = snap.breakdown.fixed || {};
    breakdownChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['42%', '70%'],
        label: { color: '#cbd5e1', fontSize: 11 },
        data: [
          { name: 'GCE VM', value: fixed.gce_fusion_mesh_exit_eur_month || 0 },
          { name: 'GCS', value: fixed.gcs_storage_eur_month || 0 },
          { name: 'GKE Burn/h×720', value: (gke.eur_hour || 0) * 720 },
          { name: 'L4 GPU/h', value: (gke.gpu_l4 || 0) * 0.55 },
        ],
        itemStyle: {
          borderRadius: 6,
          borderColor: '#0f172a',
          borderWidth: 2,
        },
        color: ['#2dd4bf', '#38bdf8', '#a78bfa', '#fbbf24'],
      }],
    });
  }

  function renderRepoSunburst(data) {
    repoChart.setOption({
      backgroundColor: 'transparent',
      series: [{
        type: 'sunburst',
        data: data || [],
        radius: [0, '95%'],
        label: { rotate: 'radial', fontSize: 10, color: '#e2e8f0' },
        itemStyle: { borderWidth: 1, borderColor: '#0f172a' },
        levels: [{}, { r0: 0, r: '35%' }, { r0: '35%', r: '70%' }, { r0: '70%', r: '95%' }],
      }],
    });
  }

  function renderCorrections(repo) {
    const feed = document.getElementById('correction-feed');
    const items = repo.corrections_last || [];
    if (!items.length) {
      feed.innerHTML = '<li class="text-slate-500">Keine Korrekturen in letztem Tick — Spiegelung OK</li>';
    } else {
      feed.innerHTML = items.map((c) =>
        `<li class="${c.ok ? 'text-teal-400' : 'text-rose-400'}">[${c.action}] ${c.target}<br><span class="text-slate-500">${c.detail || ''}</span></li>`
      ).join('');
    }
    const drift = repo.drift || {};
    const el = document.getElementById('m-drift');
    el.textContent = drift.tree_drift ? 'DRIFT' : 'OK';
    el.className = `ops-metric text-3xl mt-1 ${drift.tree_drift ? 'text-rose-400' : 'text-teal-400'}`;
  }

  async function refresh() {
    try {
      const [costRes, energyRes, repoRes] = await Promise.all([
        fetch('/api/mainframe/cost/status'),
        fetch('/api/mainframe/energy/status'),
        fetch('/api/mainframe/repo/status'),
      ]);
      const cost = await costRes.json();
      const energy = await energyRes.json();
      const repo = await repoRes.json();
      const snap = cost.snapshot || {};
      const esnap = energy.snapshot || {};
      const pricing = energy.subcontractor_pricing || esnap.subcontractor_pricing || {};

      document.getElementById('m-month').textContent = fmtEur(snap.total_eur_month_est);
      document.getElementById('m-hour').textContent = fmtEur(snap.total_eur_hour_burn);
      document.getElementById('m-kwh').textContent = fmtNum(esnap.energy_kwh_equivalent, 3);
      document.getElementById('m-feu').textContent = fmtNum(esnap.feu_per_hour, 1);
      document.getElementById('m-token-price').textContent = fmtEur(
        pricing.headline_price_eur_per_1k_tokens ?? pricing.tiers?.inference_standard?.api_price_eur_per_1k_tokens
      );

      renderCostHistory(cost.history || []);
      renderEnergyHistory(energy.history || []);
      renderBreakdown(snap);
      renderPricingTable(pricing, energy.businessplan);
      renderRepoSunburst(repo.sunburst || []);
      renderCorrections(repo);

      const gke = snap.breakdown?.gke || {};
      const costAlerts = (snap.alerts || []).join(' · ');
      const energyAlerts = (esnap.alerts || []).join(' · ');
      const podInfo = `GKE ${gke.pods_running ?? 0}/${gke.pods_pending ?? 0} pods`;
      document.getElementById('alerts').textContent = [podInfo, costAlerts, energyAlerts].filter(Boolean).join(' · ');
    } catch (e) {
      console.warn('mainframe_ops refresh', e);
    }
  }

  refresh();
  setInterval(refresh, 15000);
  window.addEventListener('resize', () => {
    costChart.resize();
    energyChart.resize();
    breakdownChart.resize();
    repoChart.resize();
  });
})();