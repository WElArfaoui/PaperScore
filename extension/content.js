// PaperScore - content.js
// Muestra IF y Cuartil JCR junto a cada paper en PubMed y Scopus.
// Si la revista no está en la BD muestra "Sin información".

let journalDB = {};

// ── CARGA BD ──────────────────────────────────────────────────
async function loadJournalData() {
  const url = chrome.runtime.getURL("journal_data.json");
  const res  = await fetch(url);
  const data = await res.json();
  // Índice doble: nombre completo + abreviatura, todo en minúsculas
  data.forEach(j => {
    if (j.name) journalDB[normalize(j.name)] = j;
    if (j.abbr) journalDB[normalize(j.abbr)] = j;
  });
}

function normalize(s) {
  return s.toLowerCase().trim().replace(/\s+/g, " ");
}

function findJournal(rawName) {
  if (!rawName) return null;
  return journalDB[normalize(rawName)] || null;
}

// ── CREAR BADGE ───────────────────────────────────────────────
// journal puede ser null → muestra "Sin información"
function createBadge(journal) {
  const wrap = document.createElement("span");
  wrap.className = "ps-badge";

  if (!journal) {
    wrap.innerHTML = '<span class="ps-unknown">Sin información</span>';
    return wrap;
  }

  // Color IF
  let ifCls = "ps-if-low";
  if (journal.jif >= 10) ifCls = "ps-if-high";
  else if (journal.jif >= 5) ifCls = "ps-if-mid";

  // Color cuartil
  const qColor = { Q1: "#1a7f37", Q2: "#2ea44f", Q3: "#d4a017", Q4: "#cf222e" };
  const qBg = qColor[journal.quartile] || "#6e7681";

  const ifTxt  = journal.jif != null ? "IF " + journal.jif.toFixed(2) : "IF N/A";
  const qTxt   = journal.quartile || "N/A";

  wrap.innerHTML =
    '<span class="ps-if ' + ifCls + '" title="Factor de Impacto JCR">' + ifTxt + '</span>' +
    '<span class="ps-q" style="background:' + qBg + '" title="Cuartil JCR">' + qTxt + '</span>';

  return wrap;
}

// ── PUBMED ────────────────────────────────────────────────────
//  Resultados: cada artículo está en .docsum-content
//              la cita tiene la forma: "J Pathol. 2024 Jan;..."
//              el nombre de revista es el texto antes del primer "."
//
//  Detalle:    el nombre de la revista está en .journal-actions > a
function enrichPubMed() {

  // --- Lista de resultados ---
  document.querySelectorAll(".docsum-content:not([data-ps])").forEach(article => {
    const citeEl = article.querySelector(".docsum-journal-citation");
    if (!citeEl) return;

    // Marcar ya para no reprocesar aunque no haya match
    article.dataset.ps = "1";

    const journalName = citeEl.textContent.split(".")[0].trim();
    const journal = findJournal(journalName);

    // Insertar badge justo después del elemento de cita
    const badge = createBadge(journal);
    citeEl.parentElement.insertBefore(badge, citeEl.nextSibling);
  });

  // --- Página de detalle de un artículo ---
  const journalLink = document.querySelector(".journal-actions a:not([data-ps])");
  if (journalLink) {
    journalLink.dataset.ps = "1";
    const journal = findJournal(journalLink.textContent.trim());
    const badge = createBadge(journal);
    journalLink.parentElement.appendChild(badge);
  }
}

// ── SCOPUS ────────────────────────────────────────────────────
//  Scopus es una SPA Angular; el nombre de la revista aparece en
//  distintos elementos según la vista. Cubrimos los más comunes.
//
//  Resultados de búsqueda:
//    - .resultCard-recordTitle  → título del paper (padre de la fila)
//    - [class*="Source"]        → nombre de la revista (selector amplio)
//
//  Scopus cambia clases con frecuencia; usamos varios selectores
//  en orden de especificidad.
function enrichScopus() {
  // Contenedor de cada resultado (varía por versión de Scopus)
  const RESULT_SELECTORS = [
    "[data-testid='result-item']",
    ".resultCard",
    "tr.searchArea",
    ".search-results-item",
  ].join(", ");

  // Selectores para el nombre de la revista DENTRO de cada resultado
  const SOURCE_SELECTORS = [
    "[data-testid='publication-title']",
    "[class*='publicationName']",
    "[class*='sourceTitle']",
    "[class*='PublicationTitle']",
    "a[class*='source']",
    "a[href*='sourceId']",           // enlace al perfil de la revista
    "[class*='Source'] a",
  ].join(", ");

  document.querySelectorAll(RESULT_SELECTORS).forEach(row => {
    if (row.dataset.ps) return;
    row.dataset.ps = "1";

    const sourceEl = row.querySelector(SOURCE_SELECTORS);
    const journalName = sourceEl ? sourceEl.textContent.trim() : null;
    const journal = findJournal(journalName);

    const badge = createBadge(journal);
    badge.classList.add("ps-inline");   // clase extra para posición

    if (sourceEl) {
      // Insertar el badge justo después del nombre de la revista
      sourceEl.parentElement.insertBefore(badge, sourceEl.nextSibling);
    } else {
      // Fallback: al final de la fila
      row.appendChild(badge);
    }
  });
}

// ── DISPATCH + OBSERVER ───────────────────────────────────────
function enrichPage() {
  const h = location.hostname;
  if (h.includes("pubmed.ncbi.nlm.nih.gov")) enrichPubMed();
  if (h.includes("scopus.com"))               enrichScopus();
}

// Debounce: evita llamadas excesivas durante la carga de la SPA
let debounceTimer;
function scheduleEnrich() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(enrichPage, 400);
}

new MutationObserver(scheduleEnrich).observe(document.body, {
  childList: true, subtree: true
});

// ── INICIO ────────────────────────────────────────────────────
(async () => {
  await loadJournalData();
  enrichPage();
})();
