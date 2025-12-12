const dominioActual = window.location.hostname.replace('www.', '');
console.log("🌐 Dominio detectado:", dominioActual);

// ============================================
// AUTENTICACIÓN
// ============================================
let usuarioId = null;

// Cargar usuario_id al iniciar
chrome.storage.local.get(['usuario_id'], (data) => {
    usuarioId = data.usuario_id;
    if (usuarioId) {
        console.log('[AUTH] ✅ Usuario:', usuarioId);
    } else {
        console.log('[AUTH] ⚠️ Sin autenticación - intentando obtener...');
        obtenerUsuarioDesdeServidor();
    }
});

// Si estamos en el dashboard, obtener usuario_id del servidor
function obtenerUsuarioDesdeServidor() {
    const esDashboard = window.location.hostname.includes('tiempo-check-production.up.railway.app') ||
                        window.location.hostname.includes('localhost');
    
    if (!esDashboard) return;
    
    fetch('/api/usuario/me', { credentials: 'include' })
        .then(res => {
            if (!res.ok) throw new Error('No autenticado');
            return res.json();
        })
        .then(data => {
            if (data.usuario_id) {
                chrome.storage.local.set({ 
                    usuario_id: data.usuario_id,
                    sesion_activa: true,
                    timestamp: Date.now()
                }, () => {
                    console.log('✅ [AUTH] Usuario guardado automáticamente:', data.usuario_id);
                    usuarioId = data.usuario_id;
                    
                    // Recargar categorías después de autenticar
                    cargarCategoriasParaClasificacion();
                });
            }
        })
        .catch(err => {
            console.log('[AUTH] No se pudo obtener usuario del servidor');
        });
}

// Escuchar cambios
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.usuario_id) {
        usuarioId = changes.usuario_id.newValue;
        console.log('[AUTH] 🔄 Usuario actualizado:', usuarioId);
        
        if (usuarioId) {
            cargarCategoriasParaClasificacion();
        }
    }
});

// ============================================
// SISTEMA DE ALERTAS DE LÍMITES
// ============================================

verificarAlerta();
iniciarIntervaloVerificacion();

function verificarAlerta() {
  if (!usuarioId) {
    console.log('[ALERTAS] ⚠️ Sin autenticación');
    return;
  }

  chrome.storage.local.get(["recordatorios", "tiempoRecordatorio", "alertasMostradas"], (data) => {
    const recordatorios = data.recordatorios || {};
    const ultimaVez = recordatorios[dominioActual] || 0;
    const ahora = Date.now();
    const tiempoEsperaMs = (data.tiempoRecordatorio || 1) * 60 * 1000;
    const tiempoTranscurrido = ahora - ultimaVez;

    if (tiempoTranscurrido < tiempoEsperaMs) {
      console.log(`⏳ Aún no ha pasado el tiempo de espera. Faltan ${(tiempoEsperaMs - tiempoTranscurrido) / 1000}s`);
      return;
    }

    fetch("https://tiempo-check-production.up.railway.app/api/alerta_dominio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Usuario-ID": String(usuarioId)
      },
      body: JSON.stringify({ dominio: dominioActual })
    })
    .then(res => res.json())
    .then(response => {
      console.log("📨 Respuesta de alerta:", response);

      if (!response.alerta) return;

      if (response.tipo === "exceso") {
        mostrarAlertaPersonalizada(response.mensaje);
      } else if (response.tipo === "proximidad") {
        const alertas = data.alertasMostradas || {};
        const hoy = new Date().toDateString();

        if (alertas[dominioActual] === hoy) {
          console.log("🔁 Alerta de proximidad ya mostrada hoy.");
          return;
        }

        mostrarAlertaProximidad(response.mensaje);
        const nuevasAlertas = { ...alertas, [dominioActual]: hoy };
        chrome.storage.local.set({ alertasMostradas: nuevasAlertas });
      }
    })
    .catch(err => console.error("❌ Error en fetch:", err));
  });
}

// ============================================
// SISTEMA DE CLASIFICACIÓN
// ============================================

let categoriasDisponibles = [];
let notificacionClasificacionMostrada = false;

cargarCategoriasParaClasificacion();

