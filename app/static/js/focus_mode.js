// ========================================
// FOCUS MODE - JavaScript COMPLETO
// Versión: 1.0 - Con todas las funciones necesarias
// ========================================

// ==================== VARIABLES GLOBALES ====================
let focusInterval = null;
let focusDurationMinutes = 0;
let focusCategoriasBloquedas = [];
let focusModoEstricto = false;
let focusStartTime = null;
let focusPausado = false;

// ==================== EMOJIS DE CATEGORÍAS ====================
function obtenerEmojiCategoria(categoria) {
  const emojis = {
    'Redes Sociales': '📱',
    'Ocio': '🎮',
    'Comercio': '🛒',
    'Entretenimiento': '🎬',
    'Sin categoría': '❓',
    'Trabajo': '💼',
    'Estudio': '📚',
    'Productividad': '⚡',
    'Herramientas': '🔧',
    'Informacion': 'ℹ️',
    'Salud y bientestar': '💚'
  };
  return emojis[categoria] || '📁';
}

// ==================== INICIO RÁPIDO (Dashboard) ====================
function iniciarFocusRapido(minutosDefault, categoriasDefault) {
  console.log('[FOCUS] iniciarFocusRapido llamado:', { minutosDefault, categoriasDefault });
  
  if (focusInterval) {
    mostrarToast('error', 'Ya tienes una sesión activa');
    return;
  }

  // Determinar tipo de configuración
  const tipo = getTipoConfiguracion(minutosDefault);
  
  // Intentar cargar configuración guardada
  const savedConfig = cargarConfiguracion(tipo);
  
  let minutos = minutosDefault;
  let categorias = categoriasDefault;
  let strictMode = false;
  let allowBreak = false;
  let notifyEnd = true;
  
  // Si hay configuración guardada, usarla
  if (savedConfig) {
    console.log(`[FOCUS] Usando configuración guardada para "${tipo}":`, savedConfig);
    minutos = savedConfig.duration || minutosDefault;
    categorias = savedConfig.categories || categoriasDefault;
    strictMode = savedConfig.strict_mode || false;
    allowBreak = savedConfig.allow_break || false;
    notifyEnd = savedConfig.notify_end !== undefined ? savedConfig.notify_end : true;
  } else {
    console.log(`[FOCUS] No hay configuración guardada para "${tipo}", usando valores por defecto`);
  }

  // Construir mensaje de confirmación
  const configInfo = savedConfig 
    ? `\n📋 Usando última configuración guardada:\n• ${categorias.length} categorías\n• Modo estricto: ${strictMode ? 'Sí' : 'No'}`
    : `\n📋 Configuración por defecto:\n• ${categorias.length} categorías`;
  
  // Confirmar
  if (!confirm(`¿Iniciar sesión Focus de ${minutos} minutos?${configInfo}`)) {
    return;
  }

  // Enviar al backend
  fetch('/api/focus/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      duration_minutes: minutos,
      blocked_categories: categorias,
      allow_break: allowBreak,
      strict_mode: strictMode,
      notify_end: notifyEnd
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log('[FOCUS] Respuesta de /api/focus/start:', data);
    
    if (data.success) {
      focusDurationMinutes = minutos;
      focusCategoriasBloquedas = categorias;
      focusModoEstricto = strictMode;
      focusStartTime = new Date();
      
      // Notificar extensión
      notificarExtensionFocus('start', {
        categorias: categorias,
        strict: strictMode,
        session_id: data.session_id
      });
      
      // Cambiar UI del widget
      mostrarEstadoActivoWidget();
      iniciarContador();
      
      // Guardar en localStorage
      localStorage.setItem('focus_active', JSON.stringify({
        start: focusStartTime.getTime(),
        duration: minutos,
        categories: categorias,
        strict: strictMode,
        session_id: data.session_id
      }));

      const emoji = savedConfig ? '🎯' : '🚀';
      mostrarToast('success', `${emoji} Modo Focus iniciado por ${minutos} minutos`);
    } else {
      mostrarToast('error', 'Error: ' + data.message);
    }
  })
  .catch(error => {
    console.error('[FOCUS] Error:', error);
    mostrarToast('error', 'Error de conexión');
  });
}

