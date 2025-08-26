
// === Dataset desde HTML ===
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

  // Fusiona variantes viejas (SinCategoria, etc.) en 'Sin categoría'
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

const categoriasObj = normalizarCategorias(categoriasRaw);

// === Gráfica por dominio ===
const ctx = document.getElementById('grafica').getContext('2d');
let grafica = crearGrafica(datos);

function crearGrafica(datos) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: datos.map(d => d.dominio),
      datasets: [{
        label: 'Tiempo total (min)',
        data: datos.map(d => d.total),
        backgroundColor: 'rgba(226, 241, 251, 0.7)',
        borderColor: 'rgba(255, 0, 251, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: { ticks: { maxRotation: 90, minRotation: 45, autoSkip: false } },
        y: { beginAtZero: true }
      }
    }
  });
}

// === Filtro de rango de tiempo ===
document.getElementById('rango').addEventListener('change', () => {
  const seleccion = document.getElementById('rango').value;
  document.getElementById('fechas').style.display = (seleccion === 'entre') ? 'block' : 'none';
  if (seleccion !== 'entre') {
    window.location.href = `/dashboard?rango=${seleccion}`;
  }
});

document.getElementById('filtrar').addEventListener('click', () => {
  const desde = document.getElementById('desde').value;
  const hasta = document.getElementById('hasta').value;
  if (desde && hasta) {
    window.location.href = `/dashboard?rango=entre&desde=${desde}&hasta=${hasta}`;
  }
});

// === Gráfica de uso por hora ===
const ctxHorario = document.getElementById('graficaHorario').getContext('2d');
new Chart(ctxHorario, {
  type: 'line',
  data: {
    labels: usoHorario.map(e => `${e.hora}:00`),
    datasets: [{
      label: 'Minutos en pantalla por hora',
      data: usoHorario.map(e => e.total),
      backgroundColor: 'rgba(255, 159, 64, 0.2)',
      borderColor: 'rgba(255, 159, 64, 1)',
      tension: 0.2,
      fill: true
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Minutos' }
      },
      x: {
        title: { display: true, text: 'Hora del día' }
      }
    }
  }
});


// === Gráfica por categoría ===
const ctxCat = document.getElementById('graficaPastel').getContext('2d');
const labelsCat = Object.keys(categoriasObj);
const dataCat = Object.values(categoriasObj);

// evita overlays al recargar en caliente
if (window._chartCat) window._chartCat.destroy();

window._chartCat = new Chart(ctxCat, {
  type: 'pie',
  data: {
    labels: labelsCat,
    datasets: [{
      label: 'Tiempo por categoría (min)',
      data: dataCat,
      backgroundColor: ['#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc948','#d073c4ff'],
      borderWidth: 1
    }]
  },
  options: { responsive: true }
});

// === Gráfica por día ===
const ctxLinea = document.getElementById('graficaLinea').getContext('2d');
new Chart(ctxLinea, {
  type: 'line',
  data: {
    labels: usoDiario.map(e => e.dia),
    datasets: [{
      label: 'Minutos por día',
      data: usoDiario.map(e => e.total),
      backgroundColor: 'rgba(54, 162, 235, 0.3)',
      borderColor: 'rgba(54, 162, 235, 1)',
      tension: 0.2
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero: true }
    }
  }
});

// === Resumen de actividad ===
fetch('/resumen')
  .then(response => response.json())
  .then(data => {
    document.getElementById('resumen-tiempo').textContent = `${data.tiempo_total} minutos`;
    document.getElementById('resumen-dia').textContent = `${data.dia_mas_activo} (${data.tiempo_dia_top} min)`;
    document.getElementById('resumen-sitio').textContent = `${data.sitio_mas_visitado} (${data.tiempo_sitio_top} min)`;
    document.getElementById('resumen-categoria').textContent = `${data.categoria_dominante} (${data.tiempo_categoria_top} min)`;
    document.getElementById('resumen-promedio').textContent = `${data.promedio_diario} min/día`;
  })
  .catch(err => {
    console.error("Error al cargar resumen:", err);
  });

// === Modal alerta por categoría ===
function mostrarModal(mensaje) {
  document.getElementById('categoriaModal').textContent = mensaje;
  document.getElementById('alertaModal').classList.remove('hidden');
}

function cerrarModal() {
  document.getElementById('alertaModal').classList.add('hidden');
}

function ignorarAlerta() {
  document.getElementById('alertaModal').classList.add('hidden');
}

// === DOMContentLoaded ===
document.addEventListener("DOMContentLoaded", () => {
  const guardado = localStorage.getItem("tema_usuario");
  const temaSelect = document.getElementById('selector-tema');
  const modoToggle = document.getElementById('modoDiaNoche');

  if (guardado) {
    const [temaClass, modoClass] = guardado.split(" ");
    document.body.classList.forEach(cls => {
      if (cls.startsWith("theme-") || cls === "day" || cls === "night") {
        document.body.classList.remove(cls);
      }
    });
    document.body.classList.add(temaClass, modoClass);

    if (temaSelect && modoToggle) {
      temaSelect.value = temaClass.replace("theme-", "");
      modoToggle.checked = modoClass === "night";
    }
  }

  // Verificar alerta de categoría (por ahora fija: categoría 3 = redes)
  fetch('/admin/api/alerta_categoria', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ categoria_id: 3 })
  })
    .then(res => res.json())
    .then(data => {
      if (data.alerta) {
        mostrarModal(data.mensaje);
      }
    })
    .catch(err => console.error("Error al verificar alerta:", err));
});

////
(async function(){
  function isoHoyMX() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth()+1).padStart(2,'0');
    const d = String(now.getDate()).padStart(2,'0');
    return `${y}-${m}-${d}`;
  }
  async function pintarEstado(dia) {
    const qs = new URLSearchParams({usuario_id: 1, dia});
    const [est, qa] = await Promise.all([
      fetch(`/admin/api/features_estado?${qs}`).then(r=>r.json()),
      fetch(`/admin/api/features_qa?${qs}`).then(r=>r.json())
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
  await pintarEstado(isoHoyMX());
})();