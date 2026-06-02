// ─────────────────────────────────────────────────────────────────────────────
// Configuración del sitio del marketplace.
// Para levantar el marketplace en OTRO repo: copiá toda esta carpeta a /docs del
// nuevo repo y ajustá solo estas variables. El resto del sitio no se toca.
// ─────────────────────────────────────────────────────────────────────────────
window.MARKETPLACE_CONFIG = {
  // Título que se muestra en el header.
  siteTitle: "neuralVISION Plugin Marketplace",

  // Logo (ruta relativa dentro de la carpeta del sitio).
  logo: "assets/logo.svg",

  // De dónde se lee el catálogo. Con GitHub Pages sirviendo desde /docs, el
  // catalog.json de la raíz del repo NO se publica, así que se lee por URL raw
  // (raw.githubusercontent permite CORS). Apuntá a la rama 'main' del repo.
  // Para preview local, si esto falla, el sitio cae a ./catalog.json.
  catalogUrl: "https://raw.githubusercontent.com/OneclickEB/nv-plugins-marketplace/main/catalog.json",

  // Base para resolver download_url / links al repo (solo para mostrar enlaces).
  repoUrl: "https://github.com/OneclickEB/nv-plugins-marketplace",

  // Texto/instrucción de instalación que se muestra en el detalle del plugin.
  installHint:
    "Instalá este plugin desde la UI de neuralVISION → Plugins → Marketplace, " +
    "o descargá el bundle.json de la versión deseada.",
};
