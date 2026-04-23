/**
 * Sistema de feedback para clasificaciones automáticas
 */

let notificacionActual = null;
let categoriasClasificacion = []; 
let colaPendientes = [];

// Inicializar al cargar página
document.addEventListener('DOMContentLoaded', () => {
    cargarCategorias();
    verificarNotificacionesPendientes();
    
    // Verificar cada 30 segundos
    setInterval(verificarNotificacionesPendientes, 30000);
});

async function cargarCategorias() {
    try {
        const response = await fetch('/api/categorias');
        const data = await response.json();
        categoriasClasificacion = data.categorias || [];
        
        // Llenar selector
        const select = document.getElementById('categoriaCorrecta');
        if (select) {
            select.innerHTML = categoriasClasificacion.map(cat => 
                `<option value="${cat.id}">${cat.nombre}</option>`
            ).join('');
        }
    } catch (error) {
        console.error('[CLASIFICACIÓN] Error cargando categorías:', error);
    }
}

async function verificarNotificacionesPendientes() {
    try {
        const response = await fetch('/api/clasificacion/pendientes');
        const data = await response.json();
        
        if (data.pendientes && data.pendientes.length > 0) {
            colaPendientes = data.pendientes;
            
            // Mostrar primera notificación si no hay una activa
            if (!notificacionActual) {
                mostrarSiguienteNotificacion();
            }
        }
    } catch (error) {
        console.error('[CLASIFICACIÓN] Error verificando pendientes:', error);
    }
}

function mostrarSiguienteNotificacion() {
    if (colaPendientes.length === 0) {
        console.log('[CLASIFICACIÓN] No hay más notificaciones pendientes');
        return;
    }
    
    notificacionActual = colaPendientes.shift();
    mostrarModalClasificacion(notificacionActual);
}

function mostrarModalClasificacion(notif) {
    const esManual = notif.metodo === 'manual_required';
    
    // Llenar datos básicos
    document.getElementById('clasificacion-dominio').textContent = notif.dominio;
    
    // Configurar modal según tipo
    const modal = document.getElementById('modalClasificacion');
    const modalHeader = document.getElementById('modal-header');
    const modalIcono = document.getElementById('modal-icono');
    const modalTitulo = document.getElementById('modal-titulo');
    const contenidoAutomatico = document.getElementById('contenido-automatico');
    const contenidoManual = document.getElementById('contenido-manual');
    const selectorCategoria = document.getElementById('selectorCategoria');
    
    if (esManual) {
        // MODO: Clasificación Manual Requerida
        modal.classList.add('manual-mode');
        modalIcono.textContent = '❓';
        modalTitulo.textContent = 'Clasificación Manual Requerida';
        
        contenidoAutomatico.classList.add('hidden');
        contenidoManual.classList.remove('hidden');
        selectorCategoria.classList.remove('hidden');
        
        // Pre-seleccionar "Sin categoría" si existe
        const select = document.getElementById('categoriaCorrecta');
        const sinCategoriaOption = Array.from(select.options).find(
            opt => opt.text.toLowerCase().includes('sin categoría')
        );
        if (sinCategoriaOption) {
            select.value = sinCategoriaOption.value;
        }
        
        console.log('[CLASIFICACIÓN] Modo: Manual requerida');
        
    } else {
        // MODO: Confirmación de clasificación automática
        modal.classList.remove('manual-mode');
        modalIcono.textContent = '🤖';
        modalTitulo.textContent = 'Clasificación Automática';
        
        contenidoAutomatico.classList.remove('hidden');
        contenidoManual.classList.add('hidden');
        selectorCategoria.classList.add('hidden');
        
        // Llenar info de clasificación automática
        document.getElementById('clasificacion-categoria').textContent = notif.categoria_sugerida;
        
        const confBadge = document.getElementById('clasificacion-confianza');
        const confianza = Math.round(notif.confianza * 100);
        confBadge.textContent = `${confianza}%`;
        
        // Color según confianza
        if (confianza >= 80) {
            confBadge.style.background = '#dcfce7';
            confBadge.style.color = '#15803d';
        } else if (confianza >= 60) {
            confBadge.style.background = '#fef3c7';
            confBadge.style.color = '#a16207';
        } else {
            confBadge.style.background = '#fee2e2';
            confBadge.style.color = '#991b1b';
        }
        
        // Método
        const metodoTexto = notif.metodo === 'ml' ? 
            '🤖 Clasificado con Machine Learning' : 
            '📝 Clasificado con reglas';
        document.getElementById('clasificacion-metodo').textContent = metodoTexto;
        
        console.log('[CLASIFICACIÓN] Modo: Confirmación automática');
    }
    
    // Mostrar modal
    modal.classList.remove('hidden');
}

function cerrarModalClasificacion() {
    document.getElementById('modalClasificacion').classList.add('hidden');
    notificacionActual = null;
}

async function confirmarClasificacion() {
    if (!notificacionActual) return;
    
    try {
        const response = await fetch(`/api/clasificacion/confirmar/${notificacionActual.id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarToast('✅ Clasificación confirmada', 'success');
            cerrarModalClasificacion();
            
            // Mostrar siguiente si hay más
            setTimeout(() => {
                if (colaPendientes.length > 0) {
                    mostrarSiguienteNotificacion();
                }
            }, 500);
        }
    } catch (error) {
        console.error('[CLASIFICACIÓN] Error confirmando:', error);
        mostrarToast('❌ Error al confirmar', 'error');
    }
}

function mostrarSelectorCategoria() {
    document.getElementById('selectorCategoria').classList.remove('hidden');
    
    // Preseleccionar categoría actual
    const select = document.getElementById('categoriaCorrecta');
    const catActual = categoriasClasificacion.find(c => c.nombre === notificacionActual.categoria_sugerida);
    if (catActual) {
        select.value = catActual.id;
    }
}

async function guardarCorreccion() {
    if (!notificacionActual) return;
    
    const categoriaCorrecta = document.getElementById('categoriaCorrecta').value;
    
    if (!categoriaCorrecta) {
        mostrarToast('⚠️ Selecciona una categoría', 'warning');
        return;
    }
    
    const esManual = notificacionActual.metodo === 'manual_required';
    const endpoint = esManual ? 
        `/api/clasificacion/clasificar_manual/${notificacionActual.id}` :
        `/api/clasificacion/rechazar/${notificacionActual.id}`;
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                categoria_correcta_id: parseInt(categoriaCorrecta)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const catNombre = categoriasClasificacion.find(c => c.id == categoriaCorrecta)?.nombre || '';
            const mensaje = esManual ? 
                `✅ Sitio clasificado como: ${catNombre}` :
                `✅ Corregido a: ${catNombre}`;
            
            mostrarToast(mensaje, 'success');
            cerrarModalClasificacion();
            
            // Mostrar siguiente
            setTimeout(() => {
                if (colaPendientes.length > 0) {
                    mostrarSiguienteNotificacion();
                }
            }, 500);
        }
    } catch (error) {
        console.error('[CLASIFICACIÓN] Error guardando:', error);
        mostrarToast('❌ Error al guardar', 'error');
    }
}

function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-clasificacion ${tipo}`;
    toast.textContent = mensaje;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInUp 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// GET /api/categorias
