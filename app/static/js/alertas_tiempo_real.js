// Cargar usuario_id
let usuarioId = null;
chrome.storage.local.get(['usuario_id'], (data) => {
    usuarioId = data.usuario_id;
    if (usuarioId) {
        console.log('[ALERTAS] ✅ Usuario autenticado:', usuarioId);
        // Iniciar polling
        iniciarPolling();
    } else {
        console.log('[ALERTAS] ⚠️ Usuario no autenticado');
    }
});

// Sistema de Alertas en Tiempo Real - Global
let alertasPollingInterval = null;

// Inicializar sistema de alertas
function initAlertasSistema() {
  const usuarioId = window.USUARIO_ID;
  
  if (!usuarioId) {
    console.log('[ALERTAS] Usuario no autenticado, no iniciar polling');
    return;
  }
  
  console.log('[ALERTAS] Sistema inicializado para usuario', usuarioId);
  
  // Primera verificación inmediata
  setTimeout(() => {
    checkAlertasTiempoReal();
    checkAnomaliasPendientes();
  }, 2000);
  
  // Polling cada 5 minutos
  if (!alertasPollingInterval) {
    alertasPollingInterval = setInterval(() => {
      checkAlertasTiempoReal();
      checkAnomaliasPendientes();
    }, 5 * 60 * 1000);
  }
}

// Verificar alertas en tiempo real
async function checkAlertasTiempoReal() {
  try {
    const usuarioId = window.USUARIO_ID;
    if (!usuarioId) return;
    
    const response = await fetch(`/admin/api/coach/sugerencias?usuario_id=${usuarioId}`) ;
    const data = await response.json();
    
    if (data.ok && data.items && data.items.length > 0) {
      // Filtrar solo anomalías en tiempo real
      const alertas = data.items.filter(item => item.tipo === 'anomalia_tiempo_real');
      
      if (alertas.length > 0) {
        mostrarAlertaTiempoReal(alertas[0]);
      }
    }
  } catch (error) {
    console.error('[ALERTAS] Error:', error);
  }
}

// Verificar anomalías históricas pendientes
async function checkAnomaliasPendientes() {
  try {
    const response = await fetch('/api/anomalias/pendientes');
    const data = await response.json();
    
    if (data.pendientes && data.pendientes.length > 0) {
      // Solo mostrar si no hay modal visible
      if (!document.getElementById('modalAnomalia').classList.contains('hidden')) {
        return;
      }
      
      mostrarModalAnomalia(data.pendientes[0]);
    }
  } catch (error) {
    console.error('[ALERTAS] Error anomalías:', error);
  }
}

// Mostrar alerta en tiempo real
function mostrarAlertaTiempoReal(alerta) {
  // Verificar si ya hay una alerta visible
  if (document.querySelector('.alerta-tiempo-real')) {
    return;
  }
  
  const payload = typeof alerta.action_payload === 'string' 
    ? JSON.parse(alerta.action_payload) 
    : alerta.action_payload;
  
  // Crear toast
  const toast = document.createElement('div');
  toast.className = 'alerta-tiempo-real';
  toast.setAttribute('data-alerta-id', alerta.id);
  toast.innerHTML = `
    <div class="alerta-header">
      <span class="alerta-icono">🔍</span>
      <h4>Coach Virtual</h4>
      <button onclick="cerrarAlerta(${alerta.id})" class="btn-cerrar-mini">×</button>
    </div>
    <div class="alerta-body">
      <h5>${alerta.titulo}</h5>
      <p>${alerta.cuerpo}</p>
      <button onclick="explicarAhora(${alerta.id}, ${JSON.stringify(payload).replace(/"/g, '&quot;')})" class="btn-explicar">
        ¿Qué está pasando?
      </button>
      <button onclick="ignorarAlerta(${alerta.id})" class="btn-ignorar">
        Está bien, continuar
      </button>
    </div>
  `;
  
  // Agregar al container
  const container = document.getElementById('alertas-container') || document.body;
  container.appendChild(toast);
  
  // Auto-cerrar después de 30 segundos
  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 300);
    }
  }, 30000);
}

// Explicar anomalía ahora
async function explicarAhora(sugerenciaId, payload) {
  const usuarioId = window.USUARIO_ID;
  
  // Marcar como vista
  await fetch('/coach/sugerencias/act', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      id: sugerenciaId, 
      usuario_id: usuarioId,
      action: 'accept' 
    })
  });
  
  // Abrir modal de explicación
  mostrarModalExplicacionTiempoReal(payload);
  
  // Cerrar toast
  document.querySelector('.alerta-tiempo-real')?.remove();
}

// Ignorar alerta
async function ignorarAlerta(sugerenciaId) {
  const usuarioId = window.USUARIO_ID;
  
  // Marcar como dismissed
  await fetch('/coach/sugerencias/act', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      id: sugerenciaId, 
      usuario_id: usuarioId,
      action: 'dismiss' 
    })
  });
  
  document.querySelector('.alerta-tiempo-real')?.remove();
  
  mostrarToast('Alerta ignorada', 'info');
}

// Cerrar alerta sin cambiar status
function cerrarAlerta(sugerenciaId) {
  document.querySelector('.alerta-tiempo-real')?.remove();
}

// Mostrar modal de explicación para tiempo real
function mostrarModalExplicacionTiempoReal(payload) {
  const fecha = new Date();
  const fechaBonita = fecha.toLocaleDateString('es-MX', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
  
  const desviacion = payload.desviacion || 0;
  
  document.getElementById('anomalia-fecha').textContent = `HOY (${fechaBonita})`;
  document.getElementById('anomalia-diferencia').textContent = 
    desviacion > 0 
      ? `${Math.abs(desviacion).toFixed(0)}% más` 
      : `${Math.abs(desviacion).toFixed(0)}% menos`;
  document.getElementById('anomalia-real').textContent = 
    `${payload.uso_actual.toFixed(0)} minutos (${(payload.uso_actual / 60).toFixed(1)}h)`;
  document.getElementById('anomalia-esperado').textContent = 
    `${payload.uso_esperado.toFixed(0)} minutos (${(payload.uso_esperado / 60).toFixed(1)}h)`;
  document.getElementById('anomalia-dia-semana').textContent = 'hoy';
  
  // Mostrar modal
  document.getElementById('modalAnomalia').classList.remove('hidden');
}

// Toast de notificación
function mostrarToast(mensaje, tipo = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${tipo}`;
  toast.textContent = mensaje;
  
  const colores = {
    'success': '#10b981',
    'error': '#ef4444',
    'info': '#3b82f6',
    'warning': '#f59e0b'
  };
  
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: ${colores[tipo] || colores.info};
    color: white;
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 10001;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAlertasSistema);
} else {
  initAlertasSistema();
}

// Limpiar interval al salir
window.addEventListener('beforeunload', () => {
  if (alertasPollingInterval) {
    clearInterval(alertasPollingInterval);
  }
});