// ==================== MODAL DE CONFIGURACIÓN (Dashboard) ====================
function abrirConfigFocus() {
  console.log('[FOCUS] Abriendo modal de configuración...');
  
  const modal = document.getElementById('modal-focus-config');
  if (!modal) {
    console.error('[FOCUS] Modal no encontrado');
    mostrarToast('error', 'Error: Modal no encontrado');
    return;
  }
  
  modal.classList.remove('hidden');
  modal.style.display = 'flex';
  
  // Cargar categorías
  cargarCategoriasEnModal();
  
  // Listener para duración personalizada
  const durationSelect = document.getElementById('focus-duration-modal');
  if (durationSelect) {
    durationSelect.addEventListener('change', function(e) {
      const customInput = document.getElementById('focus-duration-custom-modal');
      if (customInput) {
        if (e.target.value === 'custom') {
          customInput.classList.remove('hidden');
          customInput.style.display = 'block';
          customInput.focus();
        } else {
          customInput.classList.add('hidden');
          customInput.style.display = 'none';
        }
      }
    });
  }
  
  console.log('[FOCUS] Modal abierto');
}

function cerrarConfigFocus() {
  const modal = document.getElementById('modal-focus-config');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}

// ==================== CARGAR CATEGORÍAS EN MODAL ====================
async function cargarCategoriasEnModal() {
  console.log('[FOCUS] Cargando categorías en modal...');
  
  try {
    const response = await fetch('/api/categorias');
    const data = await response.json();
    
    console.log('[FOCUS] Respuesta de /api/categorias:', data);
    
    if (data.categorias || data.success) {
      const container = document.getElementById('focus-categories-grid');
      if (!container) {
        console.error('[FOCUS] Container focus-categories-grid no encontrado');
        return;
      }
      
      container.innerHTML = '';
      
      // Categorías sugeridas para bloquear
      const sugeridas = ['Redes Sociales', 'Ocio', 'Comercio', 'Sin categoría'];
      const categorias = data.categorias || [];
      
      console.log('[FOCUS] Procesando', categorias.length, 'categorías');
      
      categorias.forEach(cat => {
        const checked = sugeridas.includes(cat.nombre) ? 'checked' : '';
        const checkedClass = checked ? 'checked' : '';
        const emoji = obtenerEmojiCategoria(cat.nombre);
        
        const label = document.createElement('label');
        label.className = `category-checkbox-item ${checkedClass}`;
        label.dataset.category = cat.nombre;
        
        label.innerHTML = `
          <input type="checkbox" value="${cat.nombre}" ${checked} onchange="toggleCategoryCheck(this)">
          <span>${emoji} ${cat.nombre}</span>
        `;
        
        container.appendChild(label);
      });
      
      console.log('[FOCUS] Categorías cargadas exitosamente');
    } else {
      console.error('[FOCUS] Respuesta sin categorías');
    }
  } catch (error) {
    console.error('[FOCUS] Error cargando categorías:', error);
  }
}

// ==================== TOGGLE CATEGORÍAS ====================
function toggleCategoryCheck(checkbox) {
  const label = checkbox.closest('.category-checkbox-item');
  if (checkbox.checked) {
    label.classList.add('checked');
  } else {
    label.classList.remove('checked');
  }
}

function toggleTodasCategorias() {
  const checkboxes = document.querySelectorAll('#focus-categories-grid input[type="checkbox"]');
  const todasChecked = Array.from(checkboxes).every(cb => cb.checked);
  
  checkboxes.forEach(cb => {
    cb.checked = !todasChecked;
    toggleCategoryCheck(cb);
  });
}

