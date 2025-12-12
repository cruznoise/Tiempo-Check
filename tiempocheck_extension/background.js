// ============================================
// AUTENTICACIÓN
// ============================================
let usuarioId = null;

// Cargar usuario_id al iniciar extensión
chrome.storage.local.get(['usuario_id'], (data) => {
    usuarioId = data.usuario_id;
    if (usuarioId) {
        console.log('[AUTH]  Usuario autenticado:', usuarioId);
    } else {
        console.log('[AUTH]  Sin autenticación - inicia sesión en TiempoCheck');
    }
});

// Escuchar cambios en el storage (cuando el usuario hace login)
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.usuario_id) {
        usuarioId = changes.usuario_id.newValue;
        console.log('[AUTH]  Usuario actualizado:', usuarioId);
    }
});

// ============================================
// TRACKING DE TIEMPO (ORIGINAL)
// ============================================
let dominioActual = null;
let tiempoAcumulado = 0;
let inicioSesion = null;
let tiempoPorDominio = {};
let ultimaPeticion = {};

chrome.storage.local.get(null, (data) => {
  tiempoPorDominio = data || {};
  actualizarDominioActivo(); 
});

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

function guardarTiempo(forzarEnvio = false) {
  if (!dominioActual || !inicioSesion) return;

  const ahora = Date.now();
  const MAX_TIEMPO_DELTA = 600;
  const deltaCrudo = Math.floor((ahora - inicioSesion) / 1000);
  const delta = Math.min(deltaCrudo, MAX_TIEMPO_DELTA);
  if (!Number.isFinite(delta) || delta <= 0) return;

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

  fetch("https://tiempo-check-production.up.railway.app/admin/guardar", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include",
    body: new URLSearchParams({
      dominio: dominioActual,
      tiempo: String(delta),
      fecha_hora: new Date(ahora).toISOString(),
      timezone_offset_min: String(new Date().getTimezoneOffset())
    })
  });

  tiempoAcumulado = 0;
  inicioSesion = Date.now();
}

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

setInterval(() => {
  guardarTiempo(true);
}, 20000);

// ============================================
// NOTIFICACIONES
// ============================================

function mostrarNotificacion(titulo, mensaje) {
  if (Notification.permission === 'granted') {
    new Notification(titulo, {
      body: mensaje,
      icon: 'https://cdn-icons-png.flaticon.com/512/833/833472.png'
    });
  }
}

async function verificarAlertas() {
  //REQUIERE AUTENTICACIÓN
  if (!usuarioId) {
    console.log('[ALERTAS] Sin autenticación, saltando verificación');
    return;
  }

  try {
    const response = await fetch("https://tiempo-check-production.up.railway.app/api/categorias", {
      headers: {
        'Content-Type': 'application/json',
        'X-Usuario-ID': String(usuarioId) 
      }
    });
    
    const categorias = await response.json();

    if (categorias && Array.isArray(categorias)) {
      for (const cat of categorias) {
        const res = await fetch("https://tiempo-check-production.up.railway.app/api/alerta_dominio", {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Usuario-ID': String(usuarioId)  
          },
          body: JSON.stringify({ categoria_id: cat.id })
        });

        const data = await res.json();

        if (data.alerta && data.mensaje) {
          mostrarNotificacion(` ${cat.nombre}`, data.mensaje);
        }
      }
    }
  } catch (error) {
    console.error("[ALERTAS] Error:", error);
  }
}

if (Notification.permission !== 'granted') {
  Notification.requestPermission();
}

chrome.runtime.onInstalled.addListener(verificarAlertas);
setInterval(verificarAlertas, 2 * 60 * 1000);

