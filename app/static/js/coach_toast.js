function showCoachToast(msg) {
  const box = document.createElement('div');
  box.className = 'toast';
  box.style.cssText =
    'background:#222;color:#fff;padding:12px 14px;margin-top:8px;border-radius:10px;box-shadow:0 8px 20px rgba(0,0,0,.25);max-width:320px';
  box.textContent = msg;
  document.getElementById('toast-container').appendChild(box);
  setTimeout(() => box.remove(), 6000);
}

function renderCoachCards(alertas) {
  // El HTML N usa 'coach-alerts-list'
  const cont = document.getElementById('coach-alerts-list');
  // Se añade una comprobación por si el ID original existe
  if (!cont) {
    const contOriginal = document.getElementById('coach-alertas');
    if (contOriginal) contOriginal.innerHTML = "";
    else return;
  }
  
  cont.innerHTML = ""; 
  
  // Ocultar estado de carga si existe
  const loading = document.getElementById('coach-loading-state');
  if (loading) loading.classList.add('hidden');

  alertas.forEach(a => {
    // La clase 'alerta-card' es la que usa el CSS original para las tarjetas
    // El CSS N no la define directamente en el JS, pero usa la estructura.
    const card = document.createElement('div');
    // Usamos las clases del CSS N para el estilo visual
    card.className = `alerta-coach-box severidad-${a.severidad}`; 
    card.innerHTML = `
      <div class="alerta-coach-icon"><span>!</span></div>
      <div class="alerta-coach-contenido">
          <h4>${a.titulo}</h4>
          <p>${a.mensaje}</p>
          <small>${new Date(a.creado_en).toLocaleString()}</small>
      </div>
    `;
    cont.appendChild(card);
  });
  
  if (alertas.length === 0) {
      cont.innerHTML = '<p style="text-align:center; font-size:0.9em; opacity:0.7;">No hay alertas recientes.</p>';
  }
}

async function checkCoachAlertas() {
  const hoy = new Date().toISOString().slice(0, 10);
  const loading = document.getElementById('coach-loading-state');
  if (loading) loading.classList.remove('hidden');
  
  // Endpoint Mantenido
  const res = await fetch(`/admin/api/coach/alertas?fecha=${hoy}`);
  if (!res.ok) {
     if (loading) loading.classList.add('hidden');
     return;
  }

  const data = await res.json();
  const alertas = data.items || [];
  alertas.forEach(a => {
    if (a.tipo === 'exceso_diario') {
      showCoachToast(`${a.titulo}: ${a.mensaje}`);
    }
  });

  renderCoachCards(alertas);
}

document.addEventListener('DOMContentLoaded', () => {
  checkCoachAlertas();
  setInterval(checkCoachAlertas, 5 * 60 * 1000); 
});