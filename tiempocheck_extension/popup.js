let intervalId = null;

// === CONTROL DE DÍA NUEVO Y CARGA INICIAL ===
document.addEventListener("DOMContentLoaded", () => {
  const hoy = new Date().toDateString(); // "Tue Jul 15 2025"

  chrome.storage.local.get(['ultimaFecha'], (data) => {
    const ultimaFecha = data.ultimaFecha;

    if (ultimaFecha !== hoy) {
      chrome.storage.local.get(null, (allData) => {
        const historialDominios = allData.historialDominios || [];

        chrome.storage.local.clear(() => {
          chrome.storage.local.set({
            ultimaFecha: hoy,
            historialDominios: historialDominios  
          }, () => {
            console.log(" Historial reiniciado por nuevo día.");
            location.reload();
          });
        });
      });
    } else {
      iniciarPopup();
      cargarRachas(); 
    }
  });
});

// === LÓGICA PRINCIPAL DEL POPUP ===
function iniciarPopup() {
  const siteDisplay = document.getElementById("current-site");
  const timeDisplay = document.getElementById("time-spent");
  const listContainer = document.getElementById("site-list");

  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (!tab || !tab.url || !tab.url.startsWith("http")) {
      siteDisplay.textContent = "---";
      timeDisplay.textContent = "0 s";
      return;
    }

    const url = new URL(tab.url);
    const domain = url.hostname;
    siteDisplay.textContent = domain;

    chrome.storage.local.get(null, (result) => {
      const historial = result.historialDominios || [];
      let currentSeconds = result[domain] || 0;

      listContainer.innerHTML = "";
      for (const dom of historial) {
        const seconds = result[dom] || 0;
        const item = document.createElement("li");
        item.textContent = `${dom}: ${formatTime(seconds)}`;
        listContainer.appendChild(item);
      }

      if (intervalId !== null) clearInterval(intervalId);
      intervalId = updateLiveTime(timeDisplay, currentSeconds);
    });
  });
}

// === ACTUALIZADOR EN TIEMPO REAL ===
function updateLiveTime(element, initialSeconds) {
  let seconds = initialSeconds;
  element.textContent = formatTime(seconds);

  return setInterval(() => {
    seconds++;
    element.textContent = formatTime(seconds);
  }, 1000);
}

// === FORMATEO DE TIEMPO ===
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;

  if (seconds < 60) return `${secs} s`;
  else if (mins < 60) return `${mins}m ${secs}s`;
  else {
    const hrs = Math.floor(mins / 60);
    const minsRest = mins % 60;
    return `${hrs}h ${minsRest}m ${secs}s`;
  }
}

