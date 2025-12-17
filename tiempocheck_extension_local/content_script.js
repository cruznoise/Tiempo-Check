const dominioActual = window.location.hostname.replace('www.', '');
console.log("🌐 Dominio detectado:", dominioActual);

// ============================================
// SISTEMA DE ALERTAS DE LÍMITES (ORIGINAL)
// ============================================

// Inicia verificación directa + intervalos
verificarAlerta();
iniciarIntervaloVerificacion();

// Función principal de verificación de límites
function verificarAlerta() {
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

    fetch("https://localhost:5000/api/alerta_dominio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
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

        // Guardar marca de alerta de proximidad
        const nuevasAlertas = { ...alertas, [dominioActual]: hoy };
        chrome.storage.local.set({ alertasMostradas: nuevasAlertas });
      }
    })
    .catch(err => console.error("❌ Error en fetch:", err));
  });
}

function iniciarIntervaloVerificacion() {
  const intervaloMs = 30 * 1000; // Verifica cada 30 segundos

  setInterval(() => {
    verificarAlerta(); // Internamente ya evalúa si mostrar o no
    verificarClasificacionPendiente(); // ← NUEVO: Verificar clasificación
  }, intervaloMs);

  console.log(`🔄 Intervalo de verificación: cada ${intervaloMs / 1000} segundos`);
}

// ============================================
// NUEVO: SISTEMA DE CLASIFICACIÓN EN SITIO
// ============================================

let categoriasDisponibles = [];
let notificacionClasificacionMostrada = false;

// Cargar categorías al inicio
cargarCategoriasParaClasificacion();

async function cargarCategoriasParaClasificacion() {
  try {
    const response = await fetch("https://localhost:5000/api/categorias", {
      credentials: "include"
    });
    const data = await response.json();
    
    if (data.categorias) {
      categoriasDisponibles = data.categorias;
      console.log("[CLASIFICACIÓN] Categorías cargadas:", categoriasDisponibles.length);
    }
  } catch (error) {
    console.error("[CLASIFICACIÓN] Error cargando categorías:", error);
  }
}

// Verificar si este dominio necesita clasificación
async function verificarClasificacionPendiente() {
  // No mostrar si ya hay un modal visible
  if (document.getElementById("modalClasificacionSitio")) {
    return;
  }
  
  // Solo verificar una vez por sesión de página
  if (notificacionClasificacionMostrada) {
    return;
  }
  
  try {
    const response = await fetch("https://localhost:5000/api/clasificacion/verificar-dominio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ dominio: dominioActual })
    });
    
    const data = await response.json();
    
    if (data.necesita_clasificacion) {
      notificacionClasificacionMostrada = true;
      mostrarModalClasificacionEnSitio(data);
    }
  } catch (error) {
    console.error("[CLASIFICACIÓN] Error verificando:", error);
  }
}