// ==================== INICIAR DESDE MODAL ====================
function iniciarModoFocusDesdeModal() {
  console.log('[FOCUS] Iniciando desde modal...');
  
  // Obtener duración
  const durationSelect = document.getElementById('focus-duration-modal');
  let minutes = parseInt(durationSelect.value);
  
  if (durationSelect.value === 'custom') {
    const customInput = document.getElementById('focus-duration-custom-modal');
    minutes = parseInt(customInput.value);
    if (!minutes || minutes < 1 || minutes > 480) {
      mostrarToast('error', 'Duración inválida (1-480 minutos)');
      return;
    }
  }
  
  // Obtener categorías
  const checkboxes = document.querySelectorAll('#focus-categories-grid input[type="checkbox"]:checked');
  const categorias = Array.from(checkboxes).map(cb => cb.value);
  
  if (categorias.length === 0) {
    mostrarToast('error', 'Selecciona al menos una categoría');
    return;
  }
  
  // Obtener opciones
  const strictModeCheck = document.getElementById('focus-strict-mode-modal');
  const notifyEndCheck = document.getElementById('focus-notify-end-modal');
  
  const strictMode = strictModeCheck ? strictModeCheck.checked : false;
  const notifyEnd = notifyEndCheck ? notifyEndCheck.checked : true;
  
  // Confirmar modo estricto
  if (strictMode) {
    if (!confirm(' En modo estricto NO podrás cancelar hasta que finalice. ¿Continuar?')) {
      return;
    }
  }
  
  // Cerrar modal
  cerrarConfigFocus();
  
  // Enviar al backend
  fetch('/api/focus/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      duration_minutes: minutes,
      blocked_categories: categorias,
      allow_break: false,
      strict_mode: strictMode,
      notify_end: notifyEnd
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log('[FOCUS] Respuesta:', data);
    
    if (data.success) {
      focusDurationMinutes = minutes;
      focusCategoriasBloquedas = categorias;
      focusModoEstricto = strictMode;
      focusStartTime = new Date();
      
      // Notificar extensión
      notificarExtensionFocus('start', {
        categorias: categorias,
        strict: strictMode
      });
      
      // Cambiar UI
      mostrarEstadoActivoWidget();
      iniciarContador();
      
      // Guardar en localStorage
      localStorage.setItem('focus_active', JSON.stringify({
        start: focusStartTime.getTime(),
        duration: minutes,
        categories: categorias,
        strict: strictMode
      }));

      mostrarToast('success', `¡Modo Focus iniciado! ${minutes} min `);
    } else {
      mostrarToast('error', 'Error: ' + data.message);
    }
  })
  .catch(error => {
    console.error('[FOCUS] Error:', error);
    mostrarToast('error', 'Error de conexión');
  });
}

// ==================== INICIAR DESDE PÁGINA COMPLETA /focus ====================
function iniciarModoFocus() {
  console.log('[FOCUS] Iniciando desde página completa...');
  
  // Obtener duración
  const durationSelect = document.getElementById('focus-duration');
  let minutes = parseInt(durationSelect ? durationSelect.value : 25);
  
  if (durationSelect && durationSelect.value === 'custom') {
    const customInput = document.getElementById('focus-duration-custom');
    minutes = parseInt(customInput.value);
    if (!minutes || minutes < 1 || minutes > 480) {
      mostrarToast('error', 'Duración inválida (1-480 minutos)');
      return;
    }
  }
  
  // Obtener categorías seleccionadas
  const checkboxes = document.querySelectorAll('#focus-categories-list input[type="checkbox"]:checked');
  const categorias = Array.from(checkboxes).map(cb => cb.value);
  
  if (categorias.length === 0) {
    mostrarToast('error', 'Selecciona al menos una categoría');
    return;
  }
  
  // Obtener opciones
  const allowBreakCheck = document.getElementById('focus-allow-break');
  const strictModeCheck = document.getElementById('focus-strict-mode');
  const notifyEndCheck = document.getElementById('focus-notify-end');
  
  const strictMode = strictModeCheck ? strictModeCheck.checked : false;
  const notifyEnd = notifyEndCheck ? notifyEndCheck.checked : true;
  
  // Confirmar modo estricto
  if (strictMode) {
    if (!confirm(' En modo estricto NO podrás cancelar hasta que finalice. ¿Continuar?')) {
      return;
    }
  }
  
  console.log('[FOCUS] Configuración:', { minutes, categorias, strictMode, notifyEnd });
  
  // Enviar al backend
  fetch('/api/focus/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      duration_minutes: minutes,
      blocked_categories: categorias,
      allow_break: allowBreakCheck ? allowBreakCheck.checked : false,
      strict_mode: strictMode,
      notify_end: notifyEnd
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log('[FOCUS] Respuesta del servidor:', data);
    
    if (data.success) {
      focusDurationMinutes = minutes;
      focusCategoriasBloquedas = categorias;
      focusModoEstricto = strictMode;
      focusStartTime = new Date();
      
        const tipo = getTipoConfiguracion(minutes);
        guardarConfiguracion(tipo, {
          duration: minutes,
          categories: categorias,
          strict_mode: strictMode,
          allow_break: allowBreakCheck ? allowBreakCheck.checked : false,
          notify_end: notifyEnd
        });
      // Notificar extensión
      notificarExtensionFocus('start', {
        categorias: categorias,
        strict: strictMode
      });
      
      // Cambiar UI
      mostrarEstadoActivoPagina();
      iniciarContador();
      
      // Guardar en localStorage
      localStorage.setItem('focus_active', JSON.stringify({
        start: focusStartTime.getTime(),
        duration: minutes,
        categories: categorias,
        strict: strictMode
      }));

      mostrarToast('success', `¡Modo Focus iniciado! ${minutes} min `);
    } else {
      mostrarToast('error', 'Error: ' + data.message);
    }
  })
  .catch(error => {
    console.error('[FOCUS] Error:', error);
    mostrarToast('error', 'Error de conexión');
  });
}

