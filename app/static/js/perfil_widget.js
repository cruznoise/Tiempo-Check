/**
 * Widget de Perfil Adaptativo
 */

const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

// Cargar perfil al iniciar
document.addEventListener('DOMContentLoaded', () => {
    cargarPerfil();
});

async function cargarPerfil() {
    try {
        const response = await fetch('/api/perfil');
        const perfil = await response.json();
        
        if (perfil.error) {
            console.error('[PERFIL] Error:', perfil.error);
            return;
        }
        
        mostrarPerfil(perfil);
        
    } catch (error) {
        console.error('[PERFIL] Error cargando perfil:', error);
    }
}

function mostrarPerfil(perfil) {
    // Badge de confianza
    const badgeConfianza = document.getElementById('badge-confianza');
    const confianza = Math.round((perfil.confianza_inferencia || 0) * 100);
    
    if (confianza >= 80) {
        badgeConfianza.textContent = `${confianza}% Confiable`;
        badgeConfianza.className = 'badge badge-success';
    } else if (confianza >= 60) {
        badgeConfianza.textContent = `${confianza}% Buena`;
        badgeConfianza.className = 'badge badge-info';
    } else {
        badgeConfianza.textContent = `${confianza}% Inicial`;
        badgeConfianza.className = 'badge badge-warning';
    }
    
    // Tipo de usuario
    const tipoInferido = document.getElementById('perfil-tipo-inferido');
    const tipo = perfil.tipo_inferido || 'Sin determinar';
    const tipoCapitalizado = tipo.charAt(0).toUpperCase() + tipo.slice(1);
    
    tipoInferido.textContent = tipoCapitalizado;
    tipoInferido.className = `tipo-${tipo}`;
    
    // Mostrar declaración manual si existe
    const tipoManual = document.getElementById('perfil-tipo-manual');
    if (perfil.dedicacion_declarada) {
        tipoManual.textContent = `Declarado: ${perfil.dedicacion_declarada}`;
    }
    
    // Horario pico
    const horarioPico = document.getElementById('perfil-horario-pico');
    horarioPico.textContent = perfil.horario_pico || 'Sin datos';
    
    const horarioManual = document.getElementById('perfil-horario-manual');
    if (perfil.horario_preferido) {
        const horarioTexto = {
            'manana': 'Declarado: Mañana (8-13h)',
            'tarde': 'Declarado: Tarde (13-18h)',
            'noche': 'Declarado: Noche (18-23h)',
            'flexible': 'Declarado: Flexible'
        };
        horarioManual.textContent = horarioTexto[perfil.horario_preferido] || '';
    }
    
    // Días activos
    const diasActivosContainer = document.getElementById('perfil-dias-activos');
    
    if (perfil.dias_activos) {
        const diasActivos = perfil.dias_activos.split(',').map(d => parseInt(d));
        
        diasActivosContainer.innerHTML = diasSemana.map((dia, index) => {
            const activo = diasActivos.includes(index);
            return `<span class="badge ${activo ? 'activo' : ''}">${dia}</span>`;
        }).join('');
    } else {
        diasActivosContainer.innerHTML = '<small class="text-muted">Recopilando datos...</small>';
    }
    
    console.log('[PERFIL] Perfil cargado:', perfil);
}

async function actualizarPerfilManual() {
    const btn = event.target.closest('button');
    const iconOriginal = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualizando...';
    
    try {
        const response = await fetch('/api/perfil/actualizar', {
            method: 'POST'
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            // Mostrar toast de éxito
            mostrarToast('✅ Perfil actualizado correctamente', 'success');
            
            // Recargar perfil
            setTimeout(() => {
                cargarPerfil();
            }, 1000);
        } else {
            mostrarToast('⚠️ ' + resultado.mensaje, 'warning');
        }
        
    } catch (error) {
        console.error('[PERFIL] Error actualizando:', error);
        mostrarToast('❌ Error al actualizar perfil', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = iconOriginal;
    }
}

function mostrarToast(mensaje, tipo = 'info') {
    // Reutilizar función de clasificacion_feedback.js si existe
    if (typeof window.mostrarToast === 'function') {
        window.mostrarToast(mensaje, tipo);
        return;
    }
    
    // Fallback simple
    const toast = document.createElement('div');
    toast.className = `toast-clasificacion ${tipo}`;
    toast.textContent = mensaje;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10001;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

async function reentrenarClasificador() {
    const btn = event.target.closest('button');
    const iconOriginal = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Entrenando...';
    
    try {
        const response = await fetch('/api/clasificador/reentrenar', {
            method: 'POST'
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            const metricas = resultado.metricas;
            mostrarToast(
                `✅ Modelo reentrenado\n` +
                `Precisión: ${metricas.precision_anterior} → ${metricas.precision_nueva}\n` +
                `Mejora: ${metricas.mejora}`,
                'success'
            );
        } else {
            mostrarToast('⚠️ ' + resultado.error, 'warning');
        }
        
    } catch (error) {
        console.error('[CLASIFICADOR] Error:', error);
        mostrarToast('❌ Error al reentrenar', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = iconOriginal;
    }
}