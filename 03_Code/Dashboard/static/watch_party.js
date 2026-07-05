(function () {
  'use strict';

  const roomId = window.WATCH_ROOM_ID || '';
  const initialVideoId = window.WATCH_VIDEO_ID || '';
  let ws = null;
  let player = null;
  let suppressEvents = false;
  let reconnectTimer = null;

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

  function sendCmd(cmd, extra) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ action: 'watch_cmd', cmd, ...extra }));
  }

  function syncFromServer(st) {
    if (!player || !st) return;
    suppressEvents = true;
    try {
      if (st.video_id && st.video_id !== getCurrentVideoId()) {
        player.loadVideoById(st.video_id, st.position || 0);
      } else {
        const local = player.getCurrentTime();
        if (Math.abs(local - (st.position || 0)) > 1.2) {
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
      setTimeout(() => { suppressEvents = false; }, 400);
    }
  }

  function getCurrentVideoId() {
    if (!player || !player.getVideoData) return '';
    const data = player.getVideoData();
    return (data && data.video_id) || '';
  }

  function onPlayerReady() {
    setStatus('Verbunden — warte auf Video…');
    if (initialVideoId) {
      player.loadVideoById(initialVideoId, 0);
    }
    ws.send(JSON.stringify({ action: 'watch_join' }));
  }

  function onPlayerStateChange(event) {
    if (suppressEvents || !player) return;
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

    let seekTimer = null;
    setInterval(() => {
      if (suppressEvents || !player || player.getPlayerState() !== YT.PlayerState.PLAYING) return;
      clearTimeout(seekTimer);
      seekTimer = setTimeout(() => {
        sendCmd('seek', { position: player.getCurrentTime(), playing: true });
      }, 800);
    }, 2000);
  }

  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/watch/${roomId}`);
    ws.onopen = () => setStatus('Raum verbunden — Play/Pause synchronisiert');
    ws.onclose = () => {
      setStatus('Verbindung getrennt — reconnect…');
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWs, 2000);
    };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'watch_state') {
          syncFromServer(msg);
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
  }

  boot();
})();