async function cargarCategoriasParaClasificacion() {
  if (!usuarioId) {
    console.log('[CLASIFICACIÓN] ⚠️ Sin autenticación');
    return;
  }

  try {
    const response = await fetch("https://tiempo-check-production.up.railway.app/api/clasificacion/categorias", {
      headers: {
        "X-Usuario-ID": String(usuarioId)
      }
    });
    
    const data = await response.json();
    
    if (data.success && data.categorias) {
      categoriasDisponibles = data.categorias;
      console.log("[CLASIFICACIÓN] Categorías cargadas:", categoriasDisponibles.length);
    }
  } catch (error) {
    console.error("[CLASIFICACIÓN] Error cargando categorías:", error);
  }
}

async function verificarClasificacionPendiente() {
  if (document.getElementById("modalClasificacionSitio")) return;
  if (notificacionClasificacionMostrada) return;
  
  if (!usuarioId) {
    console.log('[CLASIFICACIÓN] ⚠️ Sin autenticación');
    return;
  }
  
  try {
    const response = await fetch("https://tiempo-check-production.up.railway.app/api/clasificacion/verificar-dominio", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "X-Usuario-ID": String(usuarioId)
      },
      body: JSON.stringify({ dominio: dominioActual })
    });
    
    const data = await response.json();
    
    if (data.necesita_clasificacion) {
      notificacionClasificacionMostrada = true;
      console.log("[CLASIFICACIÓN] ✅ Sitio necesita clasificación");
      mostrarModalClasificacionEnSitio(data);
    }
  } catch (error) {
    console.error("[CLASIFICACIÓN] Error verificando:", error);
  }
}

function mostrarModalClasificacionEnSitio(data) {
  if (document.getElementById("modalClasificacionSitio")) return;

  const esManual = data.metodo === 'manual_required';
  const modal = document.createElement("div");
  modal.id = "modalClasificacionSitio";
  modal.style = modalStyle();

  if (esManual) {
    modal.innerHTML = `
      <div style="${modalBoxStyle('#3b82f6')}">
        <h2 style="margin: 0 0 15px 0; font-size: 18px;">❓ Categorizar sitio</h2>
        <p style="margin: 0 0 15px 0; font-size: 14px;"><strong>${dominioActual}</strong></p>
        <select id="catSelect" style="width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 6px; font-size: 14px;">
          <option value="">-- Selecciona categoría --</option>
          ${categoriasDisponibles.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('')}
        </select>
        <div style="display: flex; gap: 10px;">
          <button id="btnGuardarCat" style="${btnStyle('#10b981')}" disabled>Guardar</button>
          <button id="btnCerrarCat" style="${btnStyle('#6b7280')}">Después</button>
        </div>
      </div>
    `;
  } else {
    const confianza = Math.round((data.confianza || 0) * 100);
    modal.innerHTML = `
      <div style="${modalBoxStyle('#8b5cf6')}">
        <h2 style="margin: 0 0 10px 0; font-size: 18px;">🤖 Clasificación automática</h2>
        <p style="margin: 0 0 5px 0; font-size: 13px;"><strong>${dominioActual}</strong></p>
        <p style="margin: 0 0 15px 0; font-size: 14px;">Categoría: <strong>${data.categoria_sugerida}</strong> (${confianza}%)</p>
        <div style="display: flex; gap: 10px;">
          <button id="btnConfirmar" style="${btnStyle('#10b981')}">✓ Correcto</button>
          <button id="btnCerrarCat" style="${btnStyle('#6b7280')}">Después</button>
        </div>
      </div>
    `;
  }

  document.body.appendChild(modal);

  document.getElementById("btnCerrarCat")?.addEventListener("click", () => modal.remove());
  
  if (esManual) {
    const select = document.getElementById("catSelect");
    const btnGuardar = document.getElementById("btnGuardarCat");
    
    select.addEventListener("change", () => {
      btnGuardar.disabled = !select.value;
    });
    
    btnGuardar.addEventListener("click", async () => {
      btnGuardar.disabled = true;
      btnGuardar.textContent = "Guardando...";
      
      try {
        await fetch(`https://tiempo-check-production.up.railway.app/api/clasificacion/clasificar_manual/${data.notificacion_id}`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Usuario-ID': String(usuarioId)
          },
          body: JSON.stringify({ categoria_correcta_id: parseInt(select.value) })
        });
        
        console.log("[CLASIFICACIÓN] ✅ Guardado");
        modal.remove();
      } catch (error) {
        console.error("[CLASIFICACIÓN] Error:", error);
        btnGuardar.disabled = false;
        btnGuardar.textContent = "Guardar";
      }
    });
  } else {
    document.getElementById("btnConfirmar")?.addEventListener("click", async () => {
      try {
        await fetch(`https://tiempo-check-production.up.railway.app/api/clasificacion/confirmar/${data.notificacion_id}`, {
          method: 'POST',
          headers: {
            'X-Usuario-ID': String(usuarioId)
          }
        });
        
        console.log("[CLASIFICACIÓN] ✅ Confirmado");
        modal.remove();
      } catch (error) {
        console.error("[CLASIFICACIÓN] Error:", error);
      }
    });
  }
}

