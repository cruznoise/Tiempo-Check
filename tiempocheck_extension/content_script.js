const dominioActual = window.location.hostname.replace('www.', '');
console.log("🌐 Dominio detectado:", dominioActual);

// Inicia verificación directa + intervalos
verificarAlerta();
iniciarIntervaloVerificacion();

// Función principal de verificación
function verificarAlerta() {
  chrome.storage.local.get(["recordatorios", "tiempoRecordatorio", "alertasMostradas"], (data) => {
    const recordatorios = data.recordatorios || {};
    const ultimaVez = recordatorios[dominioActual] || 0;
    const ahora = Date.now();
    const tiempoEsperaMs = (data.tiempoRecordatorio || 1) * 60 * 1000;
    const tiempoTranscurrido = ahora - ultimaVez;

    if (tiempoTranscurrido < tiempoEsperaMs) {
      console.log(`⏳ Aún no ha pasado el tiempo de espera. Faltan ${(tiempoEsperaMs - tiempoTranscurrido) / 1000}s`);
      return;
    }

    fetch("http://localhost:5000/admin/api/alerta_dominio", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ dominio: dominioActual })
})

    .then(res => res.json())
    .then(response => {
      console.log("📨 Respuesta de alerta:", response);

      if (!response.alerta) return;

      if (response.tipo === "exceso") {
        mostrarAlertaPersonalizada(response.mensaje);
      } else if (response.tipo === "proximidad") {
        const alertas = data.alertasMostradas || {};
        const hoy = new Date().toDateString();

        if (alertas[dominioActual] === hoy) {
          console.log("🔁 Alerta de proximidad ya mostrada hoy.");
          return;
        }

        mostrarAlertaProximidad(response.mensaje);

        // Guardar marca de alerta de proximidad
        const nuevasAlertas = { ...alertas, [dominioActual]: hoy };
        chrome.storage.local.set({ alertasMostradas: nuevasAlertas });
      }
    })
    .catch(err => console.error("❌ Error en fetch:", err));
  });
}

function iniciarIntervaloVerificacion() {
  const intervaloMs = 30 * 1000; // Verifica cada 30 segundos

  setInterval(() => {
    verificarAlerta(); // Internamente ya evalúa si mostrar o no
  }, intervaloMs);

  console.log(`🔄 Intervalo de verificación: cada ${intervaloMs / 1000} segundos`);
}


// Modal de EXCESO
function mostrarAlertaPersonalizada(mensaje) {
  if (document.getElementById("alertaModal")) return;

  const modal = document.createElement("div");
  modal.id = "alertaModal";
  modal.style = modalStyle();

modal.innerHTML = `
  <div style="${modalBoxStyle()}">
    <h2 style="margin-top: 0; font-weight: bold;">⏳ TiempoCheck</h2>
    <p style="margin-bottom: 20px; font-size: 16px;">❗ ${mensaje}</p>

    <label for="tiempoRecordatorio" style="font-size: 14px; display: block; margin-bottom: 5px; color: #ffffff;">¿En cuánto tiempo quieres que te lo vuelva a recordar?</label>
    <div style="margin-bottom: 20px;">
      <select id="tiempoRecordatorio" style="
      width: 100%;
      padding: 8px;
      border-radius: 6px;
      font-size: 14px;
      -webkit-appearance: none;
      height: 38px;
      ">

        <option value="5">5 minutos</option>
        <option value="10" selected>10 minutos</option>
        <option value="15">15 minutos</option>
        <option value="30">30 minutos</option>
        <option value="60">60 minutos</option>
      </select>
    </div>

    <div style="display: flex; justify-content: center; gap: 10px;">
      <button id="cerrarPestana" style="${btnStyle('#ff4d4d')}">Aceptar y cerrar</button>
      <button id="guardarRecordatorio" style="${btnStyle('#444')}">Guardar y recordar</button>
    </div>
  </div>
`;

  document.body.appendChild(modal);

  document.getElementById("cerrarPestana").addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "cerrar_pestana" });
    modal.remove();
  });

  document.getElementById("guardarRecordatorio").addEventListener("click", () => {
    const seleccionado = document.getElementById("tiempoRecordatorio").value;
    chrome.storage.local.get("recordatorios", (data) => {
      const recordatorios = data.recordatorios || {};
      const ahora = Date.now();
      const nuevoRegistro = { ...recordatorios, [dominioActual]: ahora };

      chrome.storage.local.set({
        tiempoRecordatorio: parseInt(seleccionado),
        recordatorios: nuevoRegistro
      }, () => {
        console.log(`📥 Guardado: ${seleccionado} min para ${dominioActual}`);
        modal.remove();
      });
    });
  });
}

// Modal de PROXIMIDAD
function mostrarAlertaProximidad(mensaje) {
  if (document.getElementById("alertaProximidad")) return;

  const modal = document.createElement("div");
  modal.id = "alertaProximidad";
  modal.style = modalStyle();

  modal.innerHTML = `
    <div style="${modalBoxStyle('#fff')}">
      <h2 style="color: #e67e22;">⚠️ Advertencia</h2>
      <p style="margin: 20px 0; color: #333;">${mensaje}</p>
      <button id="cerrarProximidad" style="${btnStyle('#e67e22')}">Aceptar</button>
    </div>
  `;

  document.body.appendChild(modal);
  document.getElementById("cerrarProximidad").addEventListener("click", () => {
    modal.remove();
  });
}

// Estilos reutilizables
function modalStyle() {
  return `
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: auto !important;
    height: auto !important;
    background-color: rgba(0, 0, 0, 0.75) !important;
    z-index: 999999 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    font-family: 'Segoe UI', sans-serif !important;
    padding: 0 !important;
    margin: 0 !important;
  `;
}


function modalBoxStyle(bg = "rgba(61, 90, 128, 0.7)") {
  return `
    background-color: ${bg};
    color: #ffffff;
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    max-width: 400px;
    box-shadow: 0 0 15px rgba(0,0,0,0.5);
  `;
}

function btnStyle(color) {
  return `
    background-color: ${color};
    border: none;
    padding: 10px 20px;
    margin: 10px 5px;
    color: white;
    border-radius: 8px;
    cursor: pointer;
  `;
}