// ============================================
// MENSAJES INTERNOS
// ============================================

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request === 'resetStorage') {
    chrome.storage.local.clear(() => {
      console.log('[✔] Storage local reseteado');
      sendResponse({ status: 'ok' });
    });
    return true;
  }

  if (request.type === 'verificar_alerta') {
    console.log(" Verificando dominio:", request.dominio);

    //  REQUIERE AUTENTICACIÓN
    if (!usuarioId) {
      console.log('[ALERTA]  Sin autenticación');
      sendResponse({ alerta: false });
      return true;
    }

    fetch("https://tiempo-check-production.up.railway.app/api/alerta_dominio", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "X-Usuario-ID": String(usuarioId)  
      },
      body: JSON.stringify({ dominio: request.dominio })
    })
    .then(res => res.json())
    .then(data => {
      console.log("Alerta recibida del backend:", data);
      sendResponse({ alerta: data.alerta });
    })
    .catch(err => {
      console.error("Error en background:", err);
      sendResponse({ alerta: false });
    });

    return true;
  }

  if (request.type === "cerrar_pestana") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        console.log("Cerrando pestaña:", tabs[0].id);
        chrome.tabs.remove(tabs[0].id);
      }
    });
    return true;
  }
});

// ============================================
// FOCUS MODE
// ============================================

let focusActive = false;
let blockedCategories = [];
let strictModeFocus = false;
let sessionIdFocus = null;
let categoriasMapFocus = {};
let dominiosOmitidos = [];

async function cargarCategoriasMapFocus() {
  try {
    console.log('[FOCUS] Cargando categorías desde BD...');
    
    const response = await fetch('https://tiempo-check-production.up.railway.app/api/categorias/con-dominios', {
      credentials: 'include'
    });
    
    const data = await response.json();
    
    if (data.success && data.mapeo) {
      categoriasMapFocus = data.mapeo;
      console.log('[FOCUS] Categorías cargadas desde BD');
      console.log(`[FOCUS] Total dominios: ${data.total_dominios}`);
      chrome.storage.local.set({ categoriasMapFocus: categoriasMapFocus });
    } else {
      console.error('[FOCUS] Error: respuesta sin mapeo');
      chrome.storage.local.get(['categoriasMapFocus'], (stored) => {
        if (stored.categoriasMapFocus) {
          categoriasMapFocus = stored.categoriasMapFocus;
          console.log('[FOCUS] Usando categorías desde cache');
        }
      });
    }
  } catch (error) {
    console.error('[FOCUS] Error cargando categorías:', error);
    chrome.storage.local.get(['categoriasMapFocus'], (stored) => {
      if (stored.categoriasMapFocus) {
        categoriasMapFocus = stored.categoriasMapFocus;
        console.log('[FOCUS] Usando categorías desde cache');
      }
    });
  }
}

cargarCategoriasMapFocus();
setInterval(cargarCategoriasMapFocus, 5 * 60 * 1000);

async function sincronizarEstadoFocus() {
  try {
    const response = await fetch('https://tiempo-check-production.up.railway.app/api/focus/status', {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.success && data.active) {
      focusActive = true;
      blockedCategories = data.categorias_bloqueadas || [];
      strictModeFocus = data.modo_estricto || false;
      sessionIdFocus = data.session_id || null;
      
      chrome.storage.local.set({
        focusActive: true,
        blockedCategories: blockedCategories,
        strictModeFocus: strictModeFocus,
        sessionIdFocus: sessionIdFocus
      });
      
      console.log('[FOCUS] Sesión activa restaurada');
      actualizarReglasBloqueoDNR();
    } else {
      focusActive = false;
      blockedCategories = [];
      chrome.storage.local.remove(['focusActive', 'blockedCategories', 'strictModeFocus', 'sessionIdFocus']);
      actualizarReglasBloqueoDNR();
    }
  } catch (error) {
    console.error('[FOCUS] Error sincronizando:', error);
  }
}

sincronizarEstadoFocus();
setInterval(sincronizarEstadoFocus, 30000);

chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
  console.log('[FOCUS] Mensaje externo recibido:', request);
  
  if (request.action === 'start') {
    cargarCategoriasMapFocus().then(() => {
      focusActive = true;
      blockedCategories = request.data.categorias || [];
      strictModeFocus = request.data.strict || false;
      sessionIdFocus = request.data.session_id || null;
      
      chrome.storage.local.set({
        focusActive: true,
        blockedCategories: blockedCategories,
        strictModeFocus: strictModeFocus,
        sessionIdFocus: sessionIdFocus
      });
      
      console.log('[FOCUS] Focus Mode ACTIVADO');
      actualizarReglasBloqueoDNR();
      sendResponse({ success: true, message: 'Focus activado' });
    });
    return true;
  } 
  else if (request.action === 'end') {
    focusActive = false;
    blockedCategories = [];
    strictModeFocus = false;
    sessionIdFocus = null;
    
    chrome.storage.local.remove(['focusActive', 'blockedCategories', 'strictModeFocus', 'sessionIdFocus']);
    actualizarReglasBloqueoDNR();
    
    console.log('[FOCUS] Focus Mode DESACTIVADO');
    sendResponse({ success: true, message: 'Focus desactivado' });
  }
  
  return true;
});

