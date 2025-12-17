// Sistema de Detección de Anomalías
let anomaliasDetectadas = [];
let anomaliaActual = null;
let motivoSeleccionado = null;

// Detectar anomalías al cargar dashboard
async function detectarAnomalias() {
  console.log('[ANOMALÍAS] Detectando anomalías...');
  
  try {
    const response = await fetch('/api/anomalias/recientes');
    const data = await response.json();
    
    console.log('[ANOMALÍAS]  Respuesta:', data);
    
    if (data.anomalias && data.anomalias.length > 0) {
      anomaliasDetectadas = data.anomalias;
      
      console.log('[ANOMALÍAS]  Anomalías encontradas:', data.total);
      
      // Mostrar la primera anomalía
      setTimeout(() => {
        console.log('[ANOMALÍAS]  Mostrando primera anomalía');
        mostrarModalAnomalia(anomaliasDetectadas[0]);
      }, 2000);
    } else {
      console.log('[ANOMALÍAS] No hay anomalías para mostrar');
    }
  } catch (error) {
    console.error('[ANOMALÍAS] Error al detectar:', error);
  }
}

// Mostrar modal con anomalía
function mostrarModalAnomalia(anomalia) {
  anomaliaActual = anomalia;
  
  const fecha = new Date(anomalia.fecha);
  const diasSemana = ['domingos', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábados'];
  const diaSemana = diasSemana[fecha.getDay()];
  
  const desviacion = anomalia.desviacion_pct;
  const esMayor = desviacion > 0;
  
  // Formatear fecha bonita
  const fechaBonita = fecha.toLocaleDateString('es-MX', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
  
  // Llenar datos en el modal
  document.getElementById('anomalia-fecha').textContent = fechaBonita;
  document.getElementById('anomalia-diferencia').textContent = 
    esMayor ? `${Math.abs(desviacion).toFixed(0)}% más` : `${Math.abs(desviacion).toFixed(0)}% menos`;
  document.getElementById('anomalia-real').textContent = 
    `${anomalia.uso_real.toFixed(0)} minutos (${(anomalia.uso_real / 60).toFixed(1)}h)`;
  document.getElementById('anomalia-esperado').textContent = 
    `${anomalia.uso_esperado.toFixed(0)} minutos (${(anomalia.uso_esperado / 60).toFixed(1)}h)`;
  document.getElementById('anomalia-dia-semana').textContent = diaSemana;
  
  // Mostrar modal
  document.getElementById('modalAnomalia').classList.remove('hidden');
  
  // Reset selección
  motivoSeleccionado = null;
  document.querySelectorAll('.motivo-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  document.getElementById('btnGuardar').disabled = true;
  document.getElementById('detalleExtra').classList.add('hidden');
  document.getElementById('motivoDetalle').value = '';
}

// Cerrar modal
function cerrarModalAnomalia() {
  document.getElementById('modalAnomalia').classList.add('hidden');
  
  // Si hay más anomalías pendientes, preguntar después
  if (anomaliasDetectadas.length > 1) {
    anomaliasDetectadas.shift(); // Quitar la primera
    // Podríamos mostrar la siguiente después, pero mejor no molestar mucho
  }
}

// Seleccionar motivo
document.addEventListener('DOMContentLoaded', () => {
  // Event listeners para botones de motivo
  document.querySelectorAll('.motivo-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      // Deseleccionar todos
      document.querySelectorAll('.motivo-btn').forEach(b => b.classList.remove('selected'));
      
      // Seleccionar este
      this.classList.add('selected');
      motivoSeleccionado = this.dataset.motivo;
      
      // Habilitar botón guardar
      document.getElementById('btnGuardar').disabled = false;
      
      // Mostrar campo de detalle si es "otro"
      if (motivoSeleccionado === 'otro') {
        document.getElementById('detalleExtra').classList.remove('hidden');
      } else {
        document.getElementById('detalleExtra').classList.add('hidden');
      }
    });
  });
  
  // Detectar anomalías si estamos en el dashboard
  if (window.location.pathname === '/dashboard') {
    detectarAnomalias();
  }
});

// Guardar motivo
async function guardarMotivoAnomalia() {
  if (!motivoSeleccionado || !anomaliaActual) return;
  
  const btnGuardar = document.getElementById('btnGuardar');
  btnGuardar.disabled = true;
  btnGuardar.textContent = 'Guardando...';
  
  const detalle = document.getElementById('motivoDetalle').value;
  
  try {
    const response = await fetch('/api/anomalias/guardar-motivo', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fecha: anomaliaActual.fecha,
        motivo: motivoSeleccionado,
        detalle: detalle
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Mostrar mensaje de éxito
      mostrarToast('✅ ¡Gracias! Esto me ayudará a mejorar las predicciones', 'success');
      
      // Cerrar modal
      cerrarModalAnomalia();
    } else {
      throw new Error(data.error || 'Error al guardar');
    }
  } catch (error) {
    console.error('[ANOMALÍAS] Error al guardar:', error);
    mostrarToast('❌ Error al guardar. Intenta de nuevo.', 'error');
    btnGuardar.disabled = false;
    btnGuardar.textContent = 'Guardar motivo';
  }
}

// Toast notification
function mostrarToast(mensaje, tipo = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${tipo}`;
  toast.textContent = mensaje;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: ${tipo === 'success' ? '#10b981' : '#ef4444'};
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

// CSS para animaciones
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(400px); opacity: 0; }
  }
`;
document.head.appendChild(style);
