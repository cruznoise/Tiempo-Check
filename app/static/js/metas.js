fetch('/admin/api/logros')
  .then(res => {
    if (!res.ok) throw new Error("Respuesta no válida");
    return res.json();
  })
  .then(data => {
    const contenedor = document.getElementById('contenedor-logros');
    console.log(" Logros recibidos:", data); 
    data.forEach(logro => {
      const div = document.createElement('div');
      div.className = `insignia ${logro.nivel} ${logro.desbloqueado ? '' : 'locked'}`;
      div.innerHTML = `
        <img src="/static/icons/logro.png" alt="${logro.nombre}">
        <h3>${logro.nombre}</h3>
        <p>${logro.descripcion}</p>
      `;
      contenedor.appendChild(div);
    });
  })
  .catch(err => console.error(" Error al cargar logros:", err));

/** 
 * ATENCION!!!
 * EL BLOQUE SIGUIENTE SE ENCUENTRA COMENTADO, YA QUE EL ENDPOINT API/SUGERENCIAS FUE SUSTITUIDO BAJO EL COACH
 * INTELIGENTE, SIN EMBARGO AUN SE ENCUENTRA DISPONIBLE, EN CASO DE QUE EL COACH TUVIERA ALGUN ERROR, USAR EL ENDPOINT
 * /API/SUGERENCIAS, ASI SE GARANTIZA TENERLO DISPONIBLE EN CASO DE ALGUN ERROR.
 * **/

