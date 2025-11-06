// dashboard.js 

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

const ALL_DATOS = parseDatasetJSON('datos', []); // array [{dominio,total}]
let datos = [...ALL_DATOS];
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

function filtrarDatosPorRango(rango) {
  let min = 0;
  let max = Infinity;

  switch (rango) {
    case 'top1000':
      min = 1000;
      break;
    case 'rango500_999':
      min = 500;
      max = 999;
      break;
    case 'rango150_499':
      min = 150;
      max = 499;
      break;
    case 'rango0_149':
      max = 149; 
      break;
    case 'todos':
    default:
      min = 0;
      max = Infinity;
      break;
  }

  if (rango !== 'slider') {
    datos = ALL_DATOS.filter(d => d.total >= min && d.total <= max);
  }

  const sliderMax = document.getElementById('slider-top-sites').value;
  if (sliderMax) {
      datos.sort((a, b) => b.total - a.total); // Asegurar el orden descendente
      datos = datos.slice(0, parseInt(sliderMax, 10));
  }
}

// === Función para ajustar ancho dinámico de gráfica de barras ===
function ajustarAnchoGrafica(numSitios) {
  const canvas = document.getElementById('grafica');
  const wrapper = canvas.closest('.chart-canvas-wrapper');
  
  if (!canvas || !wrapper) return;
  
  // Calcular ancho necesario (mínimo 80px por sitio)
  const anchoPorSitio = 80;
  const anchoMinimo = numSitios * anchoPorSitio;
  const anchoWrapper = wrapper.clientWidth;
  
  if (anchoMinimo > anchoWrapper) {
    // Hay overflow, activar scroll
    canvas.style.width = `${anchoMinimo}px`;
    wrapper.style.overflowX = 'scroll';
  } else {
    // Cabe todo, sin scroll
    canvas.style.width = '100%';
    wrapper.style.overflowX = 'hidden';
  }
  
  // Forzar actualización de Chart.js
  if (grafica) {
    grafica.resize();
  }
}

