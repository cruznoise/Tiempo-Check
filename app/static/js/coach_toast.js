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
  const cont = document.getElementById('coach-alertas');
  cont.innerHTML = ""; 
  alertas.forEach(a => {
    const card = document.createElement('div');
    card.className = `alerta-card severidad-${a.severidad}`;
    card.innerHTML = `
      <h4>${a.titulo}</h4>
      <p>${a.mensaje}</p>
      <small>${new Date(a.creado_en).toLocaleString()}</small>
    `;
    cont.appendChild(card);
  });
}

async function checkCoachAlertas() {
  const hoy = new Date().toISOString().slice(0, 10);
  const res = await fetch(`/admin/api/coach/alertas?fecha=${hoy}`);
  if (!res.ok) return;

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
