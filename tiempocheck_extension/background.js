let dominioActual = null;
let tiempoAcumulado = 0;
let inicioSesion = null;
let tiempoPorDominio = {};
let ultimaPeticion = {};

// Inicializar storage al cargar la extensión
chrome.storage.local.get(null, (data) => {
  tiempoPorDominio = data || {};
  actualizarDominioActivo();
});

// Obtener dominio activo desde la pestaña actual
async function actualizarDominioActivo() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url || !tab.url.startsWith("http")) return;

  const url = new URL(tab.url);
  const nuevoDominio = url.hostname.replace("www.", "");

  if (nuevoDominio !== dominioActual) {
    guardarTiempo();
    dominioActual = nuevoDominio;
    tiempoAcumulado = tiempoPorDominio[dominioActual] || 0;
    inicioSesion = Date.now();
  }
}

// Guardar tiempo transcurrido y enviarlo al backend
function guardarTiempo(forzarEnvio = false) {
  if (!dominioActual || !inicioSesion) return;

  const ahora = Date.now();
  const MAX_TIEMPO_DELTA = 600; //ESTA
  const deltaCrudo = Math.floor((ahora - inicioSesion) / 1000);
  const delta = Math.min(deltaCrudo, MAX_TIEMPO_DELTA); //  Y ESTA TAMBIEN 

  if (!Number.isFinite(delta) || delta <= 0) return;

  // Validar que no se envíe con demasiada frecuencia
  if (!forzarEnvio && ultimaPeticion[dominioActual] && ahora - ultimaPeticion[dominioActual] < 10000) {
    console.log(`[⏱] Esperando para volver a enviar ${dominioActual}`);
    return;
  }

  ultimaPeticion[dominioActual] = ahora;

  tiempoAcumulado += delta;
  tiempoPorDominio[dominioActual] = tiempoAcumulado;

  chrome.storage.local.set({ [dominioActual]: tiempoAcumulado });

  chrome.storage.local.get("historialDominios", (result) => {
    let historial = result.historialDominios || [];

    if (!historial.includes(dominioActual)) {
      historial.push(dominioActual);
      chrome.storage.local.set({ historialDominios: historial });
    }
  });

  fetch("http://localhost:5000/admin/guardar", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include",
    body: new URLSearchParams({
      dominio: dominioActual,
      tiempo: delta,
    })
  });

  // AGREGA ESTA LINEA, DE tiempoAcumulado = 0
  tiempoAcumulado = 0;

  inicioSesion = Date.now();

}



// === EVENTOS DEL NAVEGADOR ===

chrome.tabs.onActivated.addListener(() => {
  guardarTiempo();
  actualizarDominioActivo();
});

chrome.windows.onFocusChanged.addListener(() => {
  guardarTiempo();
  actualizarDominioActivo();
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    actualizarDominioActivo();
  }
});

chrome.runtime.onSuspend.addListener(() => {
  guardarTiempo();
});

// Intervalo de respaldo cada 20 segundos
setInterval(() => {
  guardarTiempo(true);
}, 20000);

function mostrarNotificacion(titulo, mensaje) {
  if (Notification.permission === 'granted') {
    new Notification(titulo, {
      body: mensaje,
      icon: 'https://cdn-icons-png.flaticon.com/512/833/833472.png'
    });
  }
}

async function verificarAlertas() {
  try {
    // 1. Obtener todas las categorías con ID (opcional si ya las conoces)
    const resCat = await fetch("http://localhost:5000/admin/api/alerta_dominio");
    const categorias = await resCat.json(); // se espera: [{id: 1, nombre: 'Redes'}, ...]

    for (const cat of categorias) {
      const res = await fetch("http://localhost:5000/admin/api/alerta_dominio", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ categoria_id: cat.id })
      });

      const data = await res.json();

      if (data.alerta && data.mensaje) {
        mostrarNotificacion(` ${cat.nombre}`, data.mensaje);
      }
    }
  } catch (error) {
    console.error(" Error al verificar alertas:", error);
  }
}

// 🛡️ Pedir permiso y lanzar cada x minutos
if (Notification.permission !== 'granted') {
  Notification.requestPermission();
}
chrome.runtime.onInstalled.addListener(verificarAlertas);
setInterval(verificarAlertas, 2 * 60 * 1000);


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request === 'resetStorage') {
    chrome.storage.local.clear(() => {
      console.log('[✔] Storage local reseteado');
      sendResponse({ status: 'ok' });
    });
    return true;
  }

  if (request.type === 'verificar_alerta') {
    console.log("🔎 Verificando dominio:", request.dominio);

    fetch("http://localhost:5000/admin/api/alerta_dominio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dominio: request.dominio })
    })
    .then(res => res.json())
    .then(data => {
      console.log("📥 Alerta recibida del backend:", data);
      console.log("✅ Respuesta recibida:", data);
      sendResponse({ alerta: data.alerta });
    })
    .catch(err => {
      console.error("❌ Error en background:", err);
      sendResponse({ alerta: false });
    });

    return true;
  }

  console.log("📩 Mensaje recibido en background:", request); 
  if (request.type === "cerrar_pestana") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        console.log("🛑 Cerrando pestaña:", tabs[0].id);
        chrome.tabs.remove(tabs[0].id);
      }
    });
    return true;
  }
});


