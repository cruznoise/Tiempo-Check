 const urlParams = new URLSearchParams(window.location.search);
    const domain = urlParams.get('domain');
    const category = urlParams.get('category');
    const strictMode = urlParams.get('strict') === 'true';

    console.log('[BLOCKED] Página cargada:', { domain, category, strictMode });

    document.getElementById('domain-name').textContent = domain || 'Sitio desconocido';
    document.getElementById('category-badge').textContent = category || 'Sin categoría';

    if (strictMode) {
      document.getElementById('strict-mode-warning').style.display = 'block';
      document.getElementById('btn-skip').disabled = true;
      document.getElementById('btn-skip').style.display = 'none';
    }

    // Actualizar tiempo restante
    async function actualizarTiempo() {
      try {
        const response = await fetch('http://localhost:5000/api/focus/status', {
          credentials: 'include'
        });
        const data = await response.json();

        if (data.success && data.active) {
          const restante = data.tiempo_restante_minutos || 0;
          const mins = Math.floor(restante);
          const secs = Math.floor((restante % 1) * 60);
          document.getElementById('time-remaining').textContent = 
            `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
          document.getElementById('time-remaining').textContent = 'Sesión finalizada';
        }
      } catch (error) {
        console.error('[BLOCKED] Error:', error);
      }
    }

    actualizarTiempo();
    setInterval(actualizarTiempo, 1000);

    // BOTÓN: Ir al Dashboard
    document.getElementById('btn-dashboard').addEventListener('click', function() {
      console.log('[BLOCKED] Click en Dashboard');
      
      // Usar chrome.tabs API
      chrome.tabs.getCurrent(tab => {
        console.log('[BLOCKED] Tab actual:', tab);
        if (tab && tab.id) {
          chrome.tabs.update(tab.id, { 
            url: 'http://localhost:5000/dashboard' 
          });
        } else {
          // Fallback: crear nueva pestaña
          chrome.tabs.create({ 
            url: 'http://localhost:5000/dashboard' 
          });
        }
      });
    });

    // BOTÓN: Omitir esta vez
    document.getElementById('btn-skip').addEventListener('click', async function() {
    if (strictMode) {
        alert('No puedes omitir en modo estricto');
        return;
    }

    if (confirm('⚠️ ¿Seguro? Romperá tu racha.')) {
        try {
        // 1. Registrar en backend
        await fetch('http://localhost:5000/api/focus/skip-block', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ domain: domain, category: category })
        });

        // 2. Notificar background para actualizar reglas
        chrome.runtime.sendMessage({
            type: 'omitir_dominio',
            domain: domain
        }, (response) => {
            if (response && response.success) {
            // 3. Esperar y redirigir
            setTimeout(() => {
                chrome.tabs.getCurrent(tab => {
                if (tab) {
                    chrome.tabs.update(tab.id, { url: `https://${domain}` });
                }
                });
            }, 500);
            }
        });
        
        } catch (error) {
        console.error('[BLOCKED] Error:', error);
        alert('Error de conexión');
        }
    }
    });

    // Cambiar título
    document.title = ` ${domain} - Bloqueado`;
    
    console.log('[BLOCKED] Script inicializado correctamente');