// ==================== SELECT ALL CATEGORIES (página /focus) ====================
function selectAllCategories() {
  const checkboxes = document.querySelectorAll('#focus-categories-list input[type="checkbox"]');
  const allChecked = Array.from(checkboxes).every(cb => cb.checked);
  
  checkboxes.forEach(cb => {
    cb.checked = !allChecked;
  });
}

// ==================== UI - MOSTRAR ESTADO ====================
function mostrarEstadoActivoWidget() {
  console.log('[FOCUS] Mostrando estado activo en widget');
  
  // Ocultar estado inactivo
  const inactiveState = document.getElementById('focus-inactive-state');
  if (inactiveState) inactiveState.style.display = 'none';
  
  // Mostrar estado activo
  const activeState = document.getElementById('focus-active-state');
  if (activeState) activeState.style.display = 'flex';
  
  // Badge
  const badge = document.getElementById('focus-status-badge');
  if (badge) {
    badge.textContent = 'Activo';
    badge.classList.add('active');
  }
  
  // Mostrar categorías bloqueadas
  const tagsContainer = document.getElementById('focus-blocked-tags-mini');
  if (tagsContainer) {
    tagsContainer.innerHTML = '';
    focusCategoriasBloquedas.forEach(cat => {
      const emoji = obtenerEmojiCategoria(cat);
      const tag = document.createElement('span');
      tag.className = 'blocked-tag-mini';
      tag.textContent = `${emoji} ${cat}`;
      tagsContainer.appendChild(tag);
    });
  }
  
  // Contador de categorías
  const countElem = document.getElementById('focus-categories-count');
  if (countElem) countElem.textContent = focusCategoriasBloquedas.length;
}

function mostrarEstadoActivoPagina() {
  console.log('[FOCUS] Mostrando estado activo en página completa');
  
  // En la página completa /focus
  const inactiveState = document.getElementById('focus-inactive-state');
  const activeState = document.getElementById('focus-active-state');
  const badge = document.getElementById('focus-status-badge');
  
  if (inactiveState) inactiveState.style.display = 'none';
  if (activeState) activeState.style.display = 'block';
  if (badge) {
    badge.textContent = 'Activo';
    badge.classList.add('active');
  }
  
  // Actualizar categorías bloqueadas
  const tagsContainer = document.getElementById('focus-blocked-tags');
  if (tagsContainer) {
    tagsContainer.innerHTML = '';
    focusCategoriasBloquedas.forEach(cat => {
      const emoji = obtenerEmojiCategoria(cat);
      const tag = document.createElement('span');
      tag.className = 'blocked-tag';
      tag.textContent = `${emoji} ${cat}`;
      tagsContainer.appendChild(tag);
    });
  }
  
  // Actualizar contador de categorías
  const countElem = document.getElementById('focus-blocked-count');
  if (countElem) countElem.textContent = focusCategoriasBloquedas.length;
}