function iniciarIntervaloVerificacion() {
  const intervaloMs = 30 * 1000;

  setInterval(() => {
    verificarAlerta();
    verificarClasificacionPendiente();
  }, intervaloMs);

  console.log(`🔄 Intervalo de verificación: cada ${intervaloMs / 1000} segundos`);
}

// ============================================
// MODALES DE ALERTAS
// ============================================

function mostrarAlertaPersonalizada(mensaje) {
  if (document.getElementById("alertaModal")) return;

  const modal = document.createElement("div");
  modal.id = "alertaModal";
  modal.style = modalStyle();

  modal.innerHTML = `
    <div style="${modalBoxStyle()}">
      <h2 style="margin-top: 0; font-weight: bold;">⏳ TiempoCheck</h2>
      <p style="margin-bottom: 20px; font-size: 16px;">❗ ${mensaje}</p>
      <label for="tiempoRecordatorio" style="font-size: 14px; display: block; margin-bottom: 5px; color: #ffffff;">¿En cuánto tiempo quieres que te lo vuelva a recordar?</label>
      <div style="margin-bottom: 20px;">
        <select id="tiempoRecordatorio" style="width: 100%; padding: 8px; border-radius: 6px; font-size: 14px; height: 38px;">
          <option value="5">5 minutos</option>
          <option value="10" selected>10 minutos</option>
          <option value="15">15 minutos</option>
          <option value="30">30 minutos</option>
          <option value="60">60 minutos</option>
        </select>
      </div>
      <div style="display: flex; justify-content: center; gap: 10px;">
        <button id="cerrarPestana" style="${btnStyle('#ff4d4d')}">Aceptar y cerrar</button>
        <button id="guardarRecordatorio" style="${btnStyle('#444')}">Guardar y recordar</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  document.getElementById("cerrarPestana").addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "cerrar_pestana" });
    modal.remove();
  });

  document.getElementById("guardarRecordatorio").addEventListener("click", () => {
    const seleccionado = document.getElementById("tiempoRecordatorio").value;
    chrome.storage.local.get("recordatorios", (data) => {
      const recordatorios = data.recordatorios || {};
      const ahora = Date.now();
      const nuevoRegistro = { ...recordatorios, [dominioActual]: ahora };

      chrome.storage.local.set({
        tiempoRecordatorio: parseInt(seleccionado),
        recordatorios: nuevoRegistro
      }, () => {
        console.log(`📥 Guardado: ${seleccionado} min para ${dominioActual}`);
        modal.remove();
      });
    });
  });
}

function mostrarAlertaProximidad(mensaje) {
  if (document.getElementById("alertaProximidad")) return;

  const modal = document.createElement("div");
  modal.id = "alertaProximidad";
  modal.style = modalStyle();

  modal.innerHTML = `
    <div style="${modalBoxStyle('#fff')}">
      <h2 style="color: #e67e22;">⚠️ Advertencia</h2>
      <p style="margin: 20px 0; color: #333;">${mensaje}</p>
      <button id="cerrarProximidad" style="${btnStyle('#e67e22')}">Aceptar</button>
    </div>
  `;

  document.body.appendChild(modal);
  document.getElementById("cerrarProximidad").addEventListener("click", () => {
    modal.remove();
  });
}

// ============================================
// ESTILOS
// ============================================

function modalStyle() {
  return `
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: auto !important;
    height: auto !important;
    background-color: rgba(0, 0, 0, 0.75) !important;
    z-index: 999999 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    font-family: 'Segoe UI', sans-serif !important;
    padding: 0 !important;
    margin: 0 !important;
  `;
}

function modalBoxStyle(bg = "rgba(61, 90, 128, 0.7)") {
  return `
    background-color: ${bg};
    color: #ffffff;
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    max-width: 400px;
    box-shadow: 0 0 15px rgba(0,0,0,0.5);
  `;
}

function btnStyle(color) {
  return `
    background-color: ${color};
    border: none;
    padding: 10px 20px;
    margin: 5px;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
  `;
}