function crearGraficas() {
  const style = getComputedStyle(document.body);
  
  // LECTURA AJUSTADA DE VARIABLES DE TEMA
  // Usamos .trim() para asegurar que no haya espacios al inicio o final del valor de la variable CSS.
  const colorPrimary = style.getPropertyValue('--chart-primary-color').trim();
  const colorSecondary = style.getPropertyValue('--chart-secondary-color').trim();
  
  // Lectura del color del texto para ejes y leyendas (CORRECCIÓN: Se usa --chart-text-color si existe, sino --text)
  const textColor = style.getPropertyValue('--chart-text-color').trim() || style.getPropertyValue('--text').trim();
  
  // Lectura de los acentos para la gráfica de pastel (se espera una cadena CSV)
  const pieAccents = style.getPropertyValue('--chart-accents').split(',').map(s => s.trim());

  // Asegurar la destrucción de gráficas existentes antes de crear las nuevas
  if (grafica) grafica.destroy();
  if (graficaPastel) graficaPastel.destroy();
  if (graficaHorario) graficaHorario.destroy();
  if (graficaLinea) graficaLinea.destroy();

  const tooltipOptions = {
    // Usamos colores fijos para el tooltip ya que el fondo es oscuro para mejor legibilidad
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
  // 1. Gráfica de Barras (Tiempo por sitio web)
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
        x: { 
          ticks: { maxRotation: 90, minRotation: 45, autoSkip: false, color: textColor }, 
          // Ajuste de color de grid para que sea sutil en cualquier tema
          grid: { color: 'rgba(255,255,255,0.1)' } 
        },
        y: { 
          beginAtZero: true, 
          ticks: { color: textColor }, 
          grid: { color: 'rgba(255,255,255,0.1)' } 
        }
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
ajustarAnchoGrafica(datos.length);
// === FILTRO DINÁMICO POR MINUTOS (SELECT) ===
// === FILTRO DINÁMICO POR MINUTOS (SELECT) ===
const filtroMinutos = document.getElementById('filtro-minutos');

if (filtroMinutos && grafica) {
  const datosOriginales = [...datos];

  filtroMinutos.addEventListener('change', () => {
    const minLimit = parseInt(filtroMinutos.value);
    const filtrados = datosOriginales.filter(d => d.total >= minLimit);
    
    // Actualizar datos
    grafica.data.labels = filtrados.map(d => d.dominio);
    grafica.data.datasets[0].data = filtrados.map(d => d.total);
    
    // Ajustar ancho según cantidad de sitios
    ajustarAnchoGrafica(filtrados.length);
    
    // Actualizar gráfica
    grafica.update('none');
  });
}

  // 2. Gráfica de Pastel (Distribución por categoría)
  graficaPastel = new Chart(ctxCat, {
    type: 'pie',
    data: {
      labels: Object.keys(categorias),
      datasets: [{
        label: 'Tiempo por categoría (min)',
        data: Object.values(categorias),
        // CORRECCIÓN CLAVE: USAMOS EL ARRAY DE COLORES LEÍDO DEL TEMA
        backgroundColor: pieAccents, 
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

  // 3. Gráfica de Línea (Distribución de uso por hora)
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
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { 
          beginAtZero: true, 
          title: { display: true, text: 'Minutos', color: textColor }, 
          ticks: { color: textColor } 
        },
        x: { 
          title: { display: true, text: 'Hora del día', color: textColor }, 
          ticks: { color: textColor } 
        }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: { ...tooltipOptions }
      }
    }
  });

  // 4. Gráfica de Línea (Tiempo total en pantalla por día)
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

  // === Lógica de filtros de rango del Dashboard (FILTRO PRINCIPAL) ===
  // Buscamos 'rango-dashboard' para evitar el conflicto de IDs
  const rangoSelDashboard = document.getElementById('rango-dashboard'); 
  if(rangoSelDashboard) {
    rangoSelDashboard.addEventListener('change', () => {
      const seleccion = rangoSelDashboard.value;
      const fechasDiv = document.getElementById('fechas');
      if(fechasDiv) fechasDiv.style.display = (seleccion === 'entre') ? 'block' : 'none';
      if (seleccion !== 'entre') window.location.href = `/dashboard?rango=${seleccion}`;
    });

    const filtrarBtn = document.getElementById('filtrar');
    if(filtrarBtn) {
      filtrarBtn.addEventListener('click', () => {
        const desde = document.getElementById('desde').value;
        const hasta = document.getElementById('hasta').value;
        if (desde && hasta) window.location.href = `/dashboard?rango=entre&desde=${desde}&hasta=${hasta}`;
      });
    }
  }

  // === Lógica para el Menú Desplegable de Configuración ===
  const btnConfig = document.getElementById('btnConfiguracion');
  const menuConfig = document.getElementById('menuFlotanteConfig');

  if (btnConfig && menuConfig) {
    btnConfig.addEventListener('click', (e) => {
      e.preventDefault(); 
      e.stopPropagation(); 
      menuConfig.classList.toggle('hidden');
    });

    // Cierra el menú si se hace clic fuera de él
    document.addEventListener('click', (e) => {
      if (!menuConfig.contains(e.target) && !btnConfig.contains(e.target) && !menuConfig.classList.contains('hidden')) {
        menuConfig.classList.add('hidden');
      }
    });
  }

  // === Fetch resumen ===
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
    try {
      const [est, qa] = await Promise.all([
        fetch(`/admin/api/features_estado?${qs}`).then(r => r.json()),
        fetch(`/admin/api/features_qa?${qs}`).then(r => r.json())
      ]);
      const fdCount = document.querySelector("#fd-count");
      if(fdCount) fdCount.textContent = est.diarias_count ?? '0';
      const fhCount = document.querySelector("#fh-count");
      if(fhCount) fhCount.textContent = est.horarias_count ?? '0';

      const badge = document.querySelector("#qa-badge");
      if (badge) {
          if (qa.ok) {
            badge.textContent = "QA OK";
            badge.className = "badge badge-success";
          } else {
            badge.textContent = "QA DESCUADRE";
            badge.className = "badge badge-danger";
          }
      }
    } catch (err) {
      console.warn("[WARN] No se pudo pintar estado:", err);
    }
  }
  
  function isoHoyMX() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth()+1).padStart(2,'0');
    const d = String(now.getDate()).padStart(2,'0');
    return `${y}-${m}-${d}`;
  }
  
  // Aseguramos que solo se pinte el estado si existen los elementos
  if (document.querySelector("#fd-count")) {
      await pintarEstado(isoHoyMX());
  }

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
    if (ul) {
      ul.innerHTML = '';
      (data.predicciones || []).forEach(p => {
        const li = document.createElement('li');
        li.textContent = `${p.categoria}: ${minsToHM(p.yhat_minutos)}`;
        ul.appendChild(li);
      });
      if (!data.predicciones || data.predicciones.length === 0) {
        ul.innerHTML = '<li>Sin suficiente historial aún</li>';
      }
    }
  } catch (err) {
    console.error("Error en predicciones ML:", err);
  }

  // === Carga de tema inicial ===
  const guardado = localStorage.getItem("tema_usuario");
  const temaSelect = document.getElementById('selector-tema');
  const modoToggle = document.getElementById('modoNocheToggle');
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