function mostrarEstadoInactivoWidget() {
  // Mostrar estado inactivo
  const inactiveState = document.getElementById('focus-inactive-state');
  if (inactiveState) inactiveState.style.display = 'flex';
  
  // Ocultar estado activo
  const activeState = document.getElementById('focus-active-state');
  if (activeState) activeState.style.display = 'none';
  
  // Badge
  const badge = document.getElementById('focus-status-badge');
  if (badge) {
    badge.textContent = 'Inactivo';
    badge.classList.remove('active');
  }
}

// ==================== CONTADOR ====================
function iniciarContador() {
  if (focusInterval) clearInterval(focusInterval);
  focusInterval = setInterval(actualizarContador, 1000);
  actualizarContador(); // Actualizar inmediatamente
}

function actualizarContador() {
  if (focusPausado) return;
  
  const ahora = new Date();
  const transcurrido = Math.floor((ahora - focusStartTime) / 1000);
  const totalSegundos = focusDurationMinutes * 60;
  const restante = totalSegundos - transcurrido;
  
  if (restante <= 0) {
    finalizarModoFocus(true);
    return;
  }
  
  // Formatear tiempo
  const minutos = Math.floor(restante / 60);
  const segundos = restante % 60;
  const tiempoFormateado = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
  
  // Actualizar todos los elementos de countdown
  const countdowns = [
    'focus-countdown',
    'sidebar-countdown',
    'modal-countdown'
  ];
  
  countdowns.forEach(id => {
    const elem = document.getElementById(id);
    if (elem) elem.textContent = tiempoFormateado;
  });
  
  // Actualizar barra de progreso
  const progreso = ((totalSegundos - restante) / totalSegundos) * 100;
  const barras = [
    'focus-progress-fill',
    'progress-fill-mini',
    'sidebar-progress',
    'modal-progress'
  ];
  
  barras.forEach(id => {
    const elem = document.getElementById(id);
    if (elem) elem.style.width = progreso + '%';
  });
}

// ==================== PAUSAR ====================
function pausarModoFocus() {
  focusPausado = !focusPausado;
  
  const btns = document.querySelectorAll('.btn-focus-pause-mini, .btn-focus-pause');
  btns.forEach(btn => {
    btn.innerHTML = focusPausado 
      ? '<i class="fas fa-play"></i> Reanudar'
      : '<i class="fas fa-pause"></i> Pausar';
  });
  
  mostrarToast('info', focusPausado ? 'Sesión pausada' : 'Sesión reanudada');
}

// ==================== FINALIZAR ====================
async function finalizarModoFocus(completed) {
  // Si es modo estricto y no completó, preguntar
  if (focusModoEstricto && !completed) {
    if (!confirm(' Modo estricto activo. ¿Seguro que quieres cancelar? Se registrará como incompleta.')) {
      return;
    }
  }
  
  clearInterval(focusInterval);
  focusInterval = null;
  
  try {
    const response = await fetch('/api/focus/end', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: completed })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Notificar extensión
      notificarExtensionFocus('end', {});
      
      // Mostrar notificación
      if (completed) {
        mostrarToast('success', `¡Sesión completada!  ${focusDurationMinutes} minutos de concentración`);
      } else {
        mostrarToast('info', 'Sesión cancelada');
      }
      
      // Limpiar estado
      localStorage.removeItem('focus_active');
      focusDurationMinutes = 0;
      focusCategoriasBloquedas = [];
      focusModoEstricto = false;
      focusStartTime = null;
      
      // Cambiar UI
      mostrarEstadoInactivoWidget();
      
      // Recargar historial si estamos en /focus
      if (typeof cargarHistorialSesiones === 'function') {
        cargarHistorialSesiones();
      }
    }
  } catch (error) {
    console.error('[FOCUS] Error finalizando:', error);
    mostrarToast('error', 'Error al finalizar sesión');
  }
}

