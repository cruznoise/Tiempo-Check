let intervalId = null;

// === CONTROL DE DÍA NUEVO Y CARGA INICIAL ===
document.addEventListener("DOMContentLoaded", () => {
  const hoy = new Date().toDateString(); // "Tue Jul 15 2025"

  chrome.storage.local.get(['ultimaFecha'], (data) => {
    const ultimaFecha = data.ultimaFecha;

    if (ultimaFecha !== hoy) {
      // Nuevo día → reiniciar, conservar historial si se desea
      chrome.storage.local.get(null, (allData) => {
        const historialDominios = allData.historialDominios || [];

        chrome.storage.local.clear(() => {
          chrome.storage.local.set({
            ultimaFecha: hoy,
            historialDominios: historialDominios  // Opcional, si lo quieres conservar
          }, () => {
            console.log("⏰ Historial reiniciado por nuevo día.");
            location.reload();
          });
        });
      });
    } else {
      iniciarPopup();
      cargarRachas();
    }
  });
});

// === LÓGICA PRINCIPAL DEL POPUP ===
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

      if (intervalId !== null) clearInterval(intervalId);
      intervalId = updateLiveTime(timeDisplay, currentSeconds);
    });
  });
}

// === ACTUALIZADOR EN TIEMPO REAL ===
function updateLiveTime(element, initialSeconds) {
  let seconds = initialSeconds;
  element.textContent = formatTime(seconds);

  return setInterval(() => {
    seconds++;
    element.textContent = formatTime(seconds);
  }, 1000);
}

// === FORMATEO DE TIEMPO ===
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

// === RACHAS: CONSULTA AL BACKEND ===
fetch("http://localhost:5000/admin/api/estado_rachas", { credentials: 'include' })
  .then(async res => {
    const contentType = res.headers.get("content-type");
    if (!res.ok || !contentType.includes("application/json")) {
      throw new Error("Respuesta no válida o sin sesión");
    }
    return res.json();
  })
  .then(data => {
    const rachaMetas = data.metas || { activa: false, dias: 0 };
    document.getElementById("contador-racha-metas").textContent = rachaMetas.dias;
    document.getElementById("icono-racha-metas").src =
      rachaMetas.activa ? "prendida.PNG" : "apagada.PNG";

    const rachaLimites = data.limites || { activa: false, dias: 0 };
    document.getElementById("contador-racha-limites").textContent = rachaLimites.dias;
    document.getElementById("icono-racha-limites").src =
      rachaLimites.activa ? "prendida.PNG" : "apagada.PNG";
  })
  .catch(err => console.error("❌ Error al cargar rachas:", err));
