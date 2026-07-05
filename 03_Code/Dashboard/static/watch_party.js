(function () {
  'use strict';

  const roomId = window.WATCH_ROOM_ID || '';
  const initialVideoId = window.WATCH_VIDEO_ID || '';
  const serverSync = window.WATCH_SERVER_SYNC === true;
  const pollMs = Number(window.WATCH_POLL_MS) || 2000;
  const rtConfig = window.WATCH_REALTIME_CONFIG || {};
  let ws = null;
  let player = null;
  let suppressEvents = false;
  let reconnectTimer = null;
  let pollTimer = null;
  let lastServerRevision = 0;
  let cmdInFlight = false;
  let realtimeConnected = false;
  let realtimeChannel = null;

  const $ = (id) => document.getElementById(id);

  function setStatus(text) {
    const el = $('watch-status');
    if (el) el.textContent = text;
  }

  function lanBase() {
    return (window.WATCH_LAN_BASE || location.origin).replace(/\/$/, '');
  }

  function joinUrl() {
    return `${lanBase()}/watch/${roomId}`;
  }

  function localUrl() {
    return `${location.origin}/watch/${roomId}`;
  }

  function updateJoinDisplay() {
    const joinEl = $('join-url');
    if (joinEl) joinEl.textContent = joinUrl();
    const localEl = $('local-url');
    if (localEl) localEl.textContent = localUrl();
    const roomInput = $('room-id');
    if (roomInput) roomInput.value = roomId;
    renderRoomQr();
    if (serverSync && rtConfig.enabled) {
      setStatus('Supabase Realtime wird verbunden…');
    } else if (serverSync) {
      setStatus('Server-Sync aktiv (Supabase Poll)');
    }
  }

  function rowToWatchState(row) {
    const now = Date.now() / 1000;
    let position = Number(row.position) || 0;
    const updatedAt = Number(row.updated_at) || now;
    const playing = !!row.playing;
    if (playing) position += Math.max(0, now - updatedAt);
    return {
      type: 'watch_state',
      room_id: row.room_id,
      video_id: row.video_id || '',
      position: Math.round(position * 100) / 100,
      playing,
      server_time: now,
      updated_at: updatedAt,
      sync_authority: 'server',
      sync_source: 'realtime',
    };
  }

  async function initRealtime() {
    if (!serverSync || !rtConfig.enabled || !rtConfig.url || !rtConfig.anon_key) return false;
    const lib = window.supabase;
    if (!lib || typeof lib.createClient !== 'function') return false;
    try {
      const sb = lib.createClient(rtConfig.url, rtConfig.anon_key);
      realtimeChannel = sb.channel(`watch-room-${roomId}`);
      realtimeChannel.on(
        'postgres_changes',
        {
          event: '*',
          schema: rtConfig.schema || 'public',
          table: rtConfig.table || 'watch_rooms',
          filter: `room_id=eq.${roomId}`,
        },
        (payload) => {
          if (!payload.new) return;
          syncFromServer(rowToWatchState(payload.new));
        }
      );
      realtimeChannel.subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          realtimeConnected = true;
          setStatus('Supabase Realtime verbunden — Live-Sync aktiv');
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') {
          realtimeConnected = false;
          setStatus('Realtime offline — Poll-Fallback aktiv');
        }
      });
      return true;
    } catch (err) {
      setStatus(`Realtime Fehler: ${err.message}`);
      return false;
    }
  }

  async function renderRoomQr() {
    const canvas = $('room-qr');
    const fallback = $('room-qr-fallback');
    const url = joinUrl();
    if (!canvas && !fallback) return;
    try {
      if (window.QRCode && canvas) {
        await QRCode.toCanvas(canvas, url, {
          width: 220,
          margin: 1,
          color: { dark: '#0a0a0f', light: '#ffffff' },
        });
        if (fallback) fallback.hidden = true;
        return;
      }
    } catch (_) { /* fallback below */ }
    if (fallback) {
      fallback.src = `/api/watch/room/${roomId}/qr?size=220`;
      fallback.hidden = false;
      if (canvas) canvas.style.display = 'none';
    }
  }

  async function sendCmd(cmd, extra) {
    const body = { cmd, ...extra };
    if (serverSync) {
      if (cmdInFlight) return;
      cmdInFlight = true;
      try {
        const r = await fetch(`/api/watch/room/${roomId}/cmd`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await r.json();
        if (data.ok && data.state) {
          lastServerRevision = data.state.updated_at || lastServerRevision;
          syncFromServer(data.state);
        }
      } catch (err) {
        setStatus(`Server-Cmd Fehler: ${err.message}`);
      } finally {
        cmdInFlight = false;
      }
      return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ action: 'watch_cmd', cmd, ...extra }));
  }

  function syncFromServer(st) {
    if (!player || !st) return;
    const rev = st.updated_at || 0;
    if (serverSync && rev > 0 && rev <= lastServerRevision && cmdInFlight) return;
    if (serverSync && rev > lastServerRevision) lastServerRevision = rev;

    suppressEvents = true;
    try {
      if (st.video_id && st.video_id !== getCurrentVideoId()) {
        player.loadVideoById(st.video_id, st.position || 0);
      } else {
        const local = player.getCurrentTime();
        const drift = Math.abs(local - (st.position || 0));
        const threshold = serverSync ? 0.8 : 1.2;
        if (drift > threshold) {
          player.seekTo(st.position || 0, true);
        }
        const state = player.getPlayerState();
        if (st.playing && state !== YT.PlayerState.PLAYING) {
          player.playVideo();
        } else if (!st.playing && state === YT.PlayerState.PLAYING) {
          player.pauseVideo();
        }
      }
    } finally {
      setTimeout(() => { suppressEvents = false; }, serverSync ? 500 : 400);
    }
  }

  function getCurrentVideoId() {
    if (!player || !player.getVideoData) return '';
    const data = player.getVideoData();
    return (data && data.video_id) || '';
  }

  function onPlayerReady() {
    setStatus(serverSync ? 'Player bereit — Server steuert Sync' : 'Verbunden — warte auf Video…');
    if (initialVideoId) {
      player.loadVideoById(initialVideoId, 0);
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'watch_join' }));
    }
    if (serverSync && !realtimeConnected) pollServerState();
  }

  function onPlayerStateChange(event) {
    if (suppressEvents || !player || cmdInFlight) return;
    const pos = player.getCurrentTime();
    if (event.data === YT.PlayerState.PLAYING) {
      sendCmd('play', { position: pos });
    } else if (event.data === YT.PlayerState.PAUSED) {
      sendCmd('pause', { position: pos });
    }
  }

  function loadYouTubeApi() {
    return new Promise((resolve) => {
      if (window.YT && window.YT.Player) {
        resolve();
        return;
      }
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (prev) prev();
        resolve();
      };
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
    });
  }

  function initPlayer() {
    player = new YT.Player('player', {
      height: '100%',
      width: '100%',
      videoId: initialVideoId || undefined,
      playerVars: {
        autoplay: 0,
        rel: 0,
        modestbranding: 1,
      },
      events: {
        onReady: onPlayerReady,
        onStateChange: onPlayerStateChange,
      },
    });

    if (!serverSync) {
      let seekTimer = null;
      setInterval(() => {
        if (suppressEvents || !player || player.getPlayerState() !== YT.PlayerState.PLAYING) return;
        clearTimeout(seekTimer);
        seekTimer = setTimeout(() => {
          sendCmd('seek', { position: player.getCurrentTime(), playing: true });
        }, 800);
      }, 2000);
    }
  }

  async function pollServerState() {
    if (!serverSync || !roomId) return;
    try {
      const r = await fetch(`/api/watch/room/${roomId}/state`);
      const data = await r.json();
      if (data.ok && data.state) {
        const rev = data.state.updated_at || 0;
        if (rev > lastServerRevision || !lastServerRevision) {
          syncFromServer(data.state);
        }
      }
    } catch (_) { /* retry next tick */ }
  }

  function startServerPoll() {
    if (!serverSync) return;
    clearInterval(pollTimer);
    pollTimer = setInterval(() => {
      if (realtimeConnected && pollMs < 15000) return;
      pollServerState();
    }, pollMs);
  }

  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/watch/${roomId}`);
    ws.onopen = () => {
      if (!serverSync) setStatus('Raum verbunden — Play/Pause synchronisiert');
      ws.send(JSON.stringify({ action: 'watch_join' }));
    };
    ws.onclose = () => {
      if (!serverSync) {
        setStatus('Verbindung getrennt — reconnect…');
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWs, 2000);
      }
    };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'watch_state') {
          if (!serverSync || (msg.updated_at || 0) >= lastServerRevision) {
            syncFromServer(msg);
          }
        } else if (msg.type === 'watch_meta') {
          const badge = $('viewer-count');
          if (badge) badge.textContent = `${msg.viewers || 0} Zuschauer`;
        }
      } catch (_) { /* ignore */ }
    };
  }

  function bindUi() {
    $('copy-link-btn')?.addEventListener('click', async () => {
      const url = joinUrl();
      try {
        await navigator.clipboard.writeText(url);
        setStatus('WLAN-Link kopiert — oder QR mit Redmi scannen');
      } catch (_) {
        setStatus(url);
      }
    });

    $('load-video-btn')?.addEventListener('click', () => {
      const url = ($('video-url')?.value || '').trim();
      if (!url) return;
      sendCmd('load', { video_id: url });
      setStatus('Video wird geladen…');
    });
  }

  async function boot() {
    if (!roomId) {
      setStatus('Kein Raum — bitte vom Dashboard erstellen');
      return;
    }
    updateJoinDisplay();
    bindUi();
    await loadYouTubeApi();
    initPlayer();
    connectWs();
    await initRealtime();
    startServerPoll();
  }

  boot();
})();