async function actualizarReglasBloqueoDNR() {
  if (!focusActive || blockedCategories.length === 0) {
    const existingRules = await chrome.declarativeNetRequest.getDynamicRules();
    const ruleIds = existingRules.map(rule => rule.id);
    
    if (ruleIds.length > 0) {
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: ruleIds
      });
      console.log('[FOCUS DNR] Reglas eliminadas:', ruleIds.length);
    }
    return;
  }

  const dominiosABloquear = Object.keys(categoriasMapFocus)
    .filter(dominio => {
      const categoria = categoriasMapFocus[dominio];
      const estaBloqueado = blockedCategories.includes(categoria);
      const estaOmitido = dominiosOmitidos.includes(dominio);
      return estaBloqueado && !estaOmitido;
    });

  console.log('[FOCUS DNR] Dominios a bloquear:', dominiosABloquear.length);

  const reglas = [];
  let ruleId = 1;

  dominiosABloquear.forEach(dominio => {
    const categoria = categoriasMapFocus[dominio];
    const dominioLimpio = dominio.replace(/^www\./, '');
    
    reglas.push({
      id: ruleId++,
      priority: 1,
      action: {
        type: "redirect",
        redirect: {
          url: chrome.runtime.getURL('blocked.html') + 
            `?domain=${encodeURIComponent(dominioLimpio)}&category=${encodeURIComponent(categoria)}&strict=${strictModeFocus}`
        }
      },
      condition: {
        urlFilter: `||${dominioLimpio}`,
        resourceTypes: ["main_frame"]
      }
    });
  });

  const reglasLimitadas = reglas.slice(0, 5000);

  try {
    const existingRules = await chrome.declarativeNetRequest.getDynamicRules();
    const ruleIds = existingRules.map(rule => rule.id);
    
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: ruleIds,
      addRules: reglasLimitadas
    });

    console.log('[FOCUS DNR] Reglas creadas:', reglasLimitadas.length);
  } catch (error) {
    console.error('[FOCUS DNR] Error creando reglas:', error);
  }
}

async function registrarIntentoBloqueadoFocus(domain, categoria) {
  try {
    await fetch('https://tiempo-check-production.up.railway.app/api/focus/block', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        url: domain,
        categoria: categoria
      })
    });
    
    console.log('[FOCUS] ✓ Bloqueo registrado en BD');
  } catch (error) {
    console.error('[FOCUS] Error registrando:', error);
  }
}

async function omitirDominio(domain) {
  console.log('[FOCUS] Omitiendo dominio:', domain);
  
  if (!dominiosOmitidos.includes(domain)) {
    dominiosOmitidos.push(domain);
    chrome.storage.local.set({ dominiosOmitidos: dominiosOmitidos });
    await actualizarReglasBloqueoDNR();
    console.log('[FOCUS] ✓ Dominio omitido');
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'omitir_dominio') {
    omitirDominio(request.domain).then(() => {
      sendResponse({ success: true });
    });
    return true;
  }
});

console.log('[FOCUS] Sistema de bloqueo inicializado');