// Mostrar modal de clasificación en el sitio
function mostrarModalClasificacionEnSitio(data) {
  if (document.getElementById("modalClasificacionSitio")) return;

  const esManual = data.metodo === 'manual_required';
  const modal = document.createElement("div");
  modal.id = "modalClasificacionSitio";
  modal.style = modalStyle();

  let contenidoHTML = '';
  
  if (esManual) {
    // MODO: Clasificación Manual Requerida
    contenidoHTML = `
      <div style="${modalBoxClasificacionStyle('#3b82f6')}">
        <div style="text-align: center; margin-bottom: 20px;">
          <span style="font-size: 48px;">❓</span>
          <h2 style="margin: 10px 0; font-size: 20px; font-weight: bold;">¿A qué categoría pertenece este sitio?</h2>
        </div>
        
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
          <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.9);">
            <strong>📍 Dominio:</strong> ${dominioActual}
          </p>
          <p style="margin: 10px 0 0 0; font-size: 12px; color: rgba(255,255,255,0.7);">
            Este sitio aún no está categorizado. Ayúdame a clasificarlo para un mejor seguimiento.
          </p>
        </div>

        <label style="display: block; margin-bottom: 8px; font-size: 14px; color: rgba(255,255,255,0.9);">
          Selecciona una categoría:
        </label>
        <select id="categoriaSeleccionada" style="
          width: 100%;
          padding: 12px;
          border-radius: 8px;
          border: 2px solid rgba(255,255,255,0.3);
          background: rgba(255,255,255,0.95);
          font-size: 14px;
          margin-bottom: 20px;
          cursor: pointer;
        ">
          <option value="">-- Selecciona --</option>
          ${categoriasDisponibles.map(cat => 
            `<option value="${cat.id}">${cat.nombre}</option>`
          ).join('')}
        </select>

        <div style="display: flex; gap: 10px; justify-content: center;">
          <button id="btnGuardarClasificacion" style="${btnClasificacionStyle('#10b981')}" disabled>
            ✓ Guardar
          </button>
          <button id="btnCerrarClasificacion" style="${btnClasificacionStyle('#6b7280')}">
            Después
          </button>
        </div>
      </div>
    `;
  } else {
    // MODO: Confirmación de clasificación automática
    const confianza = Math.round(data.confianza * 100);
    let colorConfianza = '#10b981'; // Verde
    if (confianza < 80) colorConfianza = '#f59e0b'; // Amarillo
    if (confianza < 60) colorConfianza = '#ef4444'; // Rojo
    
    contenidoHTML = `
      <div style="${modalBoxClasificacionStyle('#8b5cf6')}">
        <div style="text-align: center; margin-bottom: 20px;">
          <span style="font-size: 48px;">🤖</span>
          <h2 style="margin: 10px 0; font-size: 20px; font-weight: bold;">Clasificación Automática</h2>
        </div>
        
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
          <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.9);">
            <strong>📍 Dominio:</strong> ${dominioActual}
          </p>
          <p style="margin: 10px 0 0 0; font-size: 14px; color: rgba(255,255,255,0.9);">
            <strong>📂 Categoría sugerida:</strong> 
            <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 6px; font-weight: bold;">
              ${data.categoria_sugerida}
            </span>
          </p>
        </div>

        <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 13px;">Confianza:</span>
          <span style="background: ${colorConfianza}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 13px;">
            ${confianza}%
          </span>
        </div>

        <div style="display: flex; gap: 10px; justify-content: center;">
          <button id="btnConfirmarClasificacion" style="${btnClasificacionStyle('#10b981')}">
            ✓ Correcto
          </button>
          <button id="btnCorregirClasificacion" style="${btnClasificacionStyle('#f59e0b')}">
            ✏️ Corregir
          </button>
          <button id="btnCerrarClasificacion" style="${btnClasificacionStyle('#6b7280')}">
            Después
          </button>
        </div>

        <div id="selectorCorreccion" style="display: none; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px;">
          <label style="display: block; margin-bottom: 8px; font-size: 14px;">Categoría correcta:</label>
          <select id="categoriaCorrecta" style="
            width: 100%;
            padding: 10px;
            border-radius: 8px;
            border: 2px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.95);
            font-size: 14px;
            margin-bottom: 10px;
          ">
            ${categoriasDisponibles.map(cat => 
              `<option value="${cat.id}">${cat.nombre}</option>`
            ).join('')}
          </select>
          <button id="btnGuardarCorreccion" style="${btnClasificacionStyle('#10b981')}">
            Guardar corrección
          </button>
        </div>
      </div>
    `;
  }

  modal.innerHTML = contenidoHTML;
  document.body.appendChild(modal);

  // Event listeners según el modo
  if (esManual) {
    configurarEventosManual(data);
  } else {
    configurarEventosAutomatico(data);
  }
}