// ==================== NOTIFICAR EXTENSIÓN ====================
function notificarExtensionFocus(action, data) {
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
    const EXTENSION_ID = 'hcghpalkgapkbklfnhkfoialdcneafod'
    
    chrome.runtime.sendMessage(
      EXTENSION_ID,
      { action: action, data: data },
      response => {
        if (chrome.runtime.lastError) {
          console.warn('[FOCUS] Extensión no disponible:', chrome.runtime.lastError.message);
        } else {
          console.log('[FOCUS] Extensión notificada:', response);
        }
      }
    );
  } else {
    console.warn('[FOCUS] Chrome extension API no disponible');
  }
}

// ==================== VERIFICAR SESIÓN ACTIVA ====================
async function verificarSesionActiva() {
  console.log('[FOCUS] Verificando sesión activa...');
  
  try {
    const response = await fetch('/api/focus/status');
    const data = await response.json();
    
    if (data.success && data.active) {
      console.log('[FOCUS] Sesión activa detectada, restaurando...');
      
      // Restaurar variables
      focusDurationMinutes = data.duracion_minutos;
      focusCategoriasBloquedas = data.categorias_bloqueadas;
      focusModoEstricto = data.modo_estricto;
      
      // Calcular startTime basado en tiempo restante
      const tiempoRestante = data.tiempo_restante_minutos;
      const tiempoTranscurrido = focusDurationMinutes - tiempoRestante;
      focusStartTime = new Date(Date.now() - (tiempoTranscurrido * 60000));
      
      // Mostrar UI activa (widget o página)
      if (document.getElementById('focus-mode-widget')) {
        mostrarEstadoActivoWidget();
      }
      if (document.getElementById('focus-mode-container')) {
        mostrarEstadoActivoPagina();
      }
      
      iniciarContador();
      
      // Notificar extensión
      notificarExtensionFocus('start', {
        categorias: focusCategoriasBloquedas,
        strict: focusModoEstricto
      });
      
      console.log('[FOCUS] Sesión restaurada correctamente');
    } else {
      console.log('[FOCUS] No hay sesión activa');
    }
  } catch (error) {
    console.error('[FOCUS] Error verificando sesión:', error);
  }
}

// ==================== TOASTS ====================
function mostrarToast(tipo, mensaje) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
    `;
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${tipo}`;
  toast.style.cssText = `
    padding: 15px 20px;
    background: ${tipo === 'success' ? '#2ecc71' : tipo === 'error' ? '#e74c3c' : '#3498db'};
    color: white;
    border-radius: 8px;
    margin-bottom: 10px;
    animation: slideInRight 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    min-width: 250px;
  `;
  toast.textContent = mensaje;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', function() {
  console.log('[FOCUS] Inicializando Focus Mode...');
  
  // Verificar sesión activa
  verificarSesionActiva();
  
  // Actualizar contador de bloqueos cada minuto
  setInterval(async () => {
    if (focusInterval) {
      try {
        const response = await fetch('/api/focus/status');
        const data = await response.json();
        if (data.active && data.blocks_count !== undefined) {
          const elem = document.getElementById('focus-blocks-count') || document.getElementById('focus-blocks-today');
          if (elem) elem.textContent = data.blocks_count;
        }
      } catch (error) {
        console.error('[FOCUS] Error actualizando stats:', error);
      }
    }
  }, 60000);
  
  console.log('[FOCUS] Inicialización completa');
});

// ==================== CSS ANIMACIONES ====================
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// ==================== GUARDAR/CARGAR CONFIGURACIONES ====================

function getTipoConfiguracion(minutos) {
  if (minutos === 15) return 'quick';
  if (minutos === 25) return 'pomodoro';
  if (minutos === 45 || minutos === 90) return 'deepwork';
  return 'custom';
}

function guardarConfiguracion(tipo, config) {
  const configs = JSON.parse(localStorage.getItem('focus_configs') || '{}');
  configs[tipo] = {
    duration: config.duration,
    categories: config.categories,
    strict_mode: config.strict_mode,
    allow_break: config.allow_break,
    notify_end: config.notify_end,
    timestamp: Date.now()
  };
  localStorage.setItem('focus_configs', JSON.stringify(configs));
  console.log(`[FOCUS] Config guardada para "${tipo}":`, config);
}

function cargarConfiguracion(tipo) {
  const configs = JSON.parse(localStorage.getItem('focus_configs') || '{}');
  return configs[tipo] || null;
}