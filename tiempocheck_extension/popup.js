let intervalId = null;

// ===  CONTROL DE DÍA NUEVO ===
document.addEventListener("DOMContentLoaded", () => {
  const hoy = new Date().toDateString();  // Ejemplo: "Wed Jul 03 2025"

  chrome.storage.local.get(['ultimaFecha'], (data) => {
    const ultimaFecha = data.ultimaFecha;

    if (ultimaFecha !== hoy) {
      // Nuevo día → limpiar tiempos, pero conservar historial si se desea
      chrome.storage.local.get(null, (allData) => {
        const historialDominios = allData.historialDominios || [];

        chrome.storage.local.clear(() => {
          chrome.storage.local.set({
            ultimaFecha: hoy,
          }, () => {
            console.log("⏰ Historial reiniciado por nuevo día.");
            location.reload();  // Refresca para reflejar el cambio
          });
        });
      });
    } else {
      iniciarPopup(); // Mismo día → carga normal
    }
  });
});

// ===  LÓGICA PRINCIPAL DEL POPUP ===
function iniciarPopup() {
  const siteDisplay = document.getElementById("current-site");
  const timeDisplay = document.getElementById("time-spent");
  const listContainer = document.getElementById("site-list");

  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (!tab || !tab.url || !tab.url.startsWith("http")) {
      siteDisplay.textContent = "---";
      timeDisplay.textContent = "0 s";
      return;
    }

    const url = new URL(tab.url);
    const domain = url.hostname;
    siteDisplay.textContent = domain;

    // ===  Cargar historial de dominios ===
    chrome.storage.local.get(null, (result) => {
      const historial = result.historialDominios || [];
      let currentSeconds = result[domain] || 0;

      listContainer.innerHTML = "";
      for (const dom of historial) {
        const seconds = result[dom] || 0;
        const item = document.createElement("li");
        item.textContent = `${dom}: ${formatTime(seconds)}`;
        listContainer.appendChild(item);
      }

      //  Actualizar tiempo actual en tiempo real
      if (intervalId !== null) clearInterval(intervalId);
      intervalId = updateLiveTime(timeDisplay, currentSeconds);
    });
  });
}

// ===  CONTADOR EN TIEMPO REAL ===
function updateLiveTime(element, initialSeconds) {
  let seconds = initialSeconds;
  element.textContent = formatTime(seconds);

  return setInterval(() => {
    seconds++;
    element.textContent = formatTime(seconds);
  }, 1000);
}

// ===  FORMATO LEGIBLE DEL TIEMPO ===
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;

  if (seconds < 60) return `${secs} s`;
  else if (mins < 60) return `${mins}m ${secs}s`;
  else {
    const hrs = Math.floor(mins / 60);
    const minsRest = mins % 60;
    return `${hrs}h ${minsRest}m ${secs}s`;
  }
}