// === RACHAS: CONSULTA AL BACKEND Y GENERACIÓN DEL WIDGET ===
function cargarRachas() {
    const calendarContainer = document.getElementById('streak-calendar-visual');
    const totalStreakDisplay = document.getElementById('total-streak-days');
    const mainIcon = document.getElementById('main-streak-icon');
    
    // 1. GENERACIÓN DEL TEMPLATE SEMANAL (Vacío)
    const daysOfWeek = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
    
    calendarContainer.innerHTML = '';
    daysOfWeek.forEach((label, index) => {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'day-item';
        // Usamos el índice de 0 a 6 para identificar el día
        dayDiv.innerHTML = `
            <span class="day-status" data-status="pending" data-day-index="${index}"></span>
            <span class="day-label">${label}</span>
        `;
        calendarContainer.appendChild(dayDiv); 
    });
    
    // 2. OBTENER Y PROCESAR DATOS REALES (ENDPOINT ACTUALIZADO)
    fetch("http://localhost:5000/admin/api/estado_rachas", { credentials: 'include' })
    .then(async res => {
      const contentType = res.headers.get("content-type");
      if (!res.ok || !contentType.includes("application/json")) {
        // En caso de error o falta de sesión, usamos datos por defecto
        throw new Error("Respuesta no válida o sin sesión. Usando 0 días.");
      }
      return res.json();
    })
    .then(data => {
        const rachaMetas = data.metas || { activa: false, dias: 0 };
        const rachaLimites = data.limites || { activa: false, dias: 0 };

        // El total de la racha es el MÍNIMO, ya que ambos deben cumplirse
        const totalStreak = Math.max(rachaMetas.dias, rachaLimites.dias);
        
        // 3. Actualizar contadores y racha total
        document.getElementById("contador-racha-metas").textContent = rachaMetas.dias;
        document.getElementById("contador-racha-limites").textContent = rachaLimites.dias;
        totalStreakDisplay.textContent = totalStreak;

        // 4. Actualizar icono principal
        const iconContainer = mainIcon.parentElement; // El div.streak-icon
        if (totalStreak > 0) {
            mainIcon.src = "prendida.PNG"; 
            iconContainer.classList.remove('off');
        } else {
            mainIcon.src = "apagada.PNG"; 
            iconContainer.classList.add('off');
        }

        // 5. Actualizar visualización semanal
        // Si el backend proporciona historial_semanal (array de 7 días)
        if (data.historial_semanal && Array.isArray(data.historial_semanal) && data.historial_semanal.length === 7) {
            const dayStatusElements = document.querySelectorAll('.streak-calendar .day-status');
            
            data.historial_semanal.forEach((dayData, index) => {
                const dayElement = dayStatusElements[index];
                
                if (dayData.completed_both) { 
                    // Día con META Y LÍMITE cumplidos
                    dayElement.setAttribute('data-status', 'completed');
                    dayElement.textContent = '✓';
                } else if (dayData.today) {
                    // Día actual
                    dayElement.setAttribute('data-status', 'active');
                    dayElement.textContent = ''; 
                } else {
                    // Día pendiente o no cumplido
                    dayElement.setAttribute('data-status', 'pending');
                    dayElement.textContent = ''; 
                }
            });
        } else {
            // Si el historial semanal no está disponible, marcamos el día actual como 'active'
            const today = new Date().getDay(); // 0 (Sun) - 6 (Sat)
            // Ajustamos el índice (0=Lun, 6=Dom)
            const todayIndex = (today === 0) ? 6 : today - 1; 
            const todayElement = document.querySelector(`.streak-calendar .day-status[data-day-index="${todayIndex}"]`);
            if (todayElement) {
                todayElement.setAttribute('data-status', 'active');
                todayElement.textContent = '';
            }
        }
        
        console.log(" Rachas cargadas correctamente:", data);
        
    })
    .catch(err => {
        console.error(" Error al cargar rachas:", err);
        // Fallback para mostrar 0 días si hay error
        totalStreakDisplay.textContent = "0";
        document.getElementById("contador-racha-metas").textContent = "0";
        document.getElementById("contador-racha-limites").textContent = "0";
        mainIcon.src = "apagada.PNG";
        mainIcon.parentElement.classList.add('off');
        
        // Marcar día actual como activo aunque haya error
        const today = new Date().getDay();
        const todayIndex = (today === 0) ? 6 : today - 1;
        const todayElement = document.querySelector(`.streak-calendar .day-status[data-day-index="${todayIndex}"]`);
        if (todayElement) {
            todayElement.setAttribute('data-status', 'active');
        }
    });
}


// Verificar estado Focus Mode
async function verificarFocusMode() {
  try {
    const response = await fetch('http://localhost:5000/api/focus/status', {
      credentials: 'include'
    });
    const data = await response.json();
    
    const widget = document.getElementById('focus-status-widget');
    
    if (data.success && data.active) {
      widget.style.display = 'block';
      document.getElementById('focus-categories-count').textContent = data.categorias_bloqueadas.length;
      
      const mins = data.tiempo_restante_minutos || 0;
      document.getElementById('focus-time-remaining').textContent = 
        `${Math.floor(mins)}:${String(Math.floor((mins % 1) * 60)).padStart(2, '0')}`;
    } else {
      widget.style.display = 'none';
    }
  } catch (error) {
    console.error('[POPUP] Error verificando Focus:', error);
  }
}

// Llamar en DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // ... código existente ...
  verificarFocusMode();
  setInterval(verificarFocusMode, 5000); // Actualizar cada 5 seg
});