// Restaurar valores guardados
chrome.storage.local.get(["minIF", "maxIF", "quartiles"], (data) => {
  if (data.minIF) document.getElementById("minIF").value = data.minIF;
  if (data.maxIF) document.getElementById("maxIF").value = data.maxIF;
  if (data.quartiles) {
    document.querySelectorAll(".quartile-grid input").forEach(cb => {
      cb.checked = data.quartiles.includes(cb.value);
    });
  }
});

// Aplicar filtros
document.getElementById("btnApply").addEventListener("click", () => {
  const minIF = parseFloat(document.getElementById("minIF").value) || null;
  const maxIF = parseFloat(document.getElementById("maxIF").value) || null;
  const quartiles = [...document.querySelectorAll(".quartile-grid input:checked")]
    .map(cb => cb.value);

  chrome.storage.local.set({ minIF, maxIF, quartiles });

  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    chrome.tabs.sendMessage(tab.id, { action: "applyFilters", minIF, maxIF, quartiles });
  });
});

// Limpiar
document.getElementById("btnClear").addEventListener("click", () => {
  document.getElementById("minIF").value = "";
  document.getElementById("maxIF").value = "";
  document.querySelectorAll(".quartile-grid input").forEach(cb => cb.checked = false);
  chrome.storage.local.clear();

  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    chrome.tabs.sendMessage(tab.id, { action: "clearFilters" });
  });
});
