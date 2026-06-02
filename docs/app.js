// ─────────────────────────────────────────────────────────────────────────────
// neuralVISION Plugin Marketplace — UI estática (solo lectura del catalog.json)
// ─────────────────────────────────────────────────────────────────────────────
(function () {
  const cfg = window.MARKETPLACE_CONFIG || {};
  let allPlugins = [];

  // --- Aplicar branding de config ---
  document.getElementById("site-title").textContent = cfg.siteTitle || "Plugin Marketplace";
  document.title = cfg.siteTitle || "Plugin Marketplace";
  if (cfg.logo) {
    document.getElementById("brand-logo").src = cfg.logo;
    document.querySelector('link[rel="icon"]').href = cfg.logo;
  }
  if (cfg.repoUrl) document.getElementById("repo-link").href = cfg.repoUrl;

  const $grid = document.getElementById("grid");
  const $state = document.getElementById("state");
  const $count = document.getElementById("result-count");
  const $search = document.getElementById("search");

  function setState(msg, isError) {
    $state.textContent = msg || "";
    $state.className = "state" + (isError ? " error" : "");
    $state.style.display = msg ? "block" : "none";
  }

  // semver desc para mostrar la versión más reciente
  function latestVersion(p) {
    const vs = (p.versions || []).map((v) => v.version);
    if (!vs.length) return null;
    return vs.slice().sort((a, b) => cmpSemver(b, a))[0];
  }
  function cmpSemver(a, b) {
    const pa = String(a).split(".").map(Number);
    const pb = String(b).split(".").map(Number);
    for (let i = 0; i < 3; i++) {
      const x = pa[i] || 0, y = pb[i] || 0;
      if (x !== y) return x - y;
    }
    return 0;
  }

  function cardHtml(p) {
    const latest = latestVersion(p);
    const inputs = (p.input_types || []).map((t) => `<span class="chip input">${esc(t)}</span>`).join("");
    const tags = (p.tags || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("");
    return `
      <div class="card" data-code="${esc(p.plugin_code)}">
        <div class="card-head">
          <i class="mdi ${esc(p.icon || "mdi-puzzle")}"></i>
          <div>
            <h3>${esc(p.name || p.plugin_code)}</h3>
            <div class="card-author">${esc(p.author || "")}</div>
          </div>
        </div>
        <div class="card-desc">${esc(p.description || "")}</div>
        <div class="chips">${inputs}${tags}</div>
        <div class="card-foot">
          <span class="version-badge">v${esc(latest || "—")}</span>
          <span class="muted">${(p.versions || []).length} versión(es)</span>
        </div>
      </div>`;
  }

  function render(list) {
    if (!list.length) {
      $grid.innerHTML = "";
      setState("No se encontraron plugins.");
      $count.textContent = "";
      return;
    }
    setState("");
    $grid.innerHTML = list.map(cardHtml).join("");
    $count.textContent = `${list.length} de ${allPlugins.length}`;
    $grid.querySelectorAll(".card").forEach((el) => {
      el.addEventListener("click", () => openDetail(el.dataset.code));
    });
  }

  function applyFilter() {
    const q = $search.value.trim().toLowerCase();
    if (!q) return render(allPlugins);
    const filtered = allPlugins.filter((p) => {
      const hay = [
        p.name, p.plugin_code, p.description, p.author,
        ...(p.tags || []), ...(p.input_types || []),
      ].join(" ").toLowerCase();
      return hay.includes(q);
    });
    render(filtered);
  }

  // --- Detalle ---
  const $overlay = document.getElementById("detail-overlay");
  function openDetail(code) {
    const p = allPlugins.find((x) => x.plugin_code === code);
    if (!p) return;
    document.getElementById("detail-icon").className = "mdi " + (p.icon || "mdi-puzzle");
    document.getElementById("detail-name").textContent = p.name || p.plugin_code;
    document.getElementById("detail-author").textContent = p.author || "";
    document.getElementById("detail-desc").textContent = p.description || "";
    document.getElementById("detail-install").textContent = cfg.installHint || "";

    const chips = [
      ...(p.input_types || []).map((t) => `<span class="chip input">${esc(t)}</span>`),
      ...(p.tags || []).map((t) => `<span class="chip">${esc(t)}</span>`),
    ].join("");
    document.getElementById("detail-chips").innerHTML = chips;

    const versions = (p.versions || []).slice().sort((a, b) => cmpSemver(b.version, a.version));
    document.getElementById("detail-versions").innerHTML = versions.map((v) => `
      <div class="version-row">
        <div class="vtop">
          <span class="vname">v${esc(v.version)}</span>
          <span class="vdate">${esc(v.released_at || "")}</span>
        </div>
        ${v.release_notes ? `<div class="release-notes">${esc(v.release_notes)}</div>` : ""}
        <div class="vmeta">
          min nv: ${esc(v.min_nv_version || "—")} ·
          <a href="${esc(v.download_url || "#")}" target="_blank" rel="noopener">bundle.json</a>
        </div>
        <div class="vmeta">sha256: ${esc((v.sha256 || "").slice(0, 24))}…</div>
      </div>`).join("");

    $overlay.classList.remove("hidden");
  }
  function closeDetail() { $overlay.classList.add("hidden"); }
  document.getElementById("detail-close").addEventListener("click", closeDetail);
  $overlay.addEventListener("click", (e) => { if (e.target === $overlay) closeDetail(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDetail(); });

  $search.addEventListener("input", applyFilter);

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // --- Carga del catálogo ---
  // Intenta la URL configurada; si falla, cae a catalog.json local (preview).
  function loadCatalog(url, fallback) {
    return fetch(url, { cache: "no-cache" }).then((r) => {
      if (!r.ok) {
        if (fallback) return loadCatalog(fallback, null);
        throw new Error("HTTP " + r.status);
      }
      return r.json();
    });
  }

  setState("Cargando catálogo…");
  loadCatalog(cfg.catalogUrl || "../catalog.json", "catalog.json")
    .then((data) => {
      allPlugins = (data.plugins || []).slice().sort((a, b) =>
        (a.name || a.plugin_code).localeCompare(b.name || b.plugin_code));
      const meta = data.updated_at
        ? `${allPlugins.length} plugins · actualizado ${new Date(data.updated_at).toLocaleString()}`
        : `${allPlugins.length} plugins`;
      document.getElementById("catalog-meta").textContent = meta;
      render(allPlugins);
    })
    .catch((err) => {
      setState("No se pudo cargar el catálogo (" + err.message + "). Verificá la ruta en config.js.", true);
    });
})();
