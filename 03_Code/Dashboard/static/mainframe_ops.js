/* Mainframe Ops — live cost + repo mirror dashboard */
(function () {
  const costChart = echarts.init(document.getElementById('cost-chart'));
  const breakdownChart = echarts.init(document.getElementById('breakdown-chart'));
  const repoChart = echarts.init(document.getElementById('repo-chart'));

  const fmtEur = (n) => (n == null || isNaN(n) ? '—' : `${Number(n).toFixed(2)} €`);

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
      const [costRes, repoRes] = await Promise.all([
        fetch('/api/mainframe/cost/status'),
        fetch('/api/mainframe/repo/status'),
      ]);
      const cost = await costRes.json();
      const repo = await repoRes.json();
      const snap = cost.snapshot || {};
      document.getElementById('m-month').textContent = fmtEur(snap.total_eur_month_est);
      document.getElementById('m-hour').textContent = fmtEur(snap.total_eur_hour_burn);
      const gke = snap.breakdown?.gke || {};
      document.getElementById('m-pods').textContent = `${gke.pods_running ?? 0} / ${gke.pods_pending ?? 0}`;
      renderCostHistory(cost.history || []);
      renderBreakdown(snap);
      renderRepoSunburst(repo.sunburst || []);
      renderCorrections(repo);
      const alerts = (snap.alerts || []).join(' · ');
      document.getElementById('alerts').textContent = alerts;
    } catch (e) {
      console.warn('mainframe_ops refresh', e);
    }
  }

  refresh();
  setInterval(refresh, 15000);
  window.addEventListener('resize', () => {
    costChart.resize();
    breakdownChart.resize();
    repoChart.resize();
  });
})();