/*document.addEventListener("DOMContentLoaded", function () {
    const contenedor = document.getElementById("contenedor-sugerencias");
    const usuarioId = contenedor.dataset.usuario;

    fetch("/admin/api/sugerencias")
        .then(response => response.json())
        .then(data => {
            // Vaciar contenedor antes de renderizar
            contenedor.innerHTML = '';

            // Caso: backend devuelve un objeto con mensaje (insuficiente)
            if (!Array.isArray(data)) {
                document.getElementById("sugerenciasMetas").style.display = "block";
                contenedor.innerHTML = `
                    <div class="tile-card alerta-info">
                        <p>${data.mensaje || 'Aún no hay sugerencias disponibles.'}</p>
                    </div>
                `;
                return;
            }

            // Caso: array vacío
            if (data.length === 0) {
                document.getElementById("sugerenciasMetas").style.display = "none";
                return;
            }

            const categoriasProductivas = ["Productividad", "Estudio", "Trabajo", "Herramientas"];

            data.forEach(sug => {
                const tarjeta = document.createElement("div");
                tarjeta.classList.add("tile-card");

                // Color para nivel de confianza
                let colorConfianza = 'gray';
                if (sug.nivel_confianza === 'baja') colorConfianza = 'red';
                if (sug.nivel_confianza === 'media') colorConfianza = 'orange';
                if (sug.nivel_confianza === 'alta') colorConfianza = 'green';

                const esProductiva = categoriasProductivas.includes(sug.categoria_nombre);

                // Render condicional: solo meta en productivas, solo límite en no productivas
                tarjeta.innerHTML = `
                    <h3>${sug.categoria_nombre}</h3>
                    ${ esProductiva
                        ? `<p>Meta sugerida: <strong>${sug.sugerencia_meta} minutos</strong></p>`
                        : `<p>Límite sugerido: <strong>${sug.sugerencia_limite} minutos</strong></p>` }
                    <p>Confianza: <span style="color:${colorConfianza}; font-weight:bold;">
                        ${sug.nivel_confianza.toUpperCase()}
                    </span></p>
                    <button class="btn-aplicar-sugerencia" 
                            data-categoria="${sug.categoria_id}" 
                            data-meta="${sug.sugerencia_meta}"
                            data-limite="${sug.sugerencia_limite}"
                            ${sug.nivel_confianza === 'insuficiente' ? 'disabled' : ''}>
                        Aplicar sugerencia
                    </button>
                `;

                contenedor.appendChild(tarjeta);
            });

            // Eventos para aplicar sugerencias (meta o límite según categoría)
            document.querySelectorAll(".btn-aplicar-sugerencia").forEach(btn => {
                btn.addEventListener("click", async function () {
                    const categoriaId = this.dataset.categoria;
                    const meta = this.dataset.meta;
                    const limite = this.dataset.limite;
                    const nombre = this.parentElement.querySelector("h3").textContent;

                    const categoriasProductivas = ["Productividad", "Estudio", "Trabajo", "Herramientas"];
                    const esProductiva = categoriasProductivas.includes(nombre);

                    let endpoint = esProductiva 
                        ? "/admin/api/agregar_meta" 
                        : "/admin/api/agregar_limite";

                    let body = esProductiva 
                        ? `usuario_id=${usuarioId}&categoria_id=${categoriaId}&meta_minutos=${meta}`
                        : `usuario_id=${usuarioId}&categoria_id=${categoriaId}&limite_minutos=${limite}`;

                    try {
                        const res = await fetch(endpoint, {
                            method: "POST",
                            headers: { "Content-Type": "application/x-www-form-urlencoded" },
                            body: body
                        });

                        if (res.ok) {
                            location.reload();
                        } else {
                            alert("Error al aplicar sugerencia.");
                        }
                    } catch (err) {
                        console.error("Error al aplicar sugerencia:", err);
                        alert("Hubo un error al aplicar la sugerencia.");
                    }
                });
            });
        })
        .catch(err => {
            console.error("Error al cargar sugerencias:", err);
        });
});

async function fetchSugerenciasDetalle() {
  const res = await fetch('/api/sugerencias_detalle');
  if (!res.ok) return null;
  return await res.json();
}

let cacheDetalle = null;
document.addEventListener('click', async (e) => {
  if (e.target.matches('[data-role="ver-explicacion"]')) {
    const cat = e.target.getAttribute('data-categoria');
    if (!cacheDetalle) cacheDetalle = await fetchSugerenciasDetalle();
    const item = (cacheDetalle?.detalle || []).find(x => x.categoria === cat);
    const texto = item ? 
`Categoría: ${item.categoria}
Promedio (14 días): ${item.promedio_14d.toFixed(2)} min
Multiplicador: ${item.multiplicador.toFixed(2)}
Nivel de confianza: ${item.nivel_confianza}
Fórmula: ${item.formula}
Sugerencia: ${item.sugerencia_minutos} min`
    :
`Aún no hay suficientes datos para explicar esta sugerencia.`;
    document.getElementById('explicacion-texto').textContent = texto;
    document.getElementById('modal-explicacion').style.display = 'block';
  }
  if (e.target.id === 'cerrar-explicacion') {
    document.getElementById('modal-explicacion').style.display = 'none';
  }
});*/
document.addEventListener("DOMContentLoaded", async () => {
  const API_URL = "/api/ml/predict_multi?usuario_id=1";
  const sel = document.getElementById("categoriaSelect");
  const ctx = document.getElementById("chartPredicciones")?.getContext("2d");
  let chart;

  // Cargar predicciones multi-horizonte
  async function cargarPredicciones() {
    try {
      const res = await fetch(API_URL);
      const data = await res.json();
      if (data.status !== "ok") throw new Error(data.msg);

      const categorias = Object.keys(data.categorias);
      sel.innerHTML = ""; // limpiar
      categorias.forEach(cat => {
        const opt = document.createElement("option");
        opt.value = cat;
        opt.textContent = cat;
        sel.appendChild(opt);
      });

      window.predData = data;
      
      // Actualizar estado
      const estadoPred = document.getElementById('estadoPred');
      if(estadoPred) estadoPred.textContent = '✓ Predicciones cargadas';
      
    } catch (e) {
      console.error("[UI][Predicciones] Error:", e);
      const estadoPred = document.getElementById('estadoPred');
      if(estadoPred) estadoPred.textContent = '⚠️ Error al cargar';
    }
  }

  // Colores de barra según carga
  function colorPorCarga(valor, media, p80) {
    if (valor < media) return "#28a745";   // verde
    if (valor < p80) return "#ffc107";     // amarillo
    return "#dc3545";                      // rojo
  }

  // Render del gráfico
  function renderChart(cat) {
    if (!ctx || !window.predData || !window.predData.categorias[cat]) return;

    const registros = window.predData.categorias[cat];
    const umbral = window.predData.umbrales[cat] || { media: 0, p80: 0 };

    const labels = registros.map(r => r.fecha_pred);
    const valores = registros.map(r => r.yhat_minutos);
    const colores = valores.map(v => colorPorCarga(v, umbral.media, umbral.p80));

    if (chart) chart.destroy();
    
    // Obtener colores del tema actual
    const style = getComputedStyle(document.body);
    const textColor = style.getPropertyValue('--chart-text-color').trim() || style.getPropertyValue('--text').trim();
    
    chart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Minutos predichos",
          data: valores,
          backgroundColor: colores,
          borderColor: "#444",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            display: false 
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            callbacks: {
              label: ctx => `${ctx.parsed.y.toFixed(1)} min`
            }
          }
        },
        scales: {
          y: {
            title: { 
              display: true, 
              text: "Minutos",
              color: textColor
            },
            beginAtZero: true,
            ticks: { color: textColor }
          },
          x: {
            ticks: { color: textColor }
          }
        }
      }
    });
  }

  if(sel) {
    sel.addEventListener("change", e => renderChart(e.target.value));
  }

  // Registrar acción y sugerencia (con meta coach)
  async function registrarAccionYCrearSugerencia(cat, tipoAccion, minutos, fecha) {
    try {
      const accionPayload = { categoria: cat, fecha, minutos_predichos: minutos };

      // Registrar acción
      await fetch("/admin/api/coach/accion_log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          usuario_id: 1,
          origen: "metas",
          origen_id: null,
          accion: tipoAccion,
          payload: accionPayload,
        }),
      });

      const sugerencia = {
        usuario_id: 1,
        tipo: tipoAccion === "establecer_meta" ? "meta_personalizada" : "recomendacion_carga",
        categoria: cat,
        titulo:
          tipoAccion === "establecer_meta"
            ? `Nueva meta para ${cat}`
            : `Revisión de carga: ${cat}`,
        cuerpo:
          tipoAccion === "establecer_meta"
            ? `Se sugiere fijar una meta de ${Math.round(minutos * 0.9)} min el ${fecha}.`
            : `Se recomienda ajustar tu dedicación a ${cat} (valor predicho: ${Math.round(minutos)} min).`,
        action_type: "none",
        action_payload: accionPayload,
      };

      const resSug = await fetch("/admin/api/coach/sugerencia_insert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sugerencia),
      });

      const dataSug = await resSug.json();
      if (dataSug.status === "ok") {
        console.log(`[COACH][OK] ${dataSug.msg}`);
        
        // Mostrar toast de éxito
        if(typeof showToast === 'function') {
          showToast(
            tipoAccion === "establecer_meta"
              ? "✅ Meta del Coach registrada correctamente."
              : "✅ Revisión de carga registrada correctamente.",
            'success'
          );
        } else {
          alert(
            tipoAccion === "establecer_meta"
              ? "✅ Meta del Coach registrada correctamente."
              : "✅ Revisión de carga registrada correctamente."
          );
        }
      } else {
        console.warn("[COACH][WARN]", dataSug.msg);
        if(typeof showToast === 'function') {
          showToast(`⚠️ ${dataSug.msg || "Error registrando sugerencia."}`, 'warning');
        } else {
          alert(`Alerta: ${dataSug.msg || "Error registrando sugerencia."}`);
        }
      }
    } catch (e) {
      console.error("[COACH][ERR]", e);
      if(typeof showToast === 'function') {
        showToast("❌ Error al registrar acción o sugerencia", 'error');
      } else {
        alert("Error al registrar acción o sugerencia (ver consola).");
      }
    }
  }

  const btnMeta = document.getElementById("btnMeta");
  const btnRevision = document.getElementById("btnRevision");

  if(btnMeta) {
    btnMeta.addEventListener("click", async () => {
      const cat = sel.value;
      if (!cat) {
        if(typeof showToast === 'function') {
          showToast("⚠️ Selecciona una categoría primero.", 'warning');
        } else {
          alert("Selecciona una categoría primero.");
        }
        return;
      }

      const registros = window.predData.categorias[cat];
      if (!registros?.length) {
        if(typeof showToast === 'function') {
          showToast("⚠️ No hay predicciones para esta categoría.", 'warning');
        } else {
          alert("No hay predicciones para esta categoría.");
        }
        return;
      }

      const fecha = registros[0].fecha_pred;
      const minutos = registros[0].yhat_minutos;
      await registrarAccionYCrearSugerencia(cat, "establecer_meta", minutos, fecha);
    });
  }

  if(btnRevision) {
    btnRevision.addEventListener("click", async () => {
      const cat = sel.value;
      if (!cat) {
        if(typeof showToast === 'function') {
          showToast("⚠️ Selecciona una categoría primero.", 'warning');
        } else {
          alert("Selecciona una categoría primero.");
        }
        return;
      }

      const registros = window.predData.categorias[cat];
      if (!registros?.length) {
        if(typeof showToast === 'function') {
          showToast("⚠️ No hay predicciones para esta categoría.", 'warning');
        } else {
          alert("No hay predicciones para esta categoría.");
        }
        return;
      }

      const fecha = registros[0].fecha_pred;
      const minutos = registros[0].yhat_minutos;
      await registrarAccionYCrearSugerencia(cat, "revision_carga", minutos, fecha);
    });
  }

  await cargarPredicciones();
});