function showCoachToast(msg) {
  const box = document.createElement('div');
  box.className = 'toast';
  box.style.cssText = 'background:#222;color:#fff;padding:12px 14px;margin-top:8px;border-radius:10px;box-shadow:0 8px 20px rgba(0,0,0,.25);max-width:320px';
  box.textContent = msg;
  document.getElementById('toast-container').appendChild(box);
  setTimeout(() => box.remove(), 6000);
}

async function checkCoachAlertas() {
  const hoy = new Date().toISOString().slice(0,10);
  const res = await fetch(`/admin/api/coach/alertas?fecha=${hoy}`);
  if (!res.ok) return;
  const data = await res.json();
  (data.alertas || []).forEach(a => {
    if (a.regla === 'exceso_diario') {
      showCoachToast(`Exceso en ${a.categoria}: ${a.detalle}`);
    }
  });
}

// Llamar al cargar dashboard y cada cierto tiempo (si quieres polling simple)
document.addEventListener('DOMContentLoaded', () => {
  checkCoachAlertas();
  setInterval(checkCoachAlertas, 5 * 60 * 1000);
});