// Configurar eventos para modo manual
function configurarEventosManual(data) {
  const select = document.getElementById('categoriaSeleccionada');
  const btnGuardar = document.getElementById('btnGuardarClasificacion');
  const btnCerrar = document.getElementById('btnCerrarClasificacion');

  select.addEventListener('change', () => {
    btnGuardar.disabled = !select.value;
  });

  btnGuardar.addEventListener('click', async () => {
    const categoriaId = select.value;
    if (!categoriaId) return;

    btnGuardar.disabled = true;
    btnGuardar.textContent = 'Guardando...';

    try {
      const response = await fetch(`https://localhost:5000/api/clasificacion/clasificar_manual/${data.notificacion_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ categoria_correcta_id: parseInt(categoriaId) })
      });

      const result = await response.json();

      if (result.success) {
        mostrarToastClasificacion('✅ Sitio clasificado correctamente', 'success');
        cerrarModalClasificacion();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('[CLASIFICACIÓN] Error:', error);
      mostrarToastClasificacion('❌ Error al guardar', 'error');
      btnGuardar.disabled = false;
      btnGuardar.textContent = '✓ Guardar';
    }
  });

  btnCerrar.addEventListener('click', cerrarModalClasificacion);
}

// Configurar eventos para modo automático
function configurarEventosAutomatico(data) {
  const btnConfirmar = document.getElementById('btnConfirmarClasificacion');
  const btnCorregir = document.getElementById('btnCorregirClasificacion');
  const btnCerrar = document.getElementById('btnCerrarClasificacion');
  const selectorCorreccion = document.getElementById('selectorCorreccion');

  btnConfirmar.addEventListener('click', async () => {
    btnConfirmar.disabled = true;
    btnConfirmar.textContent = 'Confirmando...';

    try {
      const response = await fetch(`https://localhost:5000/api/clasificacion/confirmar/${data.notificacion_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });

      const result = await response.json();

      if (result.success) {
        mostrarToastClasificacion('✅ Clasificación confirmada', 'success');
        cerrarModalClasificacion();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('[CLASIFICACIÓN] Error:', error);
      mostrarToastClasificacion('❌ Error al confirmar', 'error');
      btnConfirmar.disabled = false;
      btnConfirmar.textContent = '✓ Correcto';
    }
  });

  btnCorregir.addEventListener('click', () => {
    selectorCorreccion.style.display = 'block';
    btnConfirmar.style.display = 'none';
    btnCorregir.style.display = 'none';
  });

  document.getElementById('btnGuardarCorreccion')?.addEventListener('click', async () => {
    const categoriaCorrecta = document.getElementById('categoriaCorrecta').value;
    
    try {
      const response = await fetch(`https://localhost:5000/api/clasificacion/rechazar/${data.notificacion_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ categoria_correcta_id: parseInt(categoriaCorrecta) })
      });

      const result = await response.json();

      if (result.success) {
        mostrarToastClasificacion('✅ Corrección guardada', 'success');
        cerrarModalClasificacion();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('[CLASIFICACIÓN] Error:', error);
      mostrarToastClasificacion('❌ Error al guardar', 'error');
    }
  });

  btnCerrar.addEventListener('click', cerrarModalClasificacion);
}

function cerrarModalClasificacion() {
  const modal = document.getElementById("modalClasificacionSitio");
  if (modal) {
    modal.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => modal.remove(), 300);
  }
}

function mostrarToastClasificacion(mensaje, tipo = 'info') {
  const toast = document.createElement('div');
  toast.className = 'toast-clasificacion-sitio';
  toast.textContent = mensaje;
  
  const colores = {
    'success': '#10b981',
    'error': '#ef4444',
    'info': '#3b82f6'
  };
  
  toast.style.cssText = `
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    background: ${colores[tipo]} !important;
    color: white !important;
    padding: 16px 24px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    z-index: 999998 !important;
    font-family: 'Segoe UI', sans-serif !important;
    font-size: 14px !important;
    animation: slideInDown 0.3s ease !important;
  `;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOutUp 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Estilos para modal de clasificación
function modalBoxClasificacionStyle(color) {
  return `
    background: linear-gradient(135deg, ${color} 0%, ${color}dd 100%);
    color: #ffffff;
    padding: 30px;
    border-radius: 16px;
    text-align: left;
    max-width: 450px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    animation: scaleIn 0.3s ease;
  `;
}

function btnClasificacionStyle(color) {
  return `
    background-color: ${color};
    border: none;
    padding: 12px 24px;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: transform 0.2s, opacity 0.2s;
    flex: 1;
  `;
}

// ============================================
// MODALES DE LÍMITES (ORIGINAL)
// ============================================

// Modal de EXCESO
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
        <select id="tiempoRecordatorio" style="
        width: 100%;
        padding: 8px;
        border-radius: 6px;
        font-size: 14px;
        -webkit-appearance: none;
        height: 38px;
        ">
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

// Modal de PROXIMIDAD
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

// Estilos reutilizables (ORIGINAL)
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
    margin: 10px 5px;
    color: white;
    border-radius: 8px;
    cursor: pointer;
  `;
}

// CSS para animaciones
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
  }
  @keyframes slideInDown {
    from { transform: translateY(-100px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
  @keyframes slideOutUp {
    from { transform: translateY(0); opacity: 1; }
    to { transform: translateY(-100px); opacity: 0; }
  }
  @keyframes scaleIn {
    from { transform: scale(0.9); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
`;
document.head.appendChild(style);