/* Mainframe Website client — hub, Dauer-VR, IDE, worktree */
(function (global) {
  const MainframeSite = {};

  async function jget(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(url + " " + r.status);
    return r.json();
  }

  function el(id) {
    return document.getElementById(id);
  }

  function fmtBytes(n) {
    if (n == null) return "—";
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    return (n / (1024 * 1024)).toFixed(1) + " MB";
  }

  function fmtTime(ts) {
    if (!ts) return "—";
    try {
      return new Date(ts * 1000).toLocaleString();
    } catch (_) {
      return String(ts);
    }
  }

  // ---- Hub ----
  MainframeSite.bootHub = async function () {
    const pre = el("site-status");
    const list = el("worktree-list");
    try {
      const st = await jget("/api/mainframe/site/status");
      pre.textContent = JSON.stringify(st, null, 2);
      const wts = st.worktrees || [];
      const rel = st.related || [];
      let html = "<ul>";
      wts.forEach((w) => {
        const p = w.path || w.raw || JSON.stringify(w);
        const b = w.branch || w.head || "";
        html += `<li><code>${escapeHtml(p)}</code> <span class="muted">${escapeHtml(b)}</span></li>`;
      });
      rel.forEach((r) => {
        html += `<li><a href="${escapeAttr(r.href)}">${escapeHtml(r.name)}</a> <span class="muted">${escapeHtml(r.path)}</span></li>`;
      });
      html += "</ul>";
      list.innerHTML = html;
    } catch (e) {
      pre.textContent = "error: " + e.message;
      list.textContent = "—";
    }
  };

  // ---- Dauer-VR ----
  MainframeSite.bootDauerVR = async function () {
    const statusEl = el("vr-status-text");
    const select = el("vr-scene-select");
    const clock = el("vr-clock");
    const layerEl = el("vr-layer");
    let scenes = [];
    let idx = 0;
    let rotateTimer = null;

    function setStatus(msg) {
      if (statusEl) statusEl.textContent = msg;
    }

    function tickClock() {
      if (clock) clock.textContent = new Date().toLocaleTimeString();
    }
    setInterval(tickClock, 1000);
    tickClock();

    async function loadAssets() {
      const data = await jget("/api/vr/assets");
      scenes = (data.scenes || []).map((s) => s.file || s.url);
      if (select) {
        select.innerHTML = "";
        scenes.forEach((name, i) => {
          const o = document.createElement("option");
          o.value = name;
          o.textContent = name;
          if (i === idx) o.selected = true;
          select.appendChild(o);
        });
      }
      if (!scenes.length) {
        setStatus("No VR assets in 03_VR_Assets");
        return;
      }
      await applyScene(scenes[idx] || scenes[0]);
    }

    async function applyScene(name) {
      const url = "/vr/assets/" + encodeURIComponent(name);
      const img = document.querySelector("#pano");
      const sky = document.querySelector("#sky");
      if (img) {
        img.setAttribute("src", url);
        // force A-Frame refresh
        if (sky) {
          sky.setAttribute("src", "");
          setTimeout(() => sky.setAttribute("src", "#pano"), 50);
        }
      }
      setStatus("Dauer-VR · " + name);
      const panel = document.querySelector("#hud-panel");
      if (panel) {
        panel.setAttribute(
          "text",
          "value: FUSION HERO OS\\n" + name + "; align: center; color: #40e0d0; width: 1.6; wrapCount: 28"
        );
      }
    }

    async function refreshHud() {
      try {
        const st = await jget("/api/vr/status");
        const layer = st.layer || {};
        if (layerEl) {
          layerEl.textContent =
            "layer: " +
            (layer.status || layer.mode || layer.error || "ok") +
            " · assets " +
            ((st.assets || []).length);
        }
      } catch (e) {
        if (layerEl) layerEl.textContent = "layer: " + e.message;
      }
      try {
        const site = await jget("/api/mainframe/site/status");
        if (site.ok && statusEl && !statusEl.textContent.includes("Dauer-VR")) {
          /* keep scene name */
        }
      } catch (_) {}
    }

    if (select) {
      select.addEventListener("change", () => {
        idx = scenes.indexOf(select.value);
        if (idx < 0) idx = 0;
        applyScene(select.value);
      });
    }
    if (el("vr-refresh")) {
      el("vr-refresh").onclick = () => {
        loadAssets().then(refreshHud);
      };
    }
    if (el("vr-fs")) {
      el("vr-fs").onclick = () => {
        const sc = document.getElementById("dauer-vr-scene");
        if (sc && sc.requestFullscreen) sc.requestFullscreen();
        else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
      };
    }

    // auto-rotate scenes every 90s (Dauer mode)
    function startRotate() {
      if (rotateTimer) clearInterval(rotateTimer);
      rotateTimer = setInterval(() => {
        if (scenes.length < 2) return;
        idx = (idx + 1) % scenes.length;
        if (select) select.selectedIndex = idx;
        applyScene(scenes[idx]);
      }, 90000);
    }

    await loadAssets();
    await refreshHud();
    startRotate();
    setInterval(refreshHud, 15000);
  };

  // ---- IDE ----
  let idePath = "";

  MainframeSite.bootIDE = async function (initialPath) {
    idePath = "";
    await refreshIdeStatus();
    await loadIdeDir("");
    if (initialPath) {
      if (initialPath.includes(".") && !initialPath.endsWith("/")) {
        const parent = initialPath.split("/").slice(0, -1).join("/");
        await loadIdeDir(parent);
        await openIdeFile(initialPath);
      } else {
        await loadIdeDir(initialPath);
      }
    }
    if (el("ide-refresh")) el("ide-refresh").onclick = () => loadIdeDir(idePath);
    setInterval(refreshIdeStatus, 20000);
  };

  async function refreshIdeStatus() {
    try {
      const st = await jget("/api/mainframe/ide/status");
      if (el("ide-status-pre")) el("ide-status-pre").textContent = JSON.stringify(st.endpoints, null, 2);
      if (el("ide-kernel-pre")) el("ide-kernel-pre").textContent = JSON.stringify(st.kernel_ide, null, 2);
    } catch (e) {
      if (el("ide-status-pre")) el("ide-status-pre").textContent = String(e);
    }
  }

  async function loadIdeDir(path) {
    idePath = path || "";
    const data = await jget("/api/mainframe/worktree/list?path=" + encodeURIComponent(idePath));
    const tree = el("ide-tree");
    const crumbs = el("ide-crumbs");
    if (crumbs) {
      crumbs.innerHTML = breadcrumbHtml(idePath, (p) => {
        loadIdeDir(p);
      });
      // re-bind after innerHTML — use event delegation
      crumbs.onclick = (ev) => {
        const a = ev.target.closest("a[data-path]");
        if (!a) return;
        ev.preventDefault();
        loadIdeDir(a.getAttribute("data-path") || "");
      };
    }
    if (!tree) return;
    let html = "";
    if (idePath) {
      const parent = idePath.split("/").slice(0, -1).join("/");
      html += `<a class="row dir" href="#" data-nav="${escapeAttr(parent)}">‥ ..</a>`;
    }
    (data.entries || []).forEach((e) => {
      const cls = e.type === "dir" ? "dir" : "file";
      html += `<a class="row ${cls}" href="#" data-type="${e.type}" data-path="${escapeAttr(e.path)}">${escapeHtml(e.name)}</a>`;
    });
    tree.innerHTML = html || "<span class='muted'>empty</span>";
    tree.onclick = (ev) => {
      const a = ev.target.closest("a[data-path], a[data-nav]");
      if (!a) return;
      ev.preventDefault();
      if (a.hasAttribute("data-nav")) {
        loadIdeDir(a.getAttribute("data-nav") || "");
        return;
      }
      const p = a.getAttribute("data-path");
      const t = a.getAttribute("data-type");
      if (t === "dir") loadIdeDir(p);
      else openIdeFile(p);
    };
  }

  async function openIdeFile(path) {
    if (el("ide-path")) el("ide-path").textContent = path;
    if (el("ide-open-view")) el("ide-open-view").href = "/mainframe/worktree/view?path=" + encodeURIComponent(path);
    if (el("ide-open-raw")) el("ide-open-raw").href = "/api/mainframe/worktree/raw?path=" + encodeURIComponent(path);
    try {
      const data = await jget("/api/mainframe/worktree/content?path=" + encodeURIComponent(path));
      el("ide-editor").textContent = data.text || "";
      if (data.truncated) {
        el("ide-editor").textContent += "\n\n/* … truncated … */";
      }
    } catch (e) {
      el("ide-editor").textContent = "error: " + e.message;
    }
  }

  // ---- Worktree ----
  MainframeSite.bootWorktree = async function (initialPath) {
    let current = initialPath || "";
    const filter = el("wt-filter");
    async function load(path) {
      current = path || "";
      const data = await jget("/api/mainframe/worktree/list?path=" + encodeURIComponent(current));
      const crumbs = el("wt-crumbs");
      if (crumbs) {
        crumbs.innerHTML = breadcrumbHtml(current);
        crumbs.onclick = (ev) => {
          const a = ev.target.closest("a[data-path]");
          if (!a) return;
          ev.preventDefault();
          load(a.getAttribute("data-path") || "");
        };
      }
      renderTable(data.entries || [], filter ? filter.value : "");
    }
    function renderTable(entries, q) {
      const qq = (q || "").toLowerCase();
      const filtered = qq
        ? entries.filter((e) => e.name.toLowerCase().includes(qq))
        : entries;
      let html =
        '<div class="wt-row head"><span>NAME</span><span>TYPE</span><span class="hide-sm">SIZE</span><span class="hide-sm">LINKS</span></div>';
      if (current) {
        const parent = current.split("/").slice(0, -1).join("/");
        html += `<div class="wt-row"><a href="#" data-nav="${escapeAttr(parent)}">‥ ..</a><span>dir</span><span class="hide-sm">—</span><span class="hide-sm">—</span></div>`;
      }
      filtered.forEach((e) => {
        const nameCls = e.type === "dir" ? "name-dir" : "";
        const href =
          e.type === "dir"
            ? "#"
            : "/mainframe/worktree/view?path=" + encodeURIComponent(e.path);
        const name =
          e.type === "dir"
            ? `<a class="${nameCls}" href="#" data-nav="${escapeAttr(e.path)}">${escapeHtml(e.name)}/</a>`
            : `<a class="${nameCls}" href="${href}">${escapeHtml(e.name)}</a>`;
        const links =
          e.type === "dir"
            ? `<a href="/mainframe/ide?path=${encodeURIComponent(e.path)}">ide</a>`
            : `<a href="/mainframe/worktree/view?path=${encodeURIComponent(e.path)}">view</a> ·
               <a href="/mainframe/ide?path=${encodeURIComponent(e.path)}">ide</a> ·
               <a href="/api/mainframe/worktree/raw?path=${encodeURIComponent(e.path)}">raw</a>`;
        html += `<div class="wt-row">${name}<span>${e.type}</span><span class="hide-sm">${fmtBytes(e.size)}</span><span class="hide-sm">${links}</span></div>`;
      });
      const table = el("wt-table");
      table.innerHTML = html;
      table.onclick = (ev) => {
        const a = ev.target.closest("a[data-nav]");
        if (!a) return;
        ev.preventDefault();
        load(a.getAttribute("data-nav") || "");
      };
    }
    if (filter) {
      filter.addEventListener("input", async () => {
        const data = await jget("/api/mainframe/worktree/list?path=" + encodeURIComponent(current));
        renderTable(data.entries || [], filter.value);
      });
    }
    try {
      const git = await jget("/api/mainframe/worktree/git");
      const box = el("wt-git");
      if (box) {
        let h = "<ul>";
        (git.worktrees || []).forEach((w) => {
          h += `<li><code>${escapeHtml(w.path || "")}</code> ${escapeHtml(w.branch || w.head || "")}</li>`;
        });
        (git.related || []).forEach((r) => {
          h += `<li><strong>${escapeHtml(r.name)}</strong> — <code>${escapeHtml(r.path)}</code></li>`;
        });
        h += "</ul>";
        box.innerHTML = h;
      }
    } catch (e) {
      if (el("wt-git")) el("wt-git").textContent = String(e);
    }
    await load(current);
  };

  function breadcrumbHtml(path) {
    const parts = (path || "").split("/").filter(Boolean);
    let acc = "";
    let html = `<a href="#" data-path="">root</a>`;
    parts.forEach((p) => {
      acc = acc ? acc + "/" + p : p;
      html += ` / <a href="#" data-path="${escapeAttr(acc)}">${escapeHtml(p)}</a>`;
    });
    return html;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  global.MainframeSite = MainframeSite;
})(window);
