// === Dataset desde HTML ===
const datos = JSON.parse(document.body.dataset.datos);
const categorias = JSON.parse(document.body.dataset.categorias);
const usoHorario = JSON.parse(document.body.dataset.usoHorario);
const usoDiario = JSON.parse(document.body.dataset.usoDiario);

// Referencias a los canvas de las gráficas
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

  // Destruir instancias previas para evitar duplicados
  if (grafica) grafica.destroy();
  if (graficaPastel) graficaPastel.destroy();
  if (graficaHorario) graficaHorario.destroy();
  if (graficaLinea) graficaLinea.destroy();

  // Opciones de Tooltip personalizadas
  const tooltipOptions = {
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    titleColor: '#fff',
    bodyColor: '#fff',
    borderColor: '#fff',
    borderWidth: 1,
    borderRadius: 8,
    displayColors: false,
    bodyFont: {
      size: 14
    },
    titleFont: {
      size: 16,
      weight: 'bold'
    },
    padding: 12
  };

  // === Gráfica por dominio (Barras) ===
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
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        x: {
          ticks: { maxRotation: 90, minRotation: 45, autoSkip: false, color: textColor },
          grid: { color: 'rgba(255, 255, 255, 0.1)' }
        },
        y: { beginAtZero: true, ticks: { color: textColor }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: {
          ...tooltipOptions,
          callbacks: {
            footer: (context) => {
              return 'Estos son los sitios donde pasaste más tiempo en el periodo seleccionado. El análisis te puede ayudar a detectar hábitos repetitivos o páginas que demandan mucha atención.';
            }
          }
        }
      }
    }
  });

  // === Gráfica por categoría (Pastel) ===
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
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: {
          ...tooltipOptions,
          callbacks: {
            footer: (context) => {
              return 'Esta gráfica agrupa los sitios por categorías generales. Así puedes visualizar el equilibrio (o desequilibrio) entre actividades de ocio, redes, productividad, educación, etc.';
            }
          }
        }
      }
    }
  });

  // === Gráfica de uso por hora (Línea) ===
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
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Minutos', color: textColor }, ticks: { color: textColor }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
        x: { title: { display: true, text: 'Hora del día', color: textColor }, ticks: { color: textColor }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: {
          ...tooltipOptions,
          callbacks: {
            footer: (context) => {
              return 'Aquí se representa el tiempo total que pasas frente a la pantalla según la hora del día. Este gráfico te ayuda a visualizar en qué momentos eres más propenso a usar el dispositivo, lo que puede ser útil para planificar tus hábitos.';
            }
          }
        }
      }
    }
  });

  // === Gráfica por día (Línea) ===
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
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: { beginAtZero: true, ticks: { color: textColor }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
        x: { ticks: { color: textColor }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
      },
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: {
          ...tooltipOptions,
          callbacks: {
            footer: (context) => {
              return 'Aquí se muestra tu tiempo total frente a la pantalla por día. Identifica si tus hábitos están subiendo o bajando. Ideal para reconocer días con mayor distracción o foco.';
            }
          }
        }
      }
    }
  });
}

// Escuchar el evento personalizado de temas
document.body.addEventListener('temaCambiado', crearGraficas);

// Inicializar gráficas al cargar la página y configurar otros scripts
document.addEventListener("DOMContentLoaded", () => {
    crearGraficas();

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

    // === Lógica para obtener el dominio actual y enviar la alerta ===
    const currentDomain = window.location.hostname;

    fetch('/admin/api/alerta_dominio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dominio: currentDomain })
    })
    .then(res => res.json())
    .then(data => {
        if (data.alerta) {
            mostrarModal(data.mensaje);
        }
    })
    .catch(err => console.error("Error al verificar alerta:", err));
}); 