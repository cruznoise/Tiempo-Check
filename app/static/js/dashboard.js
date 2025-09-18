// === Utils para dataset robusto ===
function parseDatasetJSON(key, fallback = {}) {
  try {
    const raw = document.body.dataset[key];
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (e) {
    console.warn('parseDatasetJSON falló para', key, e);
    return fallback;
  }
}

const datos       = parseDatasetJSON('datos', []);         // array [{dominio,total}]
let categoriasRaw = parseDatasetJSON('categorias', {});    // objeto {cat:min} o array [{categoria,minutos}]
const usoHorario  = parseDatasetJSON('usoHorario', []);    // array [{hora,total}]
const usoDiario   = parseDatasetJSON('usoDiario', []);     // array [{dia,total}]

function normalizarCategorias(raw) {
  let obj = {};
  if (Array.isArray(raw)) {
    obj = raw.reduce((acc, row) => {
      const cat = row.categoria ?? 'Sin categoría';
      acc[cat] = (acc[cat] || 0) + Number(row.minutos || 0);
      return acc;
    }, {});
  } else if (raw && typeof raw === 'object') {
    obj = { ...raw };
  }

  const aliases = ['SinCategoria', 'Sin categoria', 'sin categoria', 'sincategoria'];
  let carry = 0;
  for (const k of aliases) {
    if (obj[k] != null) {
      carry += Number(obj[k] || 0);
      delete obj[k];
    }
  }
  if (carry > 0) obj['Sin categoría'] = (obj['Sin categoría'] || 0) + carry;

  return obj;
}

const categorias = normalizarCategorias(categoriasRaw);

// === Referencias canvas ===
const ctx = document.getElementById('grafica').getContext('2d');
const ctxCat = document.getElementById('graficaPastel').getContext('2d');
const ctxHorario = document.getElementById('graficaHorario').getContext('2d');
const ctxLinea = document.getElementById('graficaLinea').getContext('2d');

let grafica, graficaPastel, graficaHorario, graficaLinea;

function crearGraficas() {
  const style = getComputedStyle(document.body);
  const colorPrimary = style.getPropertyValue('--chart-primary-color');
  const colorSecondary = style.getPropertyValue('--chart-secondary-color');
  const colorAccents = style.getPropertyValue('--chart-accents').split(',').map(s => s.trim());
  const textColor = style.getPropertyValue('--text');

  if (grafica) grafica.destroy();
  if (graficaPastel) graficaPastel.destroy();
  if (graficaHorario) graficaHorario.destroy();
  if (graficaLinea) graficaLinea.destroy();

  const tooltipOptions = {
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    titleColor: '#fff',
    bodyColor: '#fff',
    borderColor: '#fff',
    borderWidth: 1,
    borderRadius: 8,
    displayColors: false,
    bodyFont: { size: 14 },
    titleFont: { size: 16, weight: 'bold' },
    padding: 12
  };

  grafica = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: datos.map(d => d.dominio),
      datasets: [{
        label: 'Tiempo total (min)',
        data: datos.map(d => d.total),
        backgroundColor: colorPrimary,
        borderColor: colorSecondary,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { maxRotation: 90, minRotation: 45, autoSkip: false, color: textColor }, grid: { color: 'rgba(255,255,255,0.1)' } },
        y: { beginAtZero: true, ticks: { color: textColor }, grid: { color: 'rgba(255,255,255,0.1)' } }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: {
          ...tooltipOptions,
          callbacks: { footer: () => 'Estos son los sitios donde pasaste más tiempo.' }
        }
      }
    }
  });

  graficaPastel = new Chart(ctxCat, {
    type: 'pie',
    data: {
      labels: Object.keys(categorias),
      datasets: [{
        label: 'Tiempo por categoría (min)',
        data: Object.values(categorias),
        backgroundColor: colorAccents,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: {
          ...tooltipOptions,
          callbacks: { footer: () => 'Agrupa los sitios por categorías generales.' }
        }
      }
    }
  });

  graficaHorario = new Chart(ctxHorario, {
    type: 'line',
    data: {
      labels: usoHorario.map(e => `${e.hora}:00`),
      datasets: [{
        label: 'Minutos en pantalla por hora',
        data: usoHorario.map(e => e.total),
        backgroundColor: `${colorPrimary}33`,
        borderColor: colorPrimary,
        tension: 0.2,
        fill: true
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Minutos', color: textColor }, ticks: { color: textColor } },
        x: { title: { display: true, text: 'Hora del día', color: textColor }, ticks: { color: textColor } }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: { ...tooltipOptions }
      }
    }
  });

  graficaLinea = new Chart(ctxLinea, {
    type: 'line',
    data: {
      labels: usoDiario.map(e => e.dia),
      datasets: [{
        label: 'Minutos por día',
        data: usoDiario.map(e => e.total),
        backgroundColor: `${colorPrimary}33`,
        borderColor: colorPrimary,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { beginAtZero: true, ticks: { color: textColor } },
        x: { ticks: { color: textColor } }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: { ...tooltipOptions }
      }
    }
  });
}

document.body.addEventListener('temaCambiado', crearGraficas);

document.addEventListener("DOMContentLoaded", async () => {
  crearGraficas();

  const rangoSel = document.getElementById('rango');
  rangoSel.addEventListener('change', () => {
    const seleccion = rangoSel.value;
    document.getElementById('fechas').style.display = (seleccion === 'entre') ? 'block' : 'none';
    if (seleccion !== 'entre') window.location.href = `/dashboard?rango=${seleccion}`;
  });

  document.getElementById('filtrar').addEventListener('click', () => {
    const desde = document.getElementById('desde').value;
    const hasta = document.getElementById('hasta').value;
    if (desde && hasta) window.location.href = `/dashboard?rango=entre&desde=${desde}&hasta=${hasta}`;
  });

  // === Resumen ===
  try {
    const res = await fetch('/resumen');
    const data = await res.json();
    document.getElementById('resumen-tiempo').textContent = `${data.tiempo_total} minutos`;
    document.getElementById('resumen-dia').textContent = `${data.dia_mas_activo} (${data.tiempo_dia_top} min)`;
    document.getElementById('resumen-sitio').textContent = `${data.sitio_mas_visitado} (${data.tiempo_sitio_top} min)`;
    document.getElementById('resumen-categoria').textContent = `${data.categoria_dominante} (${data.tiempo_categoria_top} min)`;
    document.getElementById('resumen-promedio').textContent = `${data.promedio_diario} min/día`;
  } catch (err) {
    console.error("Error al cargar resumen:", err);
  }

  // === Modal alertas ===
  function mostrarModal(mensaje) {
    document.getElementById('categoriaModal').textContent = mensaje;
    document.getElementById('alertaModal').classList.remove('hidden');
  }
  window.cerrarModal = () => document.getElementById('alertaModal').classList.add('hidden');
  window.ignorarAlerta = () => document.getElementById('alertaModal').classList.add('hidden');

  const currentDomain = window.location.hostname;
  try {
    const resp = await fetch('/admin/api/alerta_dominio', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dominio: currentDomain })
    });
    const data = await resp.json();
    if (data.alerta) mostrarModal(data.mensaje);
  } catch (err) {
    console.error("Error al verificar alerta dominio:", err);
  }

  // === Estado features (QA) ===
  async function pintarEstado(dia) {
    const qs = new URLSearchParams({ usuario_id: 1, dia });
    const [est, qa] = await Promise.all([
      fetch(`/admin/api/features_estado?${qs}`).then(r => r.json()),
      fetch(`/admin/api/features_qa?${qs}`).then(r => r.json())
    ]);
    document.querySelector("#fd-count").textContent = est.diarias_count ?? '0';
    document.querySelector("#fh-count").textContent = est.horarias_count ?? '0';
    const badge = document.querySelector("#qa-badge");
    if (qa.ok) {
      badge.textContent = "QA OK";
      badge.className = "badge badge-success";
    } else {
      badge.textContent = "QA DESCUADRE";
      badge.className = "badge badge-danger";
    }
  }
  function isoHoyMX() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth()+1).padStart(2,'0');
    const d = String(now.getDate()).padStart(2,'0');
    return `${y}-${m}-${d}`;
  }
  await pintarEstado(isoHoyMX());

  // === Predicciones ML ===
  function minsToHM(m) {
    const mm = Math.round(m);
    const h = Math.floor(mm / 60);
    const mi = mm % 60;
    return (h > 0 ? `${h}h ` : "") + `${mi}m`;
  }
  try {
    const r = await fetch('/api/ml/predict');
    const data = await r.json();
    const ul = document.getElementById('ml-predict-list');
    ul.innerHTML = '';
    (data.predicciones || []).forEach(p => {
      const li = document.createElement('li');
      li.textContent = `${p.categoria}: ${minsToHM(p.yhat_minutos)}`;
      ul.appendChild(li);
    });
    if (!data.predicciones || data.predicciones.length === 0) {
      ul.innerHTML = '<li>Sin suficiente historial aún</li>';
    }
  } catch (err) {
    console.error("Error en predicciones ML:", err);
  }

  // === Persistencia de tema ===
  const guardado = localStorage.getItem("tema_usuario");
  const temaSelect = document.getElementById('selector-tema');
  const modoToggle = document.getElementById('modoDiaNoche');
  if (guardado) {
    const [temaClass, modoClass] = guardado.split(" ");
    document.body.classList.forEach(cls => {
      if (cls.startsWith("theme-") || cls === "day" || cls === "night") document.body.classList.remove(cls);
    });
    document.body.classList.add(temaClass, modoClass);
    if (temaSelect && modoToggle) {
      temaSelect.value = temaClass.replace("theme-", "");
      modoToggle.checked = modoClass === "night";